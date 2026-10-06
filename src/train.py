"""Entrainement et selection du modele de risque de pluie.

Demarche :
1. Chargement des agregats quotidiens depuis SQLite.
2. Split **temporel** (train : annees anterieures ; test : 2 dernieres annees)
   pour evaluer la capacite de generalisation dans le temps.
3. Comparaison de deux modeles (regression logistique, gradient boosting) par
   validation croisee temporelle sur le ROC-AUC.
4. Calibration des probabilites, evaluation finale sur le test, serialisation
   de l'artefact et des metriques.

Usage :
    python -m src.train
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from codecarbon import EmissionsTracker
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import config
from src import database, evaluate
from src.features import (
    FEATURE_COLUMNS,
    build_feature_frame,
    feature_medians,
    feature_row_mask,
)

TEST_YEARS = 2  # nombre d'annees reservees au test (fin de periode)


def load_daily() -> pd.DataFrame:
    conn = database.get_connection()
    try:
        df = pd.read_sql_query(
            "SELECT * FROM daily WHERE station_id = ? ORDER BY obs_date",
            conn,
            params=(config.STATION_ID,),
        )
    finally:
        conn.close()
    if df.empty:
        raise RuntimeError("Table 'daily' vide : lancez d'abord la collecte.")
    return df


def temporal_split(daily: pd.DataFrame):
    """Separe train / test sur la base de l'annee (derniers ``TEST_YEARS`` ans)."""
    years = pd.to_datetime(daily["obs_date"]).dt.year
    cutoff = years.max() - TEST_YEARS + 1
    train = daily[years < cutoff].reset_index(drop=True)
    test = daily[years >= cutoff].reset_index(drop=True)
    return train, test, int(cutoff)


def candidate_models() -> dict[str, Pipeline]:
    return {
        "logreg": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(
                class_weight="balanced",
                max_iter=1000,
                random_state=config.RANDOM_STATE,
            )),
        ]),
        "hist_gb": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("clf", HistGradientBoostingClassifier(
                max_depth=3,
                learning_rate=0.05,
                max_iter=300,
                l2_regularization=1.0,
                random_state=config.RANDOM_STATE,
            )),
        ]),
    }


def _train() -> dict:
    daily = load_daily()
    train_df, test_df, cutoff = temporal_split(daily)
    X_train, y_train = build_feature_frame(train_df)
    X_test, y_test = build_feature_frame(test_df)
    print(f"Train : {len(X_train)} lignes utilisables (< {cutoff}) | "
          f"Test : {len(X_test)} lignes utilisables (>= {cutoff})")

    sorted_train = train_df.sort_values("obs_date").reset_index(drop=True)
    feature_dates = pd.to_datetime(
        sorted_train.loc[feature_row_mask(sorted_train), "obs_date"]
    ).reset_index(drop=True)
    validation_year = int(feature_dates.max().year)
    fit_mask = feature_dates.dt.year < validation_year
    validation_mask = feature_dates.dt.year == validation_year
    X_fit, y_fit = X_train[fit_mask], y_train[fit_mask]
    X_validation, y_validation = X_train[validation_mask], y_train[validation_mask]
    if X_fit.empty or X_validation.empty:
        raise RuntimeError("Impossible de constituer une validation temporelle avant le test.")

    # Selection par validation croisee temporelle (ROC-AUC).
    tscv = TimeSeriesSplit(n_splits=5)
    scores = {}
    for name, pipe in candidate_models().items():
        cv = cross_val_score(pipe, X_fit, y_fit, cv=tscv, scoring="roc_auc")
        scores[name] = float(cv.mean())
        print(f"  CV ROC-AUC {name:8} : {cv.mean():.4f} (+/- {cv.std():.4f})")
    best_name = max(scores, key=scores.get)
    print(f"Modele retenu : {best_name}")

    # Le seuil est fixe sur la derniere annee pre-test, jamais sur le jeu de test.
    threshold_model = CalibratedClassifierCV(
        candidate_models()[best_name], method="sigmoid", cv=tscv
    )
    threshold_model.fit(X_fit, y_fit)
    validation_prob = threshold_model.predict_proba(X_validation)[:, 1]
    selected_threshold = evaluate.optimal_threshold(y_validation, validation_prob)

    # Le modele final est calibre sur toutes les donnees pre-test.
    base = candidate_models()[best_name]
    model = CalibratedClassifierCV(base, method="sigmoid", cv=tscv)
    model.fit(X_train, y_train)

    # Evaluation finale sur le jeu de test.
    y_prob = model.predict_proba(X_test)[:, 1]
    results = evaluate.evaluate_probabilities(y_test, y_prob, selected_threshold)
    baseline_brier = {
        "training_base_rate": round(
            float(brier_score_loss(y_test, np.full(len(y_test), y_train.mean()))), 4
        ),
        "rain_previous_day": round(
            float(brier_score_loss(y_test, X_test["rained_lag1"])), 4
        ),
    }

    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": model,
            "features": FEATURE_COLUMNS,
            "station": config.STATION_NAME,
            "fallback_medians": feature_medians(train_df),
        },
        config.MODEL_PATH,
    )

    metrics = {
        "station_id": config.STATION_ID,
        "station_name": config.STATION_NAME,
        "region": config.REGION,
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rain_threshold_mm": config.RAIN_THRESHOLD_MM,
        "n_train": len(X_train),
        "n_test": len(X_test),
        "test_from_year": cutoff,
        "validation_year": validation_year,
        "selected_model": best_name,
        "cv_roc_auc": {k: round(v, 4) for k, v in scores.items()},
        "baseline_brier": baseline_brier,
        "test_metrics": results,
    }
    return metrics


def main() -> None:
    tracker = EmissionsTracker(
        project_name="goutte-deau-training",
        output_dir=str(config.MODELS_DIR),
        save_to_file=False,
        save_to_api=False,
        save_to_logger=False,
        measure_power_secs=1,
        log_level="ERROR",
    )
    tracker.start()
    try:
        metrics = _train()
    finally:
        emissions_kg = tracker.stop()

    if emissions_kg is None:
        raise RuntimeError("CodeCarbon n'a pas pu estimer les émissions de l'entraînement.")
    metrics["emissions"] = {
        "tool": "CodeCarbon",
        "version": "3.3.1",
        "scope": "processus d'entraînement local",
        "estimated_g_co2e": round(emissions_kg * 1000, 4),
        "method": "estimation logicielle énergie CPU/RAM et intensité électrique détectée",
    }
    config.METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    m = metrics["test_metrics"]["at_0.5"]
    print(f"\nTest  ROC-AUC : {m['roc_auc']} | PR-AUC : {m['pr_auc']} | "
          f"Brier : {m['brier']} | F1@0.5 : {m['f1']}")
    print(f"Seuil de validation {metrics['validation_year']} : "
          f"{metrics['test_metrics']['selected_threshold']:.4f}")
    print(f"Emissions estimees : {metrics['emissions']['estimated_g_co2e']} gCO2e "
          "(CodeCarbon, estimation logicielle)")
    print(f"Artefact : {config.MODEL_PATH}")
    print(f"Metriques : {config.METRICS_PATH}")


if __name__ == "__main__":
    main()
