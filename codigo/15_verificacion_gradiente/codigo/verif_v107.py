#!/usr/bin/env python3
"""v107: verificación del gradiente y de la convergencia de la curva f(δ)·m(X) de E3 en los modelos finales v103 (solo entrenamiento). Ver PLAN_V107.md."""
import hashlib, json, pickle, sys, time
from pathlib import Path
import numpy as np
from scipy.optimize import minimize, approx_fprime
R = Path(__file__).resolve().parents[1]; RR = R.parent; SAL = R / "salida"
assert hashlib.sha256((R / "PLAN_V107.md").read_bytes()).hexdigest() == (R / "PLAN_V107.sha256").read_text().split()[0]
sys.path.insert(0, str(RR / "09_protocolo_test" / "codigo"))
import test_v101 as T  # noqa: E402  (dia_aj solo lee ≤ 3 sep)
from modelo_f import f_de_theta, theta_de_f  # noqa: E402
P = pickle.load(open(RR / "11_modelos_finales" / "modelos" / "modelos_finales_v103.pkl", "rb")); MOD, deltas, cols = P["MOD"], P["deltas"], P["cols"]
V = T.V; LOG = []
def log(m):
    LOG.append(f"[{time.strftime('%H:%M:%S')}] {m}"); print(LOG[-1], flush=True); (SAL / "verif_v107.log").write_text("\n".join(LOG))

def objetivo(x, eta, Z, y, e, recorte_en_gradiente):
    p = Z.shape[1]; a, th, b = x[0], x[1:-p], x[-p:]; f = f_de_theta(th, deltas); zb = Z @ b
    m = np.exp(np.clip(zb, -5, 5)); mf = m[:, None] * f[None, :]; lam = np.exp(eta[:, None] + a + mf) * e[:, None]; r = y - lam
    ll = float((y * (eta[:, None] + a + mf)).sum() - lam.sum())
    Gf = (m[:, None] * r).sum(0); gth = -np.exp(th) * np.diff(deltas) * np.cumsum(Gf[::-1])[::-1][1:]
    dm = m * (r * f[None, :]).sum(1)
    if recorte_en_gradiente: dm = np.where(np.abs(zb) < 5, dm, 0.0)       # derivada de clip: 0 fuera de [−5, 5]
    return -ll, -np.concatenate([[r.sum()], gth, Z.T @ dm])

if __name__ == "__main__":
    t0 = time.time(); aj = [T.dia_aj(d) for d in T.fechas("2026-06-29", "2026-09-03")]
    hora = np.concatenate([b["hora_utc"] for b in aj]).astype(int); e = np.concatenate([b["exposicion_s"] for b in aj])
    X49 = np.vstack([b["X49"] for b in aj]); log(f"entrenamiento cargado: {len(hora)} segundos ({time.time() - t0:.0f} s)")
    res, ok_global = {}, True
    for nom in ("E3-fkX+B", "E3-fkX"):
        X = X49 if nom == "E3-fkX+B" else np.ascontiguousarray(X49[:, :44])
        for lado in ("ask", "bid"):
            mo = MOD[nom][lado]; y = np.vstack([b["conteos"][lado] for b in aj]).astype(float)
            Z = V.est(V.covariables(X49[:, :44], cols, lado), MOD["mu"][lado], MOD["sd"][lado]); eta = mo.eta(X, hora)
            x0 = np.concatenate([[0.0], theta_de_f(mo.f, deltas), mo.b]); n = len(y)
            f0 = objetivo(x0, eta, Z, y, e, False)[0]
            rA = minimize(objetivo, x0, args=(eta, Z, y, e, False), jac=True, method="L-BFGS-B", options={"maxiter": 200})
            rB = minimize(objetivo, x0, args=(eta, Z, y, e, True), jac=True, method="L-BFGS-B", options={"maxiter": 2000})
            fB, bB = f_de_theta(rB.x[1:-4], deltas), rB.x[-4:]
            idx = np.random.default_rng(0).choice(n, 200_000, replace=False)
            ga = objetivo(x0, eta[idx], Z[idx], y[idx], e[idx], True)[1]
            gn = approx_fprime(x0, lambda x: objetivo(x, eta[idx], Z[idx], y[idx], e[idx], True)[0], 1e-6)
            r = {"recorte_activo_frac": float((np.abs(Z @ mo.b) >= 5).mean()), "max_abs_zb": float(np.abs(Z @ mo.b).max()),
                 "A_success": bool(rA.success), "A_nit": int(rA.nit), "A_msg": str(rA.message), "A_grad_inicial_norma": float(np.abs(objetivo(x0, eta, Z, y, e, False)[1]).max()),
                 "B_success": bool(rB.success), "B_nit": int(rB.nit), "B_msg": str(rB.message), "B_ganancia_ll_por_segundo": float((f0 - rB.fun) / n),
                 "B_max_dif_f": float(np.abs(fB - mo.f).max()), "B_max_dif_b": float(np.abs(bB - mo.b).max()), "B_a": float(rB.x[0]),
                 "C_grad_rel_err_max": float(np.abs(ga - gn).max() / max(np.abs(gn).max(), 1e-12))}
            r["cumple"] = bool(r["B_ganancia_ll_por_segundo"] < 1e-4 and r["B_max_dif_f"] < 0.01 and r["B_max_dif_b"] < 0.005)
            ok_global &= r["cumple"]; res[f"{nom}|{lado}"] = r; log(f"{nom} {lado}: {json.dumps(r)}"); del y
    res["veredicto"] = "modelos v103 verificados: no se reentrena" if ok_global else "la curva cambia: informar antes de reentrenar"
    (SAL / "resultado_v107.json").write_text(json.dumps(res, indent=1)); log(res["veredicto"])
