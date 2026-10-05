"""Feature engineering pour le modele de risque de pluie (prevision a J+1).

L'API fournit une estimation du risque de pluie *en fonction d'une date*.
Pour une prevision honnete (sans fuite de donnees), les variables combinent :

- **Saisonnalite** : encodage cyclique du jour de l'annee (climatologie).
- **Antecedents meteorologiques** (jours precedents) : persistance des pluies,
  tendance de pression, humidite et temperature de la veille.

Pour une date donnee, le vecteur de features est reconstruit a partir des
observations *anterieures* stockees en base. Si l'historique est indisponible
(ex. date future eloignee), les antecedents sont remplaces par les medianes
d'entrainement : le modele se comporte alors comme une climatologie.
"""
from __future__ import annotations

from datetime import date, datetime

import numpy as np
import pandas as pd

SEASONAL_COLUMNS = ["doy_sin", "doy_cos", "doy_sin2", "doy_cos2"]
LAG_COLUMNS = [
    "precip_lag1",    # precipitations de la veille (mm)
    "rained_lag1",    # a-t-il plu la veille (0/1)
    "precip_roll3",   # cumul des 3 jours precedents (mm)
    "pmer_lag1",      # pression mer de la veille (Pa)
    "pmer_trend",     # tendance de pression (veille - avant-veille)
    "u_lag1",         # humidite relative de la veille (%)
    "t_mean_lag1",    # temperature moyenne de la veille (C)
]
FEATURE_COLUMNS = SEASONAL_COLUMNS + LAG_COLUMNS
TARGET_COLUMN = "is_rainy"


def _parse_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()


def seasonal_features(value) -> dict:
    """Variables cycliques (saisonnalite) pour une date."""
    d = _parse_date(value)
    doy = d.timetuple().tm_yday
    year_len = 366 if (d.year % 4 == 0 and (d.year % 100 != 0 or d.year % 400 == 0)) else 365
    angle = 2 * np.pi * doy / year_len
    return {
        "doy_sin": np.sin(angle),
        "doy_cos": np.cos(angle),
        "doy_sin2": np.sin(2 * angle),
        "doy_cos2": np.cos(2 * angle),
    }


def build_feature_frame(daily: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Construit X (saisonnalite + antecedents) et y a partir de ``daily``.

    Les lignes sans historique suffisant (premiers jours) sont ecartees.
    """
    df = daily.sort_values("obs_date").reset_index(drop=True).copy()

    seas = df["obs_date"].apply(seasonal_features).apply(pd.Series)

    df["precip_lag1"] = df["precip_mm"].shift(1)
    df["rained_lag1"] = df["is_rainy"].shift(1)
    df["precip_roll3"] = df["precip_mm"].shift(1).rolling(3).sum()
    df["pmer_lag1"] = df["pmer_mean"].shift(1)
    df["pmer_trend"] = df["pmer_mean"].shift(1) - df["pmer_mean"].shift(2)
    df["u_lag1"] = df["u_mean"].shift(1)
    df["t_mean_lag1"] = df["t_mean"].shift(1)

    X = pd.concat([seas, df[LAG_COLUMNS]], axis=1)[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN].astype(int)

    valid = X["precip_roll3"].notna()  # besoin d'au moins 3 jours d'historique
    return X[valid].reset_index(drop=True), y[valid].reset_index(drop=True)


def feature_medians(daily: pd.DataFrame) -> dict:
    """Medianes des variables d'antecedents (valeurs de repli pour l'API)."""
    X, _ = build_feature_frame(daily)
    return {col: float(X[col].median()) for col in LAG_COLUMNS}


def features_for_date(value, daily: pd.DataFrame, fallback: dict | None = None) -> pd.DataFrame:
    """Construit le vecteur de features d'une date a partir des antecedents.

    ``daily`` : historique (table daily). ``fallback`` : medianes d'entrainement
    utilisees si l'historique anterieur est insuffisant.
    """
    target = _parse_date(value)
    row = dict(seasonal_features(target))

    hist = daily[daily["obs_date"] < target.isoformat()].sort_values("obs_date")
    fallback = fallback or {}

    # Antecedents exploitables uniquement si le dernier jour connu est recent
    # (<= 7 jours avant la cible) ; sinon on retombe sur la climatologie.
    recent_enough = False
    if len(hist) >= 3:
        last_date = _parse_date(hist.iloc[-1]["obs_date"])
        recent_enough = (target - last_date).days <= 7

    if recent_enough:
        last3 = hist.tail(3)
        last = hist.iloc[-1]
        prev = hist.iloc[-2]
        row["precip_lag1"] = float(last["precip_mm"])
        row["rained_lag1"] = float(last["is_rainy"])
        row["precip_roll3"] = float(last3["precip_mm"].sum())
        row["pmer_lag1"] = float(last["pmer_mean"]) if pd.notna(last["pmer_mean"]) else fallback.get("pmer_lag1")
        row["pmer_trend"] = (
            float(last["pmer_mean"]) - float(prev["pmer_mean"])
            if pd.notna(last["pmer_mean"]) and pd.notna(prev["pmer_mean"])
            else fallback.get("pmer_trend")
        )
        row["u_lag1"] = float(last["u_mean"]) if pd.notna(last["u_mean"]) else fallback.get("u_lag1")
        row["t_mean_lag1"] = float(last["t_mean"]) if pd.notna(last["t_mean"]) else fallback.get("t_mean_lag1")
        used_history = True
    else:
        for col in LAG_COLUMNS:
            row[col] = fallback.get(col)
        used_history = False

    frame = pd.DataFrame([row], columns=FEATURE_COLUMNS)
    frame.attrs["used_history"] = used_history
    return frame
