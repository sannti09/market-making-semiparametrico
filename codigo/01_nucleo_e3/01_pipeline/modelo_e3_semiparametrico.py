"""E3 del anteproyecto (sec. 5.5 / 6.3): λ_i(t, δ | X) = exp(g_i(X_t) + h_i(t)) · e^{-k_i δ}, por lado i.

- g_i: no paramétrico (HistGradientBoosting con pérdida Poisson; RandomForest como robustez).
- h_i: nivel por hora UTC, centrado (media cero sobre las horas observadas) para identificación.
- k_i: perfil 1-D (sección áurea), como en E1.
- Backfitting alternando g, h y k.
- Familia: 'poisson' o 'nb'. 'nb' = "NB con media Poisson fija": g, h, k se ajustan con pérdida Poisson y
  después solo se perfila la dispersión α (NB2). NO es un ajuste propio de la media bajo NB (v37).

Reducción exacta para el paso g: con k y h fijos, Σ_δ [y_δ(η − kδ) − E e^{η−kδ}] = Y·η − E S(k) e^{η} + cte,
con Y = Σ_δ y_δ y S(k) = Σ_δ e^{−kδ}. Por eso el GBM ajusta una fila por bin con objetivo Y/(E S e^{h}) y
peso E S e^{h}, que en pérdida Poisson equivale al offset log(E S) + h. Las filas por δ comparten trades
(anidadas): verosimilitud compuesta, como en v34.
"""

import math
from typing import Dict, Optional, Sequence

import numpy as np

_PHI = (math.sqrt(5.0) - 1.0) / 2.0


def _aurea(f, a, b, n=60):
    c, d = b - _PHI * (b - a), a + _PHI * (b - a)
    fc, fd = f(c), f(d)
    for _ in range(n):
        if fc >= fd:
            b, d, fd = d, c, fc
            c = b - _PHI * (b - a)
            fc = f(c)
        else:
            a, c, fc = c, d, fd
            d = a + _PHI * (b - a)
            fd = f(d)
    return c if fc >= fd else d


def _lgamma(x):
    from math import lgamma
    return np.vectorize(lgamma, otypes=[float])(x)


def ll_poisson_filas(eta, k, conteos, expo, deltas):
    """ll_pp por fila (bin): Σ_δ [y_δ(η − kδ) − E e^{η − kδ}] (sin log y!, como en v34)."""
    lam = np.exp(eta)[:, None] * np.exp(-k * deltas)[None, :] * expo[:, None]
    return (conteos * (eta[:, None] - k * deltas[None, :]) - lam).sum(1)


def ll_conteo_filas(eta, k, conteos, expo, deltas, alpha=0.0):
    m = np.exp(eta)[:, None] * np.exp(-k * deltas)[None, :] * expo[:, None]
    y = conteos.astype(float)
    if alpha <= 1e-10:
        return (y * np.log(np.maximum(m, 1e-300)) - m - _lgamma(y + 1)).sum(1)
    r = 1.0 / alpha
    return (_lgamma(y + r) - math.lgamma(r) - _lgamma(y + 1) + r * np.log(r / (r + m))
            + y * np.log(np.maximum(m, 1e-300) / (r + m))).sum(1)


