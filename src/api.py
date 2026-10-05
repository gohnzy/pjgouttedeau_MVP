"""API REST du MVP Projet Goutte d'eau.

Expose une estimation du risque de pluie *en fonction d'une date* pour la
station de reference. Le modele entraine est charge au demarrage ; les
antecedents meteorologiques necessaires a la prevision sont lus dans la base.

Lancement :
    uvicorn src.api:app --reload
Documentation interactive : http://127.0.0.1:8000/docs
"""
from __future__ import annotations

import json
from contextlib import asynccontextmanager
from datetime import date

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Query

import config
from src import database
from src.features import features_for_date

# Etat applicatif partage (charge au demarrage).
STATE: dict = {}


def _risk_level(p: float) -> str:
    if p < 0.25:
        return "faible"
    if p < 0.50:
        return "modere"
    if p < 0.75:
        return "eleve"
    return "tres eleve"


def _load_assets() -> None:
    """Charge le modele, les metriques et l'historique en memoire."""
    if not config.MODEL_PATH.exists():
        STATE["model"] = None
        return
    bundle = joblib.load(config.MODEL_PATH)
    STATE["model"] = bundle["model"]
    STATE["fallback"] = bundle.get("fallback_medians", {})

    conn = database.get_connection()
    try:
        daily = pd.read_sql_query(
            "SELECT * FROM daily WHERE station_id = ? ORDER BY obs_date",
            conn, params=(config.STATION_ID,),
        )
    finally:
        conn.close()
    STATE["daily"] = daily
    STATE["date_min"] = daily["obs_date"].min() if not daily.empty else None
    STATE["date_max"] = daily["obs_date"].max() if not daily.empty else None

    if config.METRICS_PATH.exists():
        STATE["metrics"] = json.loads(config.METRICS_PATH.read_text(encoding="utf-8"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    _load_assets()
    yield
    STATE.clear()


app = FastAPI(
    title="Projet Goutte d'eau - API de risque de pluie",
    description="Estimation du risque de pluie par date pour une station SYNOP.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": STATE.get("model") is not None,
        "data_range": {"from": STATE.get("date_min"), "to": STATE.get("date_max")},
    }


@app.get("/model-info")
def model_info():
    if "metrics" not in STATE:
        raise HTTPException(status_code=503, detail="Metriques indisponibles.")
    return STATE["metrics"]


@app.get("/predict")
def predict(
    date_str: str = Query(
        ...,
        alias="date",
        description="Date au format YYYY-MM-DD",
        examples=["2024-07-14"],
    )
):
    model = STATE.get("model")
    if model is None:
        raise HTTPException(status_code=503, detail="Modele non entraine. Lancez src.train.")
    try:
        target = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=422, detail="Format de date invalide (attendu YYYY-MM-DD).")

    X = features_for_date(target, STATE["daily"], STATE.get("fallback"))
    proba = float(model.predict_proba(X)[:, 1][0])

    return {
        "date": target.isoformat(),
        "station": config.STATION_NAME,
        "region": config.REGION,
        "rain_probability": round(proba, 4),
        "risk_level": _risk_level(proba),
        "threshold_mm": config.RAIN_THRESHOLD_MM,
        "based_on_history": bool(X.attrs.get("used_history", False)),
        "note": (
            "Prevision fondee sur les antecedents meteorologiques observes."
            if X.attrs.get("used_history")
            else "Historique anterieur indisponible : estimation climatologique (saisonniere)."
        ),
    }
