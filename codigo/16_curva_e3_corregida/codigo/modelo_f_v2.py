"""v108: versión 2 de ModeloFKX (v90 sin editar). Cambios en el paso de la curva (a, θ, b):
(1) el gradiente incorpora la derivada del recorte de Z·b a ±5 (nula donde el recorte está activo);
(2) L-BFGS con maxiter 2000 y convergencia comprobada (se guarda el resultado del optimizador)."""
import sys
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "05_curva_distancia" / "codigo"))
from modelo_f import ModeloFKX, f_de_theta, theta_de_f  # noqa: E402


def paso_curva(eta, Z, conteos, expo, deltas, f, b, maxiter=2000):
    """Paso (a, θ, b) con g + h fijos (eta). Devuelve a, f, b y el resultado del optimizador."""
    dd = np.diff(deltas); p = Z.shape[1]
    x0 = np.concatenate([[0.0], theta_de_f(f, deltas), b])

    def obj(x):
        a, th, bb = x[0], x[1:-p], x[-p:]
        ff = f_de_theta(th, deltas); zb = Z @ bb
        m = np.exp(np.clip(zb, -5, 5)); mf = m[:, None] * ff[None, :]
        lam = np.exp(eta[:, None] + a + mf) * expo[:, None]; r = conteos - lam
        ll = float((conteos * (eta[:, None] + a + mf)).sum() - lam.sum())
        Gf = (m[:, None] * r).sum(0)
        gth = -np.exp(th) * dd * np.cumsum(Gf[::-1])[::-1][1:]
        dm = np.where(np.abs(zb) < 5, m * (r * ff[None, :]).sum(1), 0.0)
        return -ll, -np.concatenate([[r.sum()], gth, Z.T @ dm])

    res = minimize(obj, x0, jac=True, method="L-BFGS-B", options={"maxiter": maxiter})
    return res.x[0], f_de_theta(res.x[1:-p], deltas), res.x[-p:], res


class ModeloFKXv2(ModeloFKX):
    def _paso(self, eta, Z, conteos, expo, deltas):
        a, f, b, res = paso_curva(eta, Z, conteos, expo, deltas, self.f, self.b)
        self.optimizador = {"success": bool(res.success), "nit": int(res.nit), "mensaje": str(res.message)}
        return a, f, b
