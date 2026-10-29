"""Métricas compartidas (v37)."""

import numpy as np


def auc(score, y):
    """AUC de Mann-Whitney con rango medio en los empates (un score constante da 0,5)."""
    score = np.asarray(score, float)
    y = np.asarray(y, bool)
    _, inv, cnt = np.unique(score, return_inverse=True, return_counts=True)
    r = (np.cumsum(cnt) - (cnt - 1) / 2.0)[inv]
    n1 = int(y.sum())
    n0 = len(y) - n1
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)) if n1 and n0 else float("nan")
