"""v110: HJB de market making (Guéant) con intensidad general Λ(δ) = A·exp(g(δ)), g lineal a trozos (log) sobre nodos δ_j.

Fuera de [δ_1, δ_J] se extiende con la pendiente del primer/último tramo. En el tramo s: Λ = A exp(c_s − k_s δ), k_s > 0.
H(p) = sup_δ Λ(δ)(1 − e^{−γ(δ−p)})/γ: en cada tramo δ_s = p + (1/γ)ln(1+γ/k_s) recortado al tramo; H = máx sobre tramos.
Derivada (envolvente): H'(p) = −Λ(δ*) e^{−γ(δ*−p)}. Sistema y solver estacionario como v49 (importado, sin editar).
"""
import itertools
import math
import multiprocessing as mp
import sys
from pathlib import Path

import numpy as np

_V49 = Path(__file__).resolve().parents[2] / "08_hjb_exponencial"
sys.path.insert(0, str(_V49))
import hjb_numerico as H49  # noqa: E402

LO_EXT, HI_EXT = -5.0, 40.0   # dominio admisible (Enmienda B)
K_MIN = 0.01


def forma_k(kraw, d):
    """Forma desde pendientes por tramo (último eje S). Fuerza k >= K_MIN y reconstruye g continua desde g(δ_1)=0.
    Devuelve dict con k, c, lo, hi, nflag (tramos corregidos, mismo shape que kraw sin el último eje sumado)."""
    kraw = np.asarray(kraw, float); d = np.asarray(d, float)
    k = np.maximum(kraw, K_MIN)
    gg = np.concatenate([np.zeros(kraw.shape[:-1] + (1,)), -np.cumsum(k * np.diff(d), -1)], -1)
    c = gg[..., :-1] + k * d[:-1]
    lo = np.concatenate([[LO_EXT], d[1:-1]]); hi = np.concatenate([d[1:-1], [HI_EXT]])
    return {"k": k, "c": c, "lo": lo, "hi": hi, "nflag": (kraw < K_MIN).sum(-1)}


def forma(g, d):
    g, d = np.asarray(g, float), np.asarray(d, float)
    return forma_k(-(g[1:] - g[:-1]) / (d[1:] - d[:-1]), d)


def Hgen(p, k, c, lo, hi, gamma):
    """p (...,) ; k, c, lo, hi con último eje S y difundibles con p[..., None]. Devuelve (H, δ*, H') para A = 1."""
    P = np.asarray(p, float)[..., None]
    d = np.clip(P + np.log1p(gamma / k) / gamma, lo, hi)
    lam = np.exp(np.minimum(c - k * d, 700.0))
    e = np.exp(np.minimum(-gamma * (d - P), 700.0))
    val = lam * (1.0 - e) / gamma
    s = np.argmax(val, axis=-1)[..., None]
    Hm = np.take_along_axis(val, s, -1)[..., 0]
    ds = np.take_along_axis(d, s, -1)[..., 0]
    Hp = -np.take_along_axis(lam * e, s, -1)[..., 0]
    return Hm, ds, Hp


def H_fuerza_bruta(p, F, gamma, n=200_001, extra=None):
    """sup por rejilla fina en [p−5, p+100] más los nodos (y extra)."""
    d = np.linspace(max(p - 5.0, LO_EXT), min(p + 100.0, HI_EXT), n)
    if extra is not None:
        d = np.concatenate([d, np.asarray(extra, float)])
    # curva por δ: tramo con lo<=δ<hi (tramo izquierdo y derecho extendidos)
    ed = np.concatenate([F["lo"][:1], F["hi"][:-1]])   # bordes internos
    idx = np.clip(np.searchsorted(F["hi"][:-1], d, side="right"), 0, len(F["k"]) - 1)
    lam = np.exp(F["c"][idx] - F["k"][idx] * d)
    v = lam * (1.0 - np.exp(-gamma * (d - p))) / gamma
    j = int(np.argmax(v))
    return float(v[j]), float(d[j])


def _campo(theta, g, Fb, Fa, Aa, Ab, sig, Q):
    n = 2 * Q + 1
    q = np.arange(-Q, Q + 1, dtype=float)
    P = np.vstack([theta[:-1] - theta[1:], theta[1:] - theta[:-1]])          # (2, 2Q): compra, venta
    K = np.stack([Fb["k"], Fa["k"]])[:, None, :]
    C = np.stack([Fb["c"], Fa["c"]])[:, None, :]
    Hm, _, Hp = Hgen(P, K, C, Fb["lo"], Fb["hi"], g)
    Hb, Ha = Ab * Hm[0], Aa * Hm[1]
    Hbp, Hap = Ab * Hp[0], Aa * Hp[1]
    F = -0.5 * g * sig ** 2 * q ** 2
    F[:-1] += Hb
    F[1:] += Ha
    J = np.zeros((n, n))
    j = np.arange(2 * Q)
    J[j, j] += Hbp
    J[j, j + 1] -= Hbp
    J[j + 1, j + 1] += Hap
    J[j + 1, j] -= Hap
    return F, J


