"""E1 (AS) y E2 (Hawkes bivariado) para Colab, con las mejoras aplicables de v90–v98.

Respuesta y métrica idénticas a E3 (v98): y[b, δ] = agresores que cruzan mid·(1 ± δ) en el bin de 1 s; ll = Σ_δ [y·L − e^L]
(sin log y!), L = log λ por bin. Partición idéntica: ajuste 29 jun–31 jul, evaluación 1 ago–3 sep.

Modelos:  log λ_i(b, δ) = log Λ_i(b) + nivel_i(hora) + forma_i(δ)
  Λ = 1 (E1) o Λ predictiva del Hawkes (E2, 1 o 2 escalas). nivel: constante o por hora UTC (+h). forma: −kδ o f(δ) monótona (MLE cerrado f_j = log N_j/N_1).
E2 (código de v46 portado sin cambios en estados/EM/predicción de 1 escala; 2 escalas = misma EM con 4 estados).
"""
import math
from datetime import date, datetime, timezone

import numpy as np
from scipy.linalg import expm

LADOS = {"ask": 0, "bid": 1}


# ------------------------------------------------------------------ datos
def medianoche_us(d):
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp()) * 1_000_000


def cargar(carpeta, d):
    z = np.load(f"{carpeta}/dias/{d}.npz")
    return {"fecha": d, "t_ms": z["t_ms"], "hora": z["hora"].astype(int), "deltas": z["deltas"],
            "y": {"ask": z["c_ask"].astype(float), "bid": z["c_bid"].astype(float)}, "T_us": z["T_us"], "tipo": z["tipo"]}


# ------------------------------------------------------------------ nivel y forma (comunes a E1 y E2)
def _aurea(f, a, b, n=80):
    g = (math.sqrt(5) - 1) / 2; c, d = b - g * (b - a), a + g * (b - a); fc, fd = f(c), f(d)
    for _ in range(n):
        if fc >= fd:
            b, d, fd = d, c, fc; c = b - g * (b - a); fc = f(c)
        else:
            a, c, fc = c, d, fd; d = a + g * (b - a); fd = f(d)
    return 0.5 * (a + b)


def ajustar_nivel_forma(Lam, y, hora, deltas, forma="k", usar_h=False):
    """MLE de log E[y_bδ] = log Λ_b + nivel(hora_b) + forma(δ). Solo depende de agregados."""
    N = y.sum(0); Y = N.sum()
    if forma == "k":
        snd = float((N * deltas).sum())
        k = _aurea(lambda k: -k * snd - Y * math.log(np.exp(-k * deltas).sum()), 0.0, 5.0)
        sh = -k * (deltas - deltas[0])
    else:
        k = None; sh = np.minimum.accumulate(np.log(np.maximum(N, 0.5) / N[0]))
    S = np.exp(sh).sum()
    if usar_h:
        num = np.bincount(hora, weights=y.sum(1), minlength=24); den = np.bincount(hora, weights=Lam, minlength=24) * S
        niv = np.where(den > 0, np.log(np.maximum(num, 0.5) / np.where(den > 0, den, 1)), 0.0)
    else:
        niv = np.full(24, math.log(Y / (Lam.sum() * S)))
    return {"forma": forma, "k": k, "sh": sh, "niv": niv, "usar_h": usar_h}


def log_lam(p, Lam, hora):
    return (np.log(Lam) + p["niv"][hora])[:, None] + p["sh"][None, :]


def ll(y, L):
    return float((y * L - np.exp(L)).sum())


# ------------------------------------------------------------------ Hawkes: estados (v46)
def estados(t, tipos, beta, inicio, fin):
    n = len(t); t = np.asarray(t, float); dec = np.exp(-beta * np.diff(t, prepend=inicio)).tolist(); tp = np.asarray(tipos).tolist()
    sp0, sp1, sa0, sa1 = [0.0] * n, [0.0] * n, [0.0] * n, [0.0] * n; s0 = s1 = b0 = b1 = 0.0
    for k in range(n):
        d = dec[k]
        if d != 1.0:
            s0 *= d; s1 *= d; b0, b1 = s0, s1
        sp0[k], sp1[k] = b0, b1
        if tp[k] == 0:
            s0 += beta
        else:
            s1 += beta
        sa0[k], sa1[k] = s0, s1
    w = 1.0 - np.exp(-beta * (fin - t)); g = np.array([w[np.asarray(tipos) == j].sum() for j in (0, 1)])
    return np.column_stack([sp0, sp1]), np.column_stack([sa0, sa1]), g


def intervalos(dias):
    out = []
    for b in dias:
        ts = (b["T_us"] - medianoche_us(b["fecha"])) / 1e6
        out.append({"t": ts, "tipos": b["tipo"], "inicio_s": float(ts[0]), "fin_s": float(ts[-1])})
    return out


def _agrupar(ivs, betas, cache):
    """Estados previos por tipo con columnas [(j, m)] = j + 2m; g y T."""
    S_t, g, T = [[], []], np.zeros(2 * len(betas)), 0.0
    for n_iv, iv in enumerate(ivs):
        cols, gs = [], []
        for b in betas:
            key = (n_iv, round(b, 10))
            if key not in cache:
                sp, _, gi = estados(iv["t"], iv["tipos"], b, iv["inicio_s"], iv["fin_s"]); cache[key] = (sp, gi)
            sp, gi = cache[key]; cols.append(sp); gs.append(gi)
        sp = np.hstack(cols); tp = np.asarray(iv["tipos"])
        for i in (0, 1):
            S_t[i].append(sp[tp == i])
        g += np.concatenate(gs); T += iv["fin_s"] - iv["inicio_s"]
    return [np.ascontiguousarray(np.vstack(s)) for s in S_t], g, T


