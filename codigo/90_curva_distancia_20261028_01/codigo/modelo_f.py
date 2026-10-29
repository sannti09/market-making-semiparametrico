"""v90: E3 con curva monótona de distancia f(δ) en lugar de −kδ (y variante f(δ)·m(X)). Reutiliza ModeloE3Semiparametrico (v37) sin editarlo.

E3-f:   log λ_i(t, δ) = g(X) + h(t) + f(δ),        f(δ_1) = 0, f decreciente.
E3-fkX: log λ_i(t, δ) = g(X) + h(t) + m(X)·f(δ),   m(X) = exp(b·z), z estandarizadas (m ≈ 1 en la media).

Parametrización del plan: f(δ_j) = −Σ_{i=2..j} exp(θ_i)(δ_i − δ_{i−1}). En E3-f, con g y h fijos, el máximo de la
verosimilitud en f es cerrado: f_j = log(N_j / N_1), N_j = Σ_bins y_j (los cruces están anidados, así que N_j es
no creciente y f es monótona sin restricción activa). En E3-fkX el paso (a, θ, b) usa L-BFGS con gradiente analítico.
"""
import math
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "37_correcciones_revision_astra_v36_20261026_01" / "01_pipeline"))
from modelo_e3_semiparametrico import ModeloE3Semiparametrico  # noqa: E402


def ll_f_filas(eta, F, conteos, expo):
    """ll_pp por bin con exponente aditivo F (n×J o J)."""
    F = np.broadcast_to(F, conteos.shape)
    return (conteos * (eta[:, None] + F) - np.exp(eta[:, None] + F) * expo[:, None]).sum(1)


def f_de_theta(th, deltas):
    return np.concatenate([[0.0], -np.cumsum(np.exp(th) * np.diff(deltas))])


def theta_de_f(f, deltas):
    return np.log(np.maximum(-np.diff(f) / np.diff(deltas), 1e-6))


class ModeloF(ModeloE3Semiparametrico):
    def _g_h_paso(self, X, hora, Y, expo, S):
        w = expo * S * np.exp(self._h(hora))
        self.g = self._nuevo_g()
        self.g.fit(X, Y / w, sample_weight=w)
        g = self._g(X)
        if self.usar_h:
            den = np.bincount(hora, weights=expo * S * np.exp(g), minlength=24)
            num = np.bincount(hora, weights=Y, minlength=24)
            obs = den > 0
            h = np.zeros(24)
            h[obs] = np.log(np.maximum(num[obs], 0.5) / den[obs])
            h[obs] -= h[obs].mean()
            self.h = h
        return g

    def ajustar(self, X, hora, conteos, expo, deltas):
        deltas = np.asarray(deltas, float)
        Y = conteos.sum(1).astype(float)
        self.f = -0.3 * (deltas - deltas[0])
        self.h, self.g, self.g0, self.c0 = np.zeros(24), None, math.log(max(Y.sum(), 1) / expo.sum()), 0.0
        hora = np.asarray(hora, int)
        self.historial = []
        N = np.maximum(conteos.sum(0).astype(float), 0.5)
        for it in range(self.n_backfit):
            g = self._g_h_paso(X, hora, Y, expo, np.exp(self.f).sum())
            eta = g + self._h(hora)
            self.f = np.minimum.accumulate(np.log(N / N[0]))
            ee = float((expo * np.exp(eta)).sum())
            self.c0 += math.log(Y.sum() / (ee * np.exp(self.f).sum()))
            eta = g + self._h(hora)
            self.historial.append({"iter": it, "f": self.f.tolist(), "ll_pp": float(ll_f_filas(eta, self.f, conteos, expo).sum())})
        return self

    def log_lam(self, X, hora, deltas, Z=None):
        return self.eta(X, hora)[:, None] + self.f[None, :]


class ModeloFKX(ModeloF):
    def __init__(self, f_ini, **kw):
        super().__init__(**kw)
        self.f_ini = np.asarray(f_ini, float)

    def _m(self, Z):
        return np.exp(np.clip(Z @ self.b, -5, 5))

    def _paso(self, eta, Z, conteos, expo, deltas):
        dd = np.diff(deltas)
        x0 = np.concatenate([[0.0], theta_de_f(self.f, deltas), self.b])
        p = Z.shape[1]

        def obj(x):
            a, th, b = x[0], x[1:-p], x[-p:]
            f = f_de_theta(th, deltas)
            m = np.exp(np.clip(Z @ b, -5, 5))
            mf = m[:, None] * f[None, :]
            lam = np.exp(eta[:, None] + a + mf) * expo[:, None]
            r = conteos - lam
            ll = float((conteos * (eta[:, None] + a + mf)).sum() - lam.sum())
            Gf = (m[:, None] * r).sum(0)                       # ∂ℓ/∂f_j
            gth = -np.exp(th) * dd * np.cumsum(Gf[::-1])[::-1][1:]   # ∂f_j/∂θ_k = −e^{θ_k}Δδ_k para j ≥ k
            gb = Z.T @ (m * (r * f[None, :]).sum(1))
            return -ll, -np.concatenate([[r.sum()], gth, gb])

        res = minimize(obj, x0, jac=True, method="L-BFGS-B", options={"maxiter": 200})
        x = res.x
        return x[0], f_de_theta(x[1:-p], deltas), x[-p:]

    def ajustar(self, X, Z, hora, conteos, expo, deltas):
        deltas = np.asarray(deltas, float)
        Y = conteos.sum(1).astype(float)
        Z = np.asarray(Z, float)
        self.f, self.b = self.f_ini.copy(), np.zeros(Z.shape[1])
        self.h, self.g, self.g0, self.c0 = np.zeros(24), None, math.log(max(Y.sum(), 1) / expo.sum()), 0.0
        hora = np.asarray(hora, int)
        self.historial = []
        for it in range(self.n_backfit):
            S = np.exp(self._m(Z)[:, None] * self.f[None, :]).sum(1)
            g = self._g_h_paso(X, hora, Y, expo, S)
            eta = g + self._h(hora)
            a, self.f, self.b = self._paso(eta, Z, conteos, expo, deltas)
            self.c0 += a
            eta = g + self._h(hora)
            F = self._m(Z)[:, None] * self.f[None, :]
            self.historial.append({"iter": it, "f": self.f.tolist(), "b": self.b.tolist(), "ll_pp": float(ll_f_filas(eta, F, conteos, expo).sum())})
        return self

    def log_lam(self, X, hora, deltas, Z=None):
        return self.eta(X, hora)[:, None] + self._m(np.asarray(Z, float))[:, None] * self.f[None, :]
