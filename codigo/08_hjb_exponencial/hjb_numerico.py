"""v49: HJB numérica de market making con inventario acotado y CARA (Guéant-Lehalle-Fernandez-Tapia), intensidades A_i e^{-k_i δ}.

Ansatz u = -exp(-γ(x + qS + θ(t,q))). Con τ = T − t:
  ∂_τ θ(q) = -½γσ²q² + 1_{q<Q} H_b(θ(q) − θ(q+1)) + 1_{q>-Q} H_a(θ(q) − θ(q−1)),   θ(τ=0, q) = 0,
  H_i(p) = A_i C_i e^{-k_i p},   C_i = (1+γ/k_i)^{-k_i/γ}/(k_i+γ),   δ_i* = p + (1/γ) ln(1+γ/k_i).
Unidades: δ en bps, tiempo en s, A por s, k por bps, σ en bps/√s.
"""
import itertools
import math

import numpy as np


def cte(gamma, k):
    return (1.0 + gamma / k) ** (-k / gamma) / (k + gamma)


def base(gamma, k):
    return np.log1p(gamma / np.asarray(k, float)) / gamma


def H(p, A, k, gamma):
    """sup_δ A e^{-kδ}(1 − e^{-γ(δ−p)})/γ en forma cerrada."""
    return A * cte(gamma, k) * np.exp(-k * np.asarray(p, float))


def H_numerica(p, A, k, gamma):
    """Verificación por fuerza bruta de H (rejilla fina de δ)."""
    d = np.linspace(p - 5.0, p + 80.0, 400001)
    return float((A * np.exp(-k * d) * (1 - np.exp(-gamma * (d - p))) / gamma).max())


def campo(theta, g, ka, kb, Aa, Ab, sig, Q):
    """F(θ) = ∂_τθ y su jacobiano J (denso, (2Q+1)²)."""
    n = 2 * Q + 1
    q = np.arange(-Q, Q + 1, dtype=float)
    pb = theta[:-1] - theta[1:]                 # compra en q = -Q..Q-1
    pa = theta[1:] - theta[:-1]                 # venta en q = -Q+1..Q
    Hb = Ab * cte(g, kb) * np.exp(np.clip(-kb * pb, -700, 600))
    Ha = Aa * cte(g, ka) * np.exp(np.clip(-ka * pa, -700, 600))
    F = -0.5 * g * sig ** 2 * q ** 2
    F[:-1] += Hb
    F[1:] += Ha
    J = np.zeros((n, n))
    j = np.arange(2 * Q)
    J[j, j] += -kb * Hb
    J[j, j + 1] += kb * Hb
    J[j + 1, j + 1] += -ka * Ha
    J[j + 1, j] += ka * Ha
    return F, J


def integrar(g, ka, kb, Aa, Ab, sig, Q, tau, theta0=None, cfl=0.5):
    """Integra hacia atrás (en τ) con RK4 de paso adaptativo (estable: dt ≤ 0.5/radio del jacobiano)."""
    th = np.zeros(2 * Q + 1) if theta0 is None else theta0.copy()
    t = 0.0
    f = lambda x: campo(x, g, ka, kb, Aa, Ab, sig, Q)[0]
    while t < tau:
        _, J = campo(th, g, ka, kb, Aa, Ab, sig, Q)
        dt = min(cfl / np.abs(J).sum(1).max(), tau - t)
        k1 = f(th); k2 = f(th + 0.5 * dt * k1); k3 = f(th + 0.5 * dt * k2); k4 = f(th + dt * k3)
        th = th + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        t += dt
    return th


def estacionario(g, ka, kb, Aa, Ab, sig, Q, tol=1e-9, max_it=300, theta0=None):
    """Solución estacionaria (ergódica): θ(τ,q) ≈ c τ + θ∞(q). Devuelve (θ∞ con θ(0)=0, c, iteraciones).

    Euler implícito linealizado con paso creciente (la matriz I − dt·J es M-matriz: diagonal dominante, fuera de
    la diagonal ≥ 0 ⇒ estable para todo dt), seguido de Newton sobre F(θ) = c·1, θ(0) = 0.
    """
    n = 2 * Q + 1
    th = np.zeros(n) if theta0 is None else theta0 - theta0[Q]
    _, J0 = campo(th, g, ka, kb, Aa, Ab, sig, Q)
    r0 = np.abs(J0).sum(1).max()
    dt = 0.1 / r0
    for it in range(max_it):
        F, J = campo(th, g, ka, kb, Aa, Ab, sig, Q)
        esc = max(np.abs(F).max(), 1e-300)
        if (F.max() - F.min()) < tol * esc + 1e-14 * r0:
            break
        th = th + np.linalg.solve(np.eye(n) - dt * J, dt * F)
        th -= th[Q]
        dt = min(dt * 1.7, 1e9 / r0)
    # Newton ergódico: incógnitas θ(q≠0) y c
    idx = [i for i in range(n) if i != Q]
    for _ in range(4):
        F, J = campo(th, g, ka, kb, Aa, Ab, sig, Q)
        c = F.mean()
        R = F - c
        if np.abs(R).max() < 1e-13 * max(np.abs(F).max(), 1e-300):
            break
        A_ = np.hstack([J[:, idx], -np.ones((n, 1))])
        d = np.linalg.solve(A_, -R)
        th2 = th.copy()
        th2[idx] += d[:-1]
        F2 = campo(th2, g, ka, kb, Aa, Ab, sig, Q)[0]
        if (F2.max() - F2.min()) <= (F.max() - F.min()):
            th = th2
        else:
            break
    F = campo(th, g, ka, kb, Aa, Ab, sig, Q)[0]
    return th, float(F.mean()), it, float(F.max() - F.min())


