"""Evaluation du modele et indicateurs qualite.

Fournit un ensemble de metriques adaptees a un probleme de classification
binaire **desequilibre** (jours pluvieux minoritaires) et a une sortie
probabiliste (risque) :

- ROC-AUC, PR-AUC : pouvoir discriminant.
- Brier score : qualite de la calibration des probabilites.
- Accuracy / precision / rappel / F1 : a un seuil donne.
- Seuil optimal (indice de Youden) et matrice de confusion.
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


def optimal_threshold(y_true, y_prob) -> float:
    """Seuil maximisant l'indice de Youden (TPR - FPR)."""
    fpr, tpr, thr = roc_curve(y_true, y_prob)
    youden = tpr - fpr
    return float(thr[int(np.argmax(youden))])


def compute_metrics(y_true, y_prob, threshold: float = 0.5) -> dict:
    """Calcule l'ensemble des metriques pour un seuil donne."""
    y_true = np.asarray(y_true).astype(int)
    y_prob = np.asarray(y_prob, dtype=float)
    y_pred = (y_prob >= threshold).astype(int)

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "threshold": round(float(threshold), 4),
        "base_rate": round(float(y_true.mean()), 4),
        "roc_auc": round(float(roc_auc_score(y_true, y_prob)), 4),
        "pr_auc": round(float(average_precision_score(y_true, y_prob)), 4),
        "brier": round(float(brier_score_loss(y_true, y_prob)), 4),
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


def evaluate_probabilities(y_true, y_prob) -> dict:
    """Metriques au seuil 0,5 et au seuil optimal (Youden)."""
    thr_opt = optimal_threshold(y_true, y_prob)
    return {
        "at_0.5": compute_metrics(y_true, y_prob, 0.5),
        "at_optimal": compute_metrics(y_true, y_prob, thr_opt),
        "optimal_threshold": round(thr_opt, 4),
    }
