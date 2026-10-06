"""Collecte des donnees SYNOP Meteo-France et stockage en base SQLite.

Pipeline :
1. Telechargement des fichiers mensuels SYNOP (archive publique, Licence Ouverte).
2. Filtrage sur la station cible et extraction des variables utiles.
3. Insertion des observations brutes (pas 3h) dans la table ``observations``.
4. Agregation quotidienne dans la table ``daily`` (cible ``is_rainy`` comprise).

Usage :
    python -m src.data_collection --start 2015 --end 2024
"""
from __future__ import annotations

import argparse
import gzip
import io
from datetime import date

import pandas as pd
import requests

import config
from src import database

# Prise en charge des CA d'entreprise (proxy TLS) via le magasin systeme Windows.
try:
    import truststore

    truststore.inject_into_ssl()
except Exception:  # pragma: no cover - environnement sans truststore
    pass

# Variables SYNOP utiles (noms de colonnes dans le CSV source).
NUMERIC_COLS = ["t", "td", "u", "pmer", "ff", "dd", "rr1", "rr3", "rr24"]


def download_month(year: int, month: int, station_id: str) -> pd.DataFrame:
    """Telecharge un mois SYNOP et renvoie les lignes de la station cible."""
    url = config.SYNOP_ARCHIVE_URL.format(year=year, month=month)
    resp = requests.get(
        url,
        timeout=config.REQUEST_TIMEOUT,
        headers={"User-Agent": config.USER_AGENT},
    )
    resp.raise_for_status()
    raw = gzip.decompress(resp.content)
    df = pd.read_csv(
        io.BytesIO(raw),
        sep=";",
        dtype=str,
        na_values=["mq"],
    )
    df = df[df["numer_sta"] == station_id].copy()
    return df


def _parse_observations(df: pd.DataFrame, station_id: str) -> list[tuple]:
    """Convertit les colonnes SYNOP en tuples SQLite avec des opérations pandas."""
    parsed = pd.DataFrame(index=df.index)
    parsed["obs_time"] = pd.to_datetime(
        df["date"], format="%Y%m%d%H%M%S", errors="coerce"
    ).dt.strftime("%Y-%m-%dT%H:%M:%S")
    numeric = df.reindex(columns=NUMERIC_COLS).apply(pd.to_numeric, errors="coerce")
    numeric["rr_best"] = numeric["rr3"].fillna(numeric["rr1"]).clip(lower=0)
    parsed = pd.concat([parsed, numeric[["t", "td", "u", "pmer", "ff", "dd", "rr24", "rr_best"]]], axis=1)
    parsed = parsed[parsed["obs_time"].notna()].astype(object)
    parsed = parsed.where(pd.notna(parsed), None)
    parsed.insert(0, "station_id", station_id)
    return list(parsed.itertuples(index=False, name=None))


def collect(
    start: int, end: int, station_id: str | None = None, refresh: bool = False
) -> int:
    """Collecte uniquement les mois absents, sauf demande explicite de rafraichissement."""
    station_id = station_id or config.STATION_ID
    database.init_db()
    conn = database.get_connection()
    total = 0
    today = date.today()
    try:
        for year in range(start, end + 1):
            for month in range(1, 13):
                if (year, month) > (today.year, today.month):
                    continue
                if not refresh and database.observation_month_count(
                    conn, station_id, year, month
                ):
                    print(f"  {year}-{month:02d} : deja present, telechargement ignore")
                    continue
                try:
                    df = download_month(year, month, station_id)
                except requests.HTTPError as exc:
                    print(f"  [skip] {year}-{month:02d} ({exc})")
                    continue
                rows = _parse_observations(df, station_id)
                if rows:
                    database.upsert_observations(conn, rows)
                    total += len(rows)
                print(f"  {year}-{month:02d} : {len(rows)} observations")
        print(f"Total observations en base : {database.count_rows(conn, 'observations')}")
    finally:
        conn.close()
    return total


def build_daily(station_id: str | None = None) -> int:
    """Agrege les observations en table ``daily`` (cumuls et cible)."""
    station_id = station_id or config.STATION_ID
    database.init_db()
    conn = database.get_connection()
    try:
        obs = pd.read_sql_query(
            "SELECT * FROM observations WHERE station_id = ?",
            conn,
            params=(station_id,),
        )
        if obs.empty:
            print("Aucune observation : lancez d'abord la collecte.")
            return 0

        obs["obs_time"] = pd.to_datetime(obs["obs_time"])
        obs["obs_date"] = obs["obs_time"].dt.date.astype(str)
        obs["rr_best"] = obs["rr_best"].clip(lower=0)
        # Temperatures SYNOP en Kelvin -> Celsius.
        for col in ["t", "td"]:
            obs[col] = obs[col] - 273.15

        grp = obs.groupby("obs_date")
        daily = pd.DataFrame({
            "precip_mm": grp["rr_best"].sum(min_count=1),
            "n_observations": grp.size(),
            "n_precip_reports": grp["rr_best"].count(),
            "t_mean": grp["t"].mean(),
            "t_min": grp["t"].min(),
            "t_max": grp["t"].max(),
            "u_mean": grp["u"].mean(),
            "pmer_mean": grp["pmer"].mean(),
            "ff_mean": grp["ff"].mean(),
        }).reset_index()

        daily["is_rainy"] = (
            (daily["precip_mm"] > config.RAIN_THRESHOLD_MM)
            .where(
                daily["precip_mm"].notna()
                & (daily["n_precip_reports"] >= config.EXPECTED_PRECIP_REPORTS_PER_DAY)
            )
        )
        daily.insert(0, "station_id", station_id)

        rows = [
            (
                r.station_id, r.obs_date,
                _none(r.precip_mm), _none(r.t_mean), _none(r.t_min), _none(r.t_max),
                _none(r.u_mean), _none(r.pmer_mean), _none(r.ff_mean),
                _none_int(r.is_rainy), int(r.n_observations), int(r.n_precip_reports),
            )
            for r in daily.itertuples(index=False)
        ]
        n = database.replace_daily(conn, rows)
        rainy = int(daily["is_rainy"].sum())
        labeled_days = int(daily["is_rainy"].notna().sum())
        rate = rainy / labeled_days if labeled_days else 0.0
        print(f"Jours agreges : {n} | jours pluvieux : {rainy} ({rate:.1%} des jours etiquetes)")
        return n
    finally:
        conn.close()


def _none(value):
    """Convertit un NaN pandas en None pour l'insertion SQLite."""
    return None if pd.isna(value) else float(value)


def _none_int(value):
    return None if pd.isna(value) else int(value)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collecte SYNOP Meteo-France -> SQLite")
    parser.add_argument("--start", type=int, default=config.YEAR_START)
    parser.add_argument("--end", type=int, default=config.YEAR_END)
    parser.add_argument("--station", type=str, default=config.STATION_ID)
    parser.add_argument("--skip-download", action="store_true",
                        help="Recalcule uniquement les agregats quotidiens.")
    parser.add_argument("--refresh", action="store_true",
                        help="Retelecharge aussi les mois deja presents en base.")
    args = parser.parse_args()

    if not args.skip_download:
        collect(args.start, args.end, args.station, refresh=args.refresh)
    build_daily(args.station)


if __name__ == "__main__":
    main()
