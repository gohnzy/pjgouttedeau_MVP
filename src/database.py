"""Acces a la base de donnees SQLite du MVP.

Deux tables :
- ``observations`` : mesures SYNOP brutes (pas de temps 3h) de la station.
- ``daily`` : agregats quotidiens derives, prets pour la modelisation.
"""
from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path
from typing import Iterable

import config


SCHEMA = """
CREATE TABLE IF NOT EXISTS observations (
    station_id TEXT    NOT NULL,
    obs_time   TEXT    NOT NULL,           -- ISO 8601 (UTC)
    t          REAL,                       -- temperature (K)
    td         REAL,                       -- point de rosee (K)
    u          REAL,                       -- humidite relative (%)
    pmer       REAL,                       -- pression mer (Pa)
    ff         REAL,                       -- vent moyen (m/s)
    dd         REAL,                       -- direction vent (deg)
    rr24       REAL,                       -- precipitations 24h (mm)
    rr_best    REAL,                       -- meilleur cumul precipitations dispo (mm)
    PRIMARY KEY (station_id, obs_time)
);

CREATE TABLE IF NOT EXISTS daily (
    station_id   TEXT NOT NULL,
    obs_date     TEXT NOT NULL,            -- YYYY-MM-DD
    precip_mm    REAL,                     -- cumul quotidien estime (mm)
    t_mean       REAL,
    t_min        REAL,
    t_max        REAL,
    u_mean       REAL,                     -- humidite relative moyenne (%)
    pmer_mean    REAL,                     -- pression moyenne (Pa)
    ff_mean      REAL,                     -- vent moyen (m/s)
    is_rainy     INTEGER,                  -- cible : 1 si precip_mm > seuil
    n_observations INTEGER NOT NULL DEFAULT 0,
    n_precip_reports INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (station_id, obs_date)
);

CREATE INDEX IF NOT EXISTS idx_daily_date ON daily (obs_date);
"""


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Ouvre une connexion SQLite (cree le dossier parent si besoin)."""
    path = Path(db_path or config.DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | None = None) -> None:
    """Cree les tables si elles n'existent pas."""
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA)
        columns = {
            row[1] for row in conn.execute("PRAGMA table_info(daily)").fetchall()
        }
        if "n_observations" not in columns:
            conn.execute(
                "ALTER TABLE daily ADD COLUMN n_observations INTEGER NOT NULL DEFAULT 0"
            )
        if "n_precip_reports" not in columns:
            conn.execute(
                "ALTER TABLE daily ADD COLUMN n_precip_reports INTEGER NOT NULL DEFAULT 0"
            )
        conn.commit()
    finally:
        conn.close()


def upsert_observations(conn: sqlite3.Connection, rows: Iterable[tuple]) -> int:
    """Insere/maj des observations brutes. ``rows`` : tuples alignes sur le schema."""
    cur = conn.executemany(
        """
        INSERT INTO observations
            (station_id, obs_time, t, td, u, pmer, ff, dd, rr24, rr_best)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(station_id, obs_time) DO UPDATE SET
            t=excluded.t, td=excluded.td, u=excluded.u, pmer=excluded.pmer,
            ff=excluded.ff, dd=excluded.dd, rr24=excluded.rr24,
            rr_best=excluded.rr_best
        """,
        rows,
    )
    conn.commit()
    return cur.rowcount


def replace_daily(conn: sqlite3.Connection, rows: Iterable[tuple]) -> int:
    """Remplace integralement la table ``daily`` (recalcul idempotent)."""
    conn.execute("DELETE FROM daily")
    cur = conn.executemany(
        """
        INSERT INTO daily
              (station_id, obs_date, precip_mm, t_mean, t_min, t_max,
               u_mean, pmer_mean, ff_mean, is_rainy, n_observations, n_precip_reports)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    return cur.rowcount


def count_rows(conn: sqlite3.Connection, table: str) -> int:
    if table not in {"observations", "daily"}:
        raise ValueError(f"Table non autorisee: {table}")
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def observation_month_count(
    conn: sqlite3.Connection, station_id: str, year: int, month: int
) -> int:
    """Compte les observations déjà stockées pour un mois de station."""
    start = date(year, month, 1).isoformat() + "T00:00:00"
    if month == 12:
        end = date(year + 1, 1, 1).isoformat() + "T00:00:00"
    else:
        end = date(year, month + 1, 1).isoformat() + "T00:00:00"
    return conn.execute(
        """SELECT COUNT(*) FROM observations
           WHERE station_id = ? AND obs_time >= ? AND obs_time < ?""",
        (station_id, start, end),
    ).fetchone()[0]
