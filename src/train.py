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
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import config
from src import database, evaluate
from src.features import FEATURE_COLUMNS, build_feature_frame, feature_medians

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


def main() -> None:
    daily = load_daily()
    train_df, test_df, cutoff = temporal_split(daily)
    X_train, y_train = build_feature_frame(train_df)
    X_test, y_test = build_feature_frame(test_df)
    print(f"Train : {len(train_df)} jours (< {cutoff}) | "
          f"Test : {len(test_df)} jours (>= {cutoff})")

    # Selection par validation croisee temporelle (ROC-AUC).
    tscv = TimeSeriesSplit(n_splits=5)
    scores = {}
    for name, pipe in candidate_models().items():
        cv = cross_val_score(pipe, X_train, y_train, cv=tscv, scoring="roc_auc")
        scores[name] = float(cv.mean())
        print(f"  CV ROC-AUC {name:8} : {cv.mean():.4f} (+/- {cv.std():.4f})")
    best_name = max(scores, key=scores.get)
    print(f"Modele retenu : {best_name}")

    # Calibration des probabilites (sigmoid) sur le meilleur modele.
    base = candidate_models()[best_name]
    model = CalibratedClassifierCV(base, method="sigmoid", cv=tscv)
    model.fit(X_train, y_train)

    # Evaluation finale sur le jeu de test.
    y_prob = model.predict_proba(X_test)[:, 1]
    results = evaluate.evaluate_probabilities(y_test, y_prob)

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
        "n_train": len(train_df),
        "n_test": len(test_df),
        "test_from_year": cutoff,
        "selected_model": best_name,
        "cv_roc_auc": {k: round(v, 4) for k, v in scores.items()},
        "test_metrics": results,
    }
    config.METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    m = results["at_0.5"]
    print(f"\nTest  ROC-AUC : {m['roc_auc']} | PR-AUC : {m['pr_auc']} | "
          f"Brier : {m['brier']} | F1@0.5 : {m['f1']}")
    print(f"Artefact : {config.MODEL_PATH}")
    print(f"Metriques : {config.METRICS_PATH}")


if __name__ == "__main__":
    main()
