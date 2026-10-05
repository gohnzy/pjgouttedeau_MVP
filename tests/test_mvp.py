"""Tests unitaires et d'integration du MVP Projet Goutte d'eau."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src import evaluate
from src.features import (
    FEATURE_COLUMNS,
    build_feature_frame,
    features_for_date,
    seasonal_features,
)


def _fake_daily(n: int = 40) -> pd.DataFrame:
    dates = pd.date_range("2020-01-01", periods=n, freq="D")
    rng = np.random.default_rng(0)
    return pd.DataFrame({
        "station_id": "07630",
        "obs_date": dates.astype(str),
        "precip_mm": rng.gamma(1.0, 2.0, n).round(1),
        "t_mean": rng.normal(10, 5, n),
        "t_min": rng.normal(5, 4, n),
        "t_max": rng.normal(15, 5, n),
        "u_mean": rng.uniform(60, 95, n),
        "pmer_mean": rng.normal(101500, 500, n),
        "ff_mean": rng.uniform(1, 6, n),
        "is_rainy": rng.integers(0, 2, n),
    })


# --- features -------------------------------------------------------------

def test_seasonal_features_bounds_and_seasonality():
    jan = seasonal_features("2024-01-01")
    jul = seasonal_features("2024-07-01")
    assert set(jan) == {"doy_sin", "doy_cos", "doy_sin2", "doy_cos2"}
    for v in jan.values():
        assert -1.0 <= v <= 1.0
    assert jan != jul  # la saison influe sur les variables


def test_build_feature_frame_shape_and_columns():
    daily = _fake_daily(40)
    X, y = build_feature_frame(daily)
    assert list(X.columns) == FEATURE_COLUMNS
    assert len(X) == len(y)
    # Les 3 premiers jours (sans historique) sont ecartes.
    assert len(X) == len(daily) - 3


def test_features_for_date_uses_recent_history():
    daily = _fake_daily(40)
    target = "2020-02-11"  # lendemain du dernier jour (2020-02-09 -> n=40)
    frame = features_for_date(target, daily, fallback={})
    assert list(frame.columns) == FEATURE_COLUMNS
    assert frame.shape[0] == 1


def test_features_for_date_future_falls_back_to_climatology():
    daily = _fake_daily(40)
    fallback = {c: 0.0 for c in FEATURE_COLUMNS}
    frame = features_for_date("2030-05-01", daily, fallback=fallback)
    assert frame.attrs["used_history"] is False


# --- evaluation -----------------------------------------------------------

def test_compute_metrics_perfect_separation():
    y_true = [0, 0, 1, 1]
    y_prob = [0.1, 0.2, 0.8, 0.9]
    m = evaluate.compute_metrics(y_true, y_prob, threshold=0.5)
    assert m["roc_auc"] == 1.0
    assert m["accuracy"] == 1.0
    assert m["confusion_matrix"]["tp"] == 2


def test_optimal_threshold_in_range():
    y_true = [0, 0, 1, 1]
    y_prob = [0.2, 0.4, 0.6, 0.8]
    thr = evaluate.optimal_threshold(y_true, y_prob)
    assert 0.0 <= thr <= 1.0


# --- API (integration, requiert modele + base) ----------------------------

@pytest.mark.skipif(
    not __import__("config").MODEL_PATH.exists(),
    reason="Modele non entraine : lancez src.train.",
)
def test_api_health_and_predict():
    from fastapi.testclient import TestClient

    from src.api import app

    with TestClient(app) as client:
        h = client.get("/health")
        assert h.status_code == 200
        assert h.json()["model_loaded"] is True

        r = client.get("/predict", params={"date": "2024-07-14"})
        assert r.status_code == 200
        body = r.json()
        assert 0.0 <= body["rain_probability"] <= 1.0
        assert body["risk_level"] in {"faible", "modere", "eleve", "tres eleve"}

        bad = client.get("/predict", params={"date": "not-a-date"})
        assert bad.status_code == 422
