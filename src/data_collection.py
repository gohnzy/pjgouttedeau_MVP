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


def _to_float(value) -> float | None:
    """Convertit une valeur SYNOP ('mq'/NaN = manquant) en float ou None."""
    if value is None:
        return None
    if isinstance(value, float):
        import math
        return None if math.isnan(value) else value
    value = str(value).strip()
    if value in ("", "mq"):
        return None
    try:
        return float(value)
    except ValueError:
        return None


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
    """Transforme un DataFrame SYNOP en tuples pour la table observations."""
    rows: list[tuple] = []
    for _, r in df.iterrows():
        obs_time = pd.to_datetime(r["date"], format="%Y%m%d%H%M%S", errors="coerce")
        if pd.isna(obs_time):
            continue
        vals = {c: _to_float(r.get(c)) for c in NUMERIC_COLS}
        # Meilleur cumul court disponible (rr3 prioritaire, sinon rr1) ; trace (-0.1) -> 0.
        rr_best = vals["rr3"] if vals["rr3"] is not None else vals["rr1"]
        if rr_best is not None and rr_best < 0:
            rr_best = 0.0
        rows.append(
            (
                station_id,
                obs_time.strftime("%Y-%m-%dT%H:%M:%S"),
                vals["t"], vals["td"], vals["u"], vals["pmer"],
                vals["ff"], vals["dd"], vals["rr24"], rr_best,
            )
        )
    return rows


def collect(start: int, end: int, station_id: str | None = None) -> int:
    """Telecharge et stocke les observations de ``start`` a ``end`` (inclus)."""
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
            "t_mean": grp["t"].mean(),
            "t_min": grp["t"].min(),
            "t_max": grp["t"].max(),
            "u_mean": grp["u"].mean(),
            "pmer_mean": grp["pmer"].mean(),
            "ff_mean": grp["ff"].mean(),
        }).reset_index()

        daily["precip_mm"] = daily["precip_mm"].fillna(0.0)
        daily["is_rainy"] = (daily["precip_mm"] > config.RAIN_THRESHOLD_MM).astype(int)
        daily.insert(0, "station_id", station_id)

        rows = [
            (
                r.station_id, r.obs_date,
                _none(r.precip_mm), _none(r.t_mean), _none(r.t_min), _none(r.t_max),
                _none(r.u_mean), _none(r.pmer_mean), _none(r.ff_mean), int(r.is_rainy),
            )
            for r in daily.itertuples(index=False)
        ]
        n = database.replace_daily(conn, rows)
        rainy = int(daily["is_rainy"].sum())
        print(f"Jours agreges : {n} | jours pluvieux : {rainy} ({rainy / n:.1%})")
        return n
    finally:
        conn.close()


def _none(value):
    """Convertit un NaN pandas en None pour l'insertion SQLite."""
    return None if pd.isna(value) else float(value)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collecte SYNOP Meteo-France -> SQLite")
    parser.add_argument("--start", type=int, default=config.YEAR_START)
    parser.add_argument("--end", type=int, default=config.YEAR_END)
    parser.add_argument("--station", type=str, default=config.STATION_ID)
    parser.add_argument("--skip-download", action="store_true",
                        help="Recalcule uniquement les agregats quotidiens.")
    args = parser.parse_args()

    if not args.skip_download:
        collect(args.start, args.end, args.station)
    build_daily(args.station)


if __name__ == "__main__":
    main()