def politica(theta, g, ka, kb):
    """(δ_a*, δ_b*) por inventario q = -Q..Q (NaN donde no se cotiza: ask en q=-Q, bid en q=Q)."""
    n = len(theta)
    Da, Db = np.full(n, np.nan), np.full(n, np.nan)
    Db[:-1] = base(g, kb) + theta[:-1] - theta[1:]
    Da[1:] = base(g, ka) + theta[1:] - theta[:-1]
    return Da, Db


def glft(q, g, ka, kb, Aa, Ab, sig):
    """Aproximación cerrada de v41 (q puede ser arreglo). Devuelve (δ_a, δ_b)."""
    wa = np.sqrt(sig ** 2 * g / (2 * ka * Aa) * (1 + g / ka) ** (1 + ka / g))
    wb = np.sqrt(sig ** 2 * g / (2 * kb * Ab) * (1 + g / kb) ** (1 + kb / g))
    return base(g, ka) - (q - 0.5) * wa, base(g, kb) + (q + 0.5) * wb


def guent_lineal(g, k, A, sig, Q):
    """Caso simétrico (k_a=k_b=k, A_a=A_b=A): w = e^{kθ} cumple ∂_τ w = M w con M tridiagonal (Guéant 2017).

    Devuelve (M, w∞ vector propio principal normalizado, θ∞ = ln w∞ / k)."""
    q = np.arange(-Q, Q + 1, dtype=float)
    eta = k * A * cte(g, k)
    M = np.diag(-0.5 * k * g * sig ** 2 * q ** 2) + eta * (np.eye(2 * Q + 1, k=1) + np.eye(2 * Q + 1, k=-1))
    val, vec = np.linalg.eigh(M)
    w = np.abs(vec[:, -1])
    return M, w, np.log(w) / k


# ----------------------------------------------------------------- tabla de búsqueda
class Tabla:
    """Política estacionaria precalculada sobre una rejilla log de parámetros adimensionales.

    Invariancia: (σ², A_a, A_b) → s·(σ², A_a, A_b) no cambia θ∞ (solo c). Ejes: u = ln(σ²/A_a), v = ln(A_b/A_a)
    y, si k varía por bin, ln k_a, ln k_b. Se almacenan p_b(q), p_a(q) (bps); la interpolación es multilineal en
    el espacio de los ejes (log) y se recorta a la rejilla (se cuenta la fracción recortada)."""

    def __init__(self, g, Q, ejes, ka=None, kb=None):
        self.g, self.Q, self.ejes, self.ka, self.kb = g, Q, [np.asarray(e, float) for e in ejes], ka, kb
        self.d = len(ejes)
        self.forma = tuple(len(e) for e in self.ejes)
        self.datos = np.zeros(self.forma + (4 * Q,))

    def params(self, nodo):
        u, v = nodo[0], nodo[1]
        ka, kb = (self.ka, self.kb) if self.d == 2 else (math.exp(nodo[2]), math.exp(nodo[3]))
        return ka, kb, 1.0, math.exp(v), math.exp(0.5 * u)

    def construir(self):
        Q = self.Q
        for ix in itertools.product(*[range(n) for n in self.forma]):
            nodo = [self.ejes[a][i] for a, i in enumerate(ix)]
            ka, kb, Aa, Ab, sg = self.params(nodo)
            th = estacionario(self.g, ka, kb, Aa, Ab, sg, Q)[0]
            self.datos[ix] = np.concatenate([th[:-1] - th[1:], th[1:] - th[:-1]])
        return self

    def interpolar(self, X):
        """X: (n, d) coordenadas -> (n, 4Q) valores [p_b | p_a]; recorta y devuelve la fracción recortada."""
        X = np.asarray(X, float)
        i0, fr, rec = [], [], np.zeros(len(X), bool)
        for a, e in enumerate(self.ejes):
            x = X[:, a]
            rec |= (x < e[0]) | (x > e[-1])
            pos = (np.clip(x, e[0], e[-1]) - e[0]) / (e[1] - e[0])
            j = np.clip(np.floor(pos).astype(int), 0, len(e) - 2)
            i0.append(j)
            fr.append(pos - j)
        out = np.zeros((len(X), self.datos.shape[-1]))
        for corner in itertools.product((0, 1), repeat=self.d):
            w = np.ones(len(X))
            idx = []
            for a, c in enumerate(corner):
                w = w * (fr[a] if c else 1 - fr[a])
                idx.append(i0[a] + c)
            out += w[:, None] * self.datos[tuple(idx)]
        return out, float(rec.mean())

    def deltas(self, X, ka, kb):
        """(Da, Db) de forma (n, 2Q+1) con NaN en los bordes; ka, kb escalares o (n,) en bps."""
        p, rec = self.interpolar(X)
        Q = self.Q
        n = len(p)
        Da, Db = np.full((n, 2 * Q + 1), np.nan), np.full((n, 2 * Q + 1), np.nan)
        Db[:, :-1] = np.reshape(base(self.g, kb), (-1, 1)) + p[:, :2 * Q]
        Da[:, 1:] = np.reshape(base(self.g, ka), (-1, 1)) + p[:, 2 * Q:]
        return Da, Db, rec
