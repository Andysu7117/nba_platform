"""Evaluation metrics for the binary game-winner model.

Thin wrappers around scikit-learn so the metric set is defined in exactly one
place and reused by both training and any ad-hoc evaluation.
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss


def compute_accuracy(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """Classification accuracy using a 0.5 probability threshold."""
    y_pred = (np.asarray(y_prob) >= 0.5).astype(int)
    return float(accuracy_score(y_true, y_pred))


def compute_log_loss(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """Log loss (cross-entropy). ``labels`` pinned so it is robust to one-class
    slices."""
    return float(log_loss(y_true, y_prob, labels=[0, 1]))


def compute_brier(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """Brier score (mean squared error of probabilistic predictions)."""
    return float(brier_score_loss(y_true, y_prob))


def evaluate_predictions(y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, float]:
    """Return all three headline metrics as a dict."""
    return {
        "accuracy": compute_accuracy(y_true, y_prob),
        "log_loss": compute_log_loss(y_true, y_prob),
        "brier_score": compute_brier(y_true, y_prob),
    }