def estacionario_general(g, Fa, Fb, Aa, Ab, sig, Q, tol=1e-9, max_it=300):
    """Solución ergódica θ∞ (θ(0)=0), c, iteraciones, dispersión. Mismo esquema que H49.estacionario."""
    n = 2 * Q + 1
    th = np.zeros(n)
    _, J0 = _campo(th, g, Fb, Fa, Aa, Ab, sig, Q)
    r0 = np.abs(J0).sum(1).max()
    dt = 0.1 / r0
    for it in range(max_it):
        F, J = _campo(th, g, Fb, Fa, Aa, Ab, sig, Q)
        esc = max(np.abs(F).max(), 1e-300)
        if (F.max() - F.min()) < tol * esc + 1e-14 * r0:
            break
        th = th + np.linalg.solve(np.eye(n) - dt * J, dt * F)
        th -= th[Q]
        dt = min(dt * 1.7, 1e9 / r0)
    idx = [i for i in range(n) if i != Q]
    for _ in range(4):
        F, J = _campo(th, g, Fb, Fa, Aa, Ab, sig, Q)
        c = F.mean()
        R = F - c
        if np.abs(R).max() < 1e-13 * max(np.abs(F).max(), 1e-300):
            break
        A_ = np.hstack([J[:, idx], -np.ones((n, 1))])
        dlt = np.linalg.solve(A_, -R)
        th2 = th.copy()
        th2[idx] += dlt[:-1]
        F2 = _campo(th2, g, Fb, Fa, Aa, Ab, sig, Q)[0]
        if (F2.max() - F2.min()) <= (F.max() - F.min()):
            th = th2
        else:
            break
    F = _campo(th, g, Fb, Fa, Aa, Ab, sig, Q)[0]
    return th, float(F.mean()), it, float(F.max() - F.min())


def pol_desde_theta(th):
    """[p_b(q=−Q..Q−1) | p_a(q=−Q+1..Q)] (4Q valores con Q → 2Q cada uno)."""
    return np.concatenate([th[:-1] - th[1:], th[1:] - th[:-1]])


def deltas_desde_p(p, Fa, Fb, g, trozo=8000):
    """p: (n, 4Q) [p_b | p_a]; Fa, Fb: formas fijas (k (S,)) o por fila (k (n,S)). Devuelve (Da, Db) (n, 2Q+1) con NaN en bordes."""
    n, m = p.shape
    Q2 = m // 2
    Da, Db = np.full((n, Q2 + 1), np.nan), np.full((n, Q2 + 1), np.nan)
    for i0 in range(0, n, trozo):
        s = slice(i0, min(i0 + trozo, n))
        for Fx, cols, D, sl in ((Fb, slice(0, Q2), Db, slice(0, Q2)), (Fa, slice(Q2, m), Da, slice(1, Q2 + 1))):
            k, c = Fx["k"], Fx["c"]
            if k.ndim == 2:
                k, c = k[s][:, None, :], c[s][:, None, :]
            D[s, sl] = Hgen(p[s, cols], k, c, Fx["lo"], Fx["hi"], g)[1]
    return Da, Db


# ------------------------------------------------------------------ tablas
_SPEC = None


def _resolver(ix):
    """Trabajador: resuelve el nodo ix de la tabla activa (_SPEC)."""
    t = _SPEC
    nodo = [t.ejes[a][i] for a, i in enumerate(ix)]
    Fa, Fb = t.formas(nodo)
    u, v = nodo[0], nodo[1]
    th = estacionario_general(t.g, Fa, Fb, 1.0, math.exp(v), math.exp(0.5 * u), t.Q)[0]
    return ix, pol_desde_theta(th)


class TablaG(H49.Tabla):
    """Tabla 2D (u, v) con formas fijas (ga, gb) o 4D (u, v, m_a, m_b) con g = m·f. Guarda p; δ* se evalúa aparte."""

    def __init__(self, g, Q, ejes, d, ga, gb):
        super().__init__(g, Q, ejes)
        self.d_nodos, self.ga, self.gb = np.asarray(d, float), np.asarray(ga, float), np.asarray(gb, float)
        self.dim = len(ejes)

    def formas(self, nodo):
        if self.dim == 2:
            return forma(self.ga, self.d_nodos), forma(self.gb, self.d_nodos)
        return forma(nodo[2] * self.ga, self.d_nodos), forma(nodo[3] * self.gb, self.d_nodos)

    def construir(self, procesos=1):
        global _SPEC
        _SPEC = self
        idxs = list(itertools.product(*[range(n) for n in self.forma]))
        if procesos > 1:
            with mp.get_context("fork").Pool(procesos) as pool:
                res = pool.map(_resolver, idxs, chunksize=64)
        else:
            res = [_resolver(ix) for ix in idxs]
        for ix, pv in res:
            self.datos[ix] = pv
        return self

    def deltas_exactos(self, X, Fa, Fb):
        """X: (n,2) o (n,4) coordenadas. Fa, Fb: formas del segundo (fijas o por fila). Devuelve (Da, Db, frac_recortada)."""
        p, rec = self.interpolar(X)
        Da, Db = deltas_desde_p(p, Fa, Fb, self.g)
        return Da, Db, rec


def forma_por_fila(f, m, d):
    """Formas por fila para g = m_i·f (m: (n,)): pendientes m·k_raw(f), con piso K_MIN."""
    f, d = np.asarray(f, float), np.asarray(d, float)
    k0 = -(f[1:] - f[:-1]) / (d[1:] - d[:-1])
    return forma_k(np.asarray(m)[:, None] * k0[None, :], d)