def _em(S_t, g, T, mu, A, max_iter, tol):
    """EM monótono (v46) generalizado a K estados por tipo: λ_i = μ_i + S_t[i] @ A[i]."""
    prev, conv = -math.inf, False
    for _ in range(max_iter):
        val = -mu.sum() * T - (A * g[None, :]).sum(); mu_n, A_n = np.empty(2), np.empty_like(A)
        for i in (0, 1):
            lam = np.maximum(mu[i] + S_t[i] @ A[i], 1e-300); inv = 1.0 / lam; val += float(np.log(lam).sum())
            mu_n[i] = mu[i] * inv.sum() / T; A_n[i] = np.where(g > 0, A[i] * (inv @ S_t[i]) / np.where(g > 0, g, 1.0), 0.0)
        mu, A = np.maximum(mu_n, 1e-12), A_n
        if abs(val - prev) <= tol:
            conv = True; break
        prev = val
    val = -mu.sum() * T - (A * g[None, :]).sum()
    for i in (0, 1):
        val += float(np.log(np.maximum(mu[i] + S_t[i] @ A[i], 1e-300)).sum())
    return mu, A, val, conv


def ramificacion(A, nb):
    """Matriz de ramificación 2×2 = Σ_m α^m (A tiene columnas j + 2m)."""
    return sum(A[:, 2 * m:2 * m + 2] for m in range(nb))


def ajustar_hawkes(ivs, rejillas, iters=(150, 1e-3), final=(3000, 1e-6), log=print):
    """rejillas: lista de tuplas de β (1 o 2 escalas). Elige por ll en la rejilla y hace EM final largo."""
    cache, res = {}, {}
    n_ev = sum(len(iv["t"]) for iv in ivs); T_tot = sum(iv["fin_s"] - iv["inicio_s"] for iv in ivs)
    for betas in rejillas:
        S_t, g, T = _agrupar(ivs, betas, cache); K = 2 * len(betas)
        A0 = np.tile(np.array([[0.2, 0.05], [0.05, 0.2]]) / len(betas), (1, len(betas)))
        mu, A, val, conv = _em(S_t, g, T, np.full(2, n_ev / (4 * T_tot)), A0, *iters)
        res[betas] = (mu, A, val); log(f"  β={betas} ll={val:.1f} ρ={max(abs(np.linalg.eigvals(ramificacion(A, len(betas))))):.3f}")
    best = max(res, key=lambda b: res[b][2]); S_t, g, T = _agrupar(ivs, best, cache)
    mu, A, val, conv = _em(S_t, g, T, res[best][0], np.maximum(res[best][1], 1e-6), *final)
    rho = float(max(abs(np.linalg.eigvals(ramificacion(A, len(best))))))
    log(f"  elegido β={best} ll={val:.1f} conv={conv} ρ={rho:.3f}")
    return {"mu": mu, "A": A, "betas": np.array(best, float), "ll": val, "convergido": conv, "rho": rho}


def lambda_predictiva(mod, x0, h=1.0):
    """Λ_i = ∫_0^h E[λ_i(t+u) | F_t] du. Estado x (n, 2·nβ) con columnas j + 2m.
    dE[x]/du = D(−I + P A) E[x] + D P μ, D = diag(β_m por columna), P mapea λ_j a sus columnas (j, m)."""
    mu, A, be = mod["mu"], mod["A"], mod["betas"]; nb = len(be); K = 2 * nb
    if max(abs(np.linalg.eigvals(ramificacion(A, nb)))) >= 1:
        raise ValueError("no estacionario")
    P = np.zeros((K, 2))
    for m in range(nb):
        P[2 * m, 0] = P[2 * m + 1, 1] = 1.0
    D = np.diag(np.repeat(be, 2)); M = D @ (-np.eye(K) + P @ A); b = D @ P @ mu
    m_inf = -np.linalg.solve(M, b); I1 = np.linalg.solve(M, expm(M * h) - np.eye(K))
    integral = h * m_inf[None, :] + (np.asarray(x0, float) - m_inf) @ I1.T
    return mu[None, :] * h + integral @ A.T


def lambda_bins(mod, b):
    """Λ por bin (n, 2): historia = eventos del mismo día con t < inicio del bin (como v46)."""
    m0 = medianoche_us(b["fecha"]); rel = b["T_us"] - m0; ts = rel / 1e6; q = np.asarray(b["t_ms"], np.int64) * 1000 - m0
    idx = np.searchsorted(rel, q, side="left") - 1; ok = idx >= 0; x0 = np.zeros((len(q), 2 * len(mod["betas"])))
    for m, be in enumerate(mod["betas"]):
        _, sa, _ = estados(ts, b["tipo"], be, float(ts[0]), float(ts[-1]))
        dt = q[ok] / 1e6 - ts[idx[ok]]; x0[ok, 2 * m:2 * m + 2] = sa[idx[ok]] * np.exp(-be * dt)[:, None]
    return lambda_predictiva(mod, x0)
