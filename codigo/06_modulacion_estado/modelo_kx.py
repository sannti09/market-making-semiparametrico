"""v47: E3 con decaimiento dependiente del estado, k_i(X) = exp(c + b·z). Reutiliza ModeloE3Semiparametrico.

Mismo paso g/h que E3 pero con S_i = Σ_δ e^{-k_i δ} por bin. Paso (a,c,b): Newton amortiguado sobre el ll Poisson
dado eta (a = nivel aditivo que se acumula en c0, como la escala perfilada de E3). Con b=0 reduce a E3 escalar.
"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "01_nucleo_e3" / "01_pipeline"))
from modelo_e3_semiparametrico import ModeloE3Semiparametrico, ll_poisson_filas  # noqa: E402

_LIM = (-7.0, 4.0)


def _k_bins(c, b, Z):
    return np.exp(np.clip(c + Z @ b, *_LIM))


def ll_kx_filas(eta, k, conteos, expo, deltas):
    """ll_pp por bin con k por bin (k: [n])."""
    kd = k[:, None] * deltas[None, :]
    lam = np.exp(eta)[:, None] * np.exp(-kd) * expo[:, None]
    return (conteos * (eta[:, None] - kd) - lam).sum(1)


class ModeloKX(ModeloE3Semiparametrico):
    def __init__(self, n_iter_newton=25, **kw):
        super().__init__(**kw)
        self.n_iter_newton = n_iter_newton

    def _kb(self, Z):
        return _k_bins(self.c, self.b, Z)

    def _paso_cb(self, eta, Z, conteos, expo, deltas):
        """Maximiza en (a,c,b) Σ_i Σ_δ y(η+a−kδ) − E e^{η+a} e^{−kδ}. Devuelve (a, c, b)."""
        n, p = Z.shape
        U = np.hstack([np.ones((n, 1)), Z])
        Y = conteos.sum(1).astype(float)
        D = conteos @ deltas
        th = np.concatenate([[0.0], [self.c], self.b])

        def partes(th):
            k = np.exp(np.clip(th[1] + Z @ th[2:], *_LIM))
            return k

        def f(th):
            k = partes(th)
            return float(ll_kx_filas(eta + th[0], k, conteos, expo, deltas).sum())

        f0 = f(th)
        for _ in range(self.n_iter_newton):
            k = partes(th)
            ek = np.exp(-k[:, None] * deltas[None, :])
            S, T1, T2 = ek.sum(1), (ek * deltas).sum(1), (ek * deltas ** 2).sum(1)
            Ee = expo * np.exp(eta + th[0])
            dk = -D + Ee * T1                      # ∂ℓ/∂k
            d2k = -Ee * T2                         # ∂²ℓ/∂k²
            g = np.concatenate([[(Y - Ee * S).sum()], U.T @ (dk * k)])
            H = np.zeros((p + 2, p + 2))
            H[0, 0] = -(Ee * S).sum()
            m = Ee * T1 * k
            H[0, 1:] = H[1:, 0] = U.T @ m
            H[1:, 1:] = (U * (d2k * k ** 2 + dk * k)[:, None]).T @ U
            # ridge hasta que -H sea definida positiva (dirección de ascenso)
            lam = 1e-8 * max(1.0, np.abs(np.diag(H)).max())
            while True:
                try:
                    paso = np.linalg.solve(-H + lam * np.eye(p + 2), g)
                    if g @ paso > 0:
                        break
                except np.linalg.LinAlgError:
                    pass
                lam *= 10
            t, ok = 1.0, False
            for _ in range(30):
                fn = f(th + t * paso)
                if fn >= f0:
                    ok = True
                    break
                t *= 0.5
            if not ok:
                break
            mejora = fn - f0
            th, f0 = th + t * paso, fn
            if mejora < 1e-9 * max(1.0, abs(f0)):
                break
        return th[0], th[1], th[2:]

    def ajustar(self, X, Z, hora, conteos, expo, deltas):
        deltas = np.asarray(deltas, float)
        Y = conteos.sum(1).astype(float)
        Z = np.asarray(Z, float)
        self.c, self.b = math.log(0.3), np.zeros(Z.shape[1])
        self.h, self.g, self.g0, self.c0 = np.zeros(24), None, math.log(max(Y.sum(), 1) / expo.sum()), 0.0
        hora = np.asarray(hora, int)
        self.historial = []
        for it in range(self.n_backfit):
            S = np.exp(-self._kb(Z)[:, None] * deltas[None, :]).sum(1)
            w = expo * S * np.exp(self._h(hora))
            self.g = self._nuevo_g()
            if self.g is None:
                self.g0 = math.log(max(Y.sum(), 1e-12) / w.sum())
            else:
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
            eta = g + self._h(hora)
            a, self.c, self.b = self._paso_cb(eta, Z, conteos, expo, deltas)
            self.c0 += a
            eta = g + self._h(hora)
            ll = float(ll_kx_filas(eta, self._kb(Z), conteos, expo, deltas).sum())
            self.historial.append({"iter": it, "c": float(self.c), "b": [float(x) for x in self.b], "ll_pp": ll})
        self.k = float(np.exp(self.c))
        return self

    def evaluar(self, X, Z, hora, conteos, expo, deltas):
        deltas = np.asarray(deltas, float)
        e = self.eta(X, hora)
        k = self._kb(np.asarray(Z, float))
        return {"n_bins": len(e), "ll_pp": float(ll_kx_filas(e, k, conteos, expo, deltas).sum())}

    def prob(self, X, Z, hora, expo, delta):
        k = self._kb(np.asarray(Z, float))
        return 1 - np.exp(-np.exp(self.eta(X, hora) - k * delta) * expo)
