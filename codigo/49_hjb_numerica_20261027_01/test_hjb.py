"""Tests de la HJB numérica (v49). Ejecutar: python -m unittest test_hjb -v"""
import math
import unittest

import numpy as np
from scipy.linalg import expm

import hjb_numerico as H

Q = 10


class TestHJB(unittest.TestCase):
    def test_H_cerrada_y_delta_optimo(self):
        """H_i(p) en forma cerrada = sup numérico; el argmax es p + (1/γ)ln(1+γ/k)."""
        for g, k, A, p in [(0.1, 0.62, 0.3, 0.7), (1.0, 0.75, 1.2, -0.5), (0.01, 0.3, 0.05, 2.0)]:
            self.assertAlmostEqual(H.H(p, A, k, g) / H.H_numerica(p, A, k, g), 1.0, places=6)
            d = np.linspace(p - 3, p + 60, 2_000_001)
            f = A * np.exp(-k * d) * (1 - np.exp(-g * (d - p))) / g
            self.assertAlmostEqual(d[f.argmax()], p + H.base(g, k), places=3)

    def test_a_gueant_lineal(self):
        """(a) k y A simétricos: ODE temporal y estacionario coinciden con w = e^{kθ}, ∂_τ w = M w."""
        g, k, A, sig = 0.1, 0.62, 0.27, 1.0
        M, w_inf, th_g = H.guent_lineal(g, k, A, sig, Q)
        for tau in (1.0, 20.0, 150.0):
            th = H.integrar(g, k, k, A, A, sig, Q, tau, cfl=0.05)
            th_exp = np.log(expm(M * tau) @ np.ones(2 * Q + 1)) / k
            self.assertLess(np.abs(th - th_exp).max(), 1e-7, tau)
        th, c, _, spread = H.estacionario(g, k, k, A, A, sig, Q)
        self.assertLess(spread, 1e-9)
        # diferencias θ(q) − θ(q+1) en el rango central (el vector propio tiene cola de precisión relativa baja)
        pb = (th[:-1] - th[1:])[Q - 6:Q + 6]
        pb_g = (th_g[:-1] - th_g[1:])[Q - 6:Q + 6]
        self.assertLess(np.abs(pb - pb_g).max(), 1e-5)
        # θ(τ) largo: las diferencias convergen a las estacionarias
        tl = H.integrar(g, k, k, A, A, sig, Q, 3000.0)
        self.assertLess(np.abs((tl[:-1] - tl[1:]) - (th[:-1] - th[1:])).max(), 1e-4)
        # asimétrico en A pero igual k sigue siendo lineal
        Ab = 0.5
        eta_a, eta_b = k * A * H.cte(g, k), k * Ab * H.cte(g, k)
        qv = np.arange(-Q, Q + 1)
        Ml = np.diag(-0.5 * k * g * sig ** 2 * qv ** 2.0) + eta_b * np.eye(2 * Q + 1, k=1) + eta_a * np.eye(2 * Q + 1, k=-1)
        th_n = H.integrar(g, k, k, A, Ab, sig, Q, 40.0, cfl=0.05)
        self.assertLess(np.abs(th_n - np.log(expm(Ml * 40.0) @ np.ones(2 * Q + 1)) / k).max(), 1e-7)

    def test_b_glft_en_el_centro(self):
        """(b) γ pequeño y Q grande: la aproximación GLFT es cercana en el centro del rango de inventario."""
        k, A, sig, Qg = 0.62, 0.27, 1.0, 40
        errs = []
        for g in (0.003, 0.01):
            th = H.estacionario(g, k, k, A, A, sig, Qg)[0]
            Da, Db = H.politica(th, g, k, k)
            q = np.arange(-4, 5)
            da_g, db_g = H.glft(q, g, k, k, A, A, sig)
            w = math.sqrt(sig ** 2 * g / (2 * k * A) * (1 + g / k) ** (1 + k / g))
            e = max(np.abs(Db[Qg + q] - db_g).max(), np.abs(Da[Qg + q] - da_g).max())
            self.assertLess(e, 0.1 * w)          # error < 10 % de la escala de inventario ω
            errs.append(e)
        self.assertLess(errs[0], errs[1])         # el error baja con γ

    def test_c_monotonia(self):
        """(c) δ_b*(q) creciente en q y δ_a*(q) decreciente, también con k, A y σ distintos por lado."""
        for par in [(0.1, 0.62, 0.62, 0.27, 0.27, 1.0), (1.0, 0.62, 0.75, 0.3, 0.5, 1.2), (0.01, 0.4, 0.9, 0.2, 0.4, 0.6)]:
            th = H.estacionario(*par, Q)[0]
            Da, Db = H.politica(th, par[0], par[1], par[2])
            self.assertTrue(np.all(np.diff(Db[:-1]) > 0))
            self.assertTrue(np.all(np.diff(Da[1:]) < 0))

    def test_d_cero_inventario(self):
        """(d) q = 0 simétrico: δ* = (1/γ)ln(1+γ/k) + corrección pequeña ≥ 0; con σ → 0 la corrección es de borde exacta."""
        g, k, A = 0.1, 0.62, 0.27
        th = H.estacionario(g, k, k, A, A, 1.0, Q)[0]
        Da, Db = H.politica(th, g, k, k)
        self.assertAlmostEqual(Da[Q], Db[Q], places=10)
        corr = Db[Q] - H.base(g, k)
        self.assertTrue(0 < corr < 1.0)
        # σ → 0: w(q) ∝ cos(π q / (2(Q+1))) ⇒ p_b(q) = (1/k) ln[cos(πq/(2(Q+1))) / cos(π(q+1)/(2(Q+1)))]
        th0 = H.estacionario(g, k, k, A, A, 1e-6, Q)[0]
        Da0, Db0 = H.politica(th0, g, k, k)
        exacto = math.log(1.0 / math.cos(math.pi / (2 * (Q + 1)))) / k
        self.assertAlmostEqual(Db0[Q] - H.base(g, k), exacto, places=6)
        # y γ → 0 con σ pequeño: la corrección tiende a ser mínima
        self.assertLess(Db0[Q] - H.base(g, k), 0.03)

    def test_e_tabla_interpolacion(self):
        """La tabla 2D reproduce la solución exacta en puntos aleatorios (error de interpolación acotado)."""
        g, ka, kb = 0.1, 0.62, 0.75
        u = np.linspace(-7.5, 7.5, 31)
        v = np.linspace(-4, 4, 17)
        T = H.Tabla(g, Q, [u, v], ka, kb).construir()
        rng = np.random.default_rng(0)
        X = np.column_stack([rng.uniform(-6, 6, 60), rng.uniform(-3, 3, 60)])
        Da, Db, rec = T.deltas(X, ka, kb)
        self.assertEqual(rec, 0.0)
        err = 0.0
        for x, da, db in zip(X, Da, Db):
            th = H.estacionario(g, ka, kb, 1.0, math.exp(x[1]), math.exp(x[0] / 2), Q)[0]
            ea, eb = H.politica(th, g, ka, kb)
            err = max(err, np.nanmax(np.abs(da - ea)), np.nanmax(np.abs(db - eb)))
        self.assertLess(err, 0.05)   # bps


if __name__ == "__main__":
    unittest.main()
