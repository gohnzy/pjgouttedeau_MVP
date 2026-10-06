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
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

import config
from src import database
from src.features import features_for_date

# Etat applicatif partage (charge au demarrage).
STATE: dict = {}


class PredictionResponse(BaseModel):
    date: date
    station: str
    region: str
    rain_probability: float = Field(ge=0, le=1)
    risk_level: Literal["faible", "modéré", "élevé", "très élevé"]
    threshold_mm: float
    alert_probability_threshold: float = Field(ge=0, le=1)
    based_on_history: bool
    note: str


class BatchPredictionRequest(BaseModel):
    dates: list[date] = Field(min_length=1, max_length=31)


def _risk_level(probability: float, threshold: float) -> str:
    if probability < threshold:
        return "faible"
    if probability < 0.50:
        return "modéré"
    if probability < 0.75:
        return "élevé"
    return "très élevé"


def _predict_for_date(target: date) -> dict:
    model = STATE.get("model")
    if model is None:
        raise HTTPException(status_code=503, detail="Modèle non entraîné. Lancez src.train.")

    X = features_for_date(target, STATE["daily"], STATE.get("fallback"))
    probability = float(model.predict_proba(X)[:, 1][0])
    alert_threshold = float(
        STATE.get("metrics", {})
        .get("test_metrics", {})
        .get("selected_threshold", 0.22)
    )
    used_history = bool(X.attrs.get("used_history", False))
    return {
        "date": target,
        "station": config.STATION_NAME,
        "region": config.REGION,
        "rain_probability": round(probability, 4),
        "risk_level": _risk_level(probability, alert_threshold),
        "threshold_mm": config.RAIN_THRESHOLD_MM,
        "alert_probability_threshold": alert_threshold,
        "based_on_history": used_history,
        "note": (
            "Prévision fondée sur les antécédents météorologiques observés."
            if used_history
            else "Historique antérieur indisponible : estimation climatologique (saisonnière)."
        ),
    }


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
        raise HTTPException(status_code=503, detail="Métriques indisponibles.")
    return STATE["metrics"]


@app.get("/predict", response_model=PredictionResponse)
def predict(
    target: date = Query(
        ...,
        alias="date",
        description="Date au format YYYY-MM-DD",
        examples=["2024-07-14"],
    )
):
    return _predict_for_date(target)


@app.post("/predict/batch", response_model=list[PredictionResponse])
def predict_batch(request: BatchPredictionRequest):
    return [_predict_for_date(target) for target in request.dates]