class ModeloE3Semiparametrico:
    def __init__(self, estimador: str = "gbm", familia: str = "poisson", n_backfit: int = 4,
                 usar_h: bool = True, params_gbm: Optional[Dict] = None, semilla: int = 0):
        self.estimador, self.familia, self.n_backfit, self.usar_h, self.semilla = estimador, familia, n_backfit, usar_h, semilla
        self.params_gbm = params_gbm or dict(max_iter=300, learning_rate=0.05, max_leaf_nodes=31,
                                             min_samples_leaf=500, l2_regularization=1.0)

    def _nuevo_g(self):
        if self.estimador == "gbm":
            from sklearn.ensemble import HistGradientBoostingRegressor
            return HistGradientBoostingRegressor(loss="poisson", random_state=self.semilla, **self.params_gbm)
        if self.estimador == "rf":
            from sklearn.ensemble import RandomForestRegressor
            return RandomForestRegressor(n_estimators=200, min_samples_leaf=500, max_features=0.5,
                                         n_jobs=-1, random_state=self.semilla)
        if self.estimador == "constante":
            return None
        raise ValueError(self.estimador)

    def _g(self, X):
        if self.g is None:
            return np.full(len(X), self.g0)
        return np.log(np.maximum(self.g.predict(X), 1e-12))

    def _h(self, hora):
        return (self.h[hora] if self.usar_h else np.zeros(len(hora))) + self.c0

    def ajustar(self, X, hora, conteos, expo, deltas):
        deltas = np.asarray(deltas, float)
        Y = conteos.sum(1).astype(float)
        self.k, self.h, self.g, self.g0, self.c0 = 0.3, np.zeros(24), None, math.log(max(Y.sum(), 1) / expo.sum()), 0.0
        hora = np.asarray(hora, int)
        self.historial = []
        for it in range(self.n_backfit):
            S = np.exp(-self.k * deltas).sum()
            # paso g (pérdida Poisson con offset log(E S) + h vía objetivo/peso)
            w = expo * S * np.exp(self._h(hora))
            self.g = self._nuevo_g()
            if self.g is None:
                self.g0 = math.log(max(Y.sum(), 1e-12) / w.sum())
            else:
                self.g.fit(X, Y / w, sample_weight=w)
            g = self._g(X)
            # paso h (forma cerrada por hora, centrado)
            if self.usar_h:
                den = np.bincount(hora, weights=expo * S * np.exp(g), minlength=24)
                num = np.bincount(hora, weights=Y, minlength=24)
                obs = den > 0
                h = np.zeros(24)
                h[obs] = np.log(np.maximum(num[obs], 0.5) / den[obs])
                h[obs] -= h[obs].mean()
                self.h = h
            eta = g + self._h(hora)
            # paso k con la escala perfilada en forma cerrada: c = ΣY / (Σ E e^η · S(k)); c se acumula en c0
            nd = conteos.sum(0).astype(float)
            ee = float((expo * np.exp(eta)).sum())
            sy, snd = float(Y.sum()), float((nd * deltas).sum())
            self.k = _aurea(lambda k: sy * math.log(max(sy, 1e-12) / (ee * np.exp(-k * deltas).sum())) - k * snd, -5.0, 50.0)
            self.c0 += math.log(max(sy, 1e-12) / (ee * np.exp(-self.k * deltas).sum()))
            eta = g + self._h(hora)
            self.historial.append({"iter": it, "k": self.k, "ll_pp": float(ll_poisson_filas(eta, self.k, conteos, expo, deltas).sum())})
        self.alpha = 0.0
        self.etiqueta_familia = "Poisson" if self.familia != "nb" else "NB con media Poisson fija"
        if self.familia == "nb":
            eta = self._g(X) + self._h(hora)
            la = _aurea(lambda la: float(ll_conteo_filas(eta, self.k, conteos, expo, deltas, math.exp(la)).sum()),
                        math.log(1e-6), math.log(100.0), n=40)
            self.alpha = math.exp(la)
        return self

    def eta(self, X, hora):
        return self._g(X) + self._h(np.asarray(hora, int))

    def evaluar(self, X, hora, conteos, expo, deltas):
        deltas = np.asarray(deltas, float)
        e = self.eta(X, hora)
        lp = ll_poisson_filas(e, self.k, conteos, expo, deltas)
        lc = ll_conteo_filas(e, self.k, conteos, expo, deltas, self.alpha)
        m = np.exp(e)[:, None] * np.exp(-self.k * deltas)[None, :] * expo[:, None]
        y = conteos.astype(float)
        dev = 2 * np.where(y > 0, y * np.log(np.maximum(y, 1e-300) / m), 0.0) - 2 * (y - m)
        return {"n_bins": len(e), "ll_pp": float(lp.sum()), "ll_conteo": float(lc.sum()),
                "deviance_poisson_media": float(dev.mean()), "k": self.k, "alpha_nb": self.alpha,
                "familia": self.etiqueta_familia}
