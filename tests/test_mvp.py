"""Tests unitaires et d'integration du MVP Projet Goutte d'eau."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src import evaluate
from src import database
from src.data_collection import _parse_observations
from src.train import temporal_split
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


def test_build_feature_frame_excludes_unknown_rain_target():
    daily = _fake_daily(40)
    daily.loc[5, ["precip_mm", "is_rainy"]] = np.nan
    X, y = build_feature_frame(daily)
    assert len(X) == len(y)
    assert len(y) < len(daily) - 3
    assert y.isin([0, 1]).all()


def test_build_feature_frame_excludes_undercovered_rain_day_and_lags():
    daily = _fake_daily(40)
    daily["n_precip_reports"] = 8
    daily.loc[5, "n_precip_reports"] = 7
    daily.loc[5, "is_rainy"] = np.nan
    X, y = build_feature_frame(daily)
    assert len(X) == len(daily) - 7
    assert y.isin([0, 1]).all()


def test_features_for_date_uses_recent_history():
    daily = _fake_daily(40)
    target = "2020-02-10"  # lendemain du dernier jour
    frame = features_for_date(target, daily, fallback={})
    assert list(frame.columns) == FEATURE_COLUMNS
    assert frame.shape[0] == 1
    assert frame.attrs["used_history"] is True


def test_features_for_date_falls_back_after_undercovered_rain_day():
    daily = _fake_daily(40)
    daily["n_precip_reports"] = 8
    daily.loc[39, "n_precip_reports"] = 7
    daily.loc[39, "is_rainy"] = np.nan
    frame = features_for_date("2020-02-10", daily, fallback={})
    assert frame.attrs["used_history"] is False


def test_features_for_date_rejects_stale_history():
    daily = _fake_daily(40)
    frame = features_for_date("2020-02-16", daily, fallback={})
    assert frame.attrs["used_history"] is False


def test_parse_observations_and_month_count(tmp_path):
    source = pd.DataFrame([{
        "date": "20240101000000", "t": "280", "td": "mq", "u": "80",
        "pmer": "101000", "ff": "3", "dd": "90", "rr1": "-0.1",
        "rr3": "mq", "rr24": "mq",
    }, {
        "date": "date-invalide", "t": "280",
    }])
    rows = _parse_observations(source, "07630")
    assert rows == [("07630", "2024-01-01T00:00:00", 280.0, None, 80.0,
                     101000.0, 3.0, 90.0, None, 0.0)]

    conn = database.get_connection(tmp_path / "test.db")
    try:
        database.init_db(tmp_path / "test.db")
        database.upsert_observations(conn, rows)
        assert database.observation_month_count(conn, "07630", 2024, 1) == 1
        assert database.observation_month_count(conn, "07630", 2024, 2) == 0
    finally:
        conn.close()


def test_build_daily_keeps_missing_precipitation_unknown(tmp_path, monkeypatch):
    import config

    from src.data_collection import build_daily

    db_path = tmp_path / "weather.db"
    monkeypatch.setattr(config, "DB_PATH", db_path)
    database.init_db()
    conn = database.get_connection()
    try:
        database.upsert_observations(conn, [(
            "07630", "2024-01-01T00:00:00", 280.0, 275.0, 80.0,
            101000.0, 3.0, 90.0, None, None,
        )])
    finally:
        conn.close()

    assert build_daily() == 1
    conn = database.get_connection()
    try:
        row = conn.execute(
            "SELECT precip_mm, is_rainy, n_observations, n_precip_reports FROM daily"
        ).fetchone()
        assert tuple(row) == (None, None, 1, 0)
    finally:
        conn.close()


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


def test_temporal_split_keeps_latest_years_for_test():
    daily = pd.DataFrame({
        "obs_date": pd.date_range("2018-01-01", "2024-12-31", freq="D").astype(str)
    })
    train, test, cutoff = temporal_split(daily)
    assert cutoff == 2023
    assert pd.to_datetime(train["obs_date"]).dt.year.max() < cutoff
    assert pd.to_datetime(test["obs_date"]).dt.year.min() == cutoff


def test_optimal_threshold_in_range():
    y_true = [0, 0, 1, 1]
    y_prob = [0.2, 0.4, 0.6, 0.8]
    thr = evaluate.optimal_threshold(y_true, y_prob)
    assert 0.0 <= thr <= 1.0


def test_evaluate_probabilities_uses_threshold_without_reoptimizing_test():
    y_true = [0, 0, 1, 1]
    y_prob = [0.2, 0.4, 0.6, 0.8]
    result = evaluate.evaluate_probabilities(y_true, y_prob, threshold=0.7)
    assert result["selected_threshold"] == 0.7
    assert result["at_selected"]["confusion_matrix"] == {
        "tn": 2, "fp": 0, "fn": 1, "tp": 1
    }


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
        assert body["risk_level"] in {"faible", "modéré", "élevé", "très élevé"}
        assert body["region"]
        assert body["note"]

        batch = client.post(
            "/predict/batch",
            json={"dates": ["2024-07-14", "2024-07-15"]},
        )
        assert batch.status_code == 200
        assert len(batch.json()) == 2
        assert all(item["region"] == body["region"] for item in batch.json())

        bad = client.get("/predict", params={"date": "not-a-date"})
        assert bad.status_code == 422
