#!/usr/bin/env python3
"""v107, detalle: dónde cambia f(δ) al reoptimizar con el gradiente corregido (mismo cálculo que verif_v107, guarda las curvas)."""
import json, sys
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
sys.path.insert(0, str(Path(__file__).resolve().parent))
import verif_v107 as W  # noqa: E402
T, V, MOD, deltas, cols = W.T, W.V, W.MOD, W.deltas, W.cols
aj = [T.dia_aj(d) for d in T.fechas("2026-06-29", "2026-09-03")]
hora = np.concatenate([b["hora_utc"] for b in aj]).astype(int); e = np.concatenate([b["exposicion_s"] for b in aj]); X49 = np.vstack([b["X49"] for b in aj])
out = {}
for nom in ("E3-fkX+B", "E3-fkX"):
    X = X49 if nom == "E3-fkX+B" else np.ascontiguousarray(X49[:, :44])
    for lado in ("ask", "bid"):
        mo = MOD[nom][lado]; y = np.vstack([b["conteos"][lado] for b in aj]).astype(float)
        Z = V.est(V.covariables(X49[:, :44], cols, lado), MOD["mu"][lado], MOD["sd"][lado]); eta = mo.eta(X, hora)
        x0 = np.concatenate([[0.0], W.theta_de_f(mo.f, deltas), mo.b])
        rA = minimize(W.objetivo, x0, args=(eta, Z, y, e, False), jac=True, method="L-BFGS-B", options={"maxiter": 200})
        rB = minimize(W.objetivo, x0, args=(eta, Z, y, e, True), jac=True, method="L-BFGS-B", options={"maxiter": 2000})
        fB = W.f_de_theta(rB.x[1:-4], deltas)
        out[f"{nom}|{lado}"] = {"N_por_delta": y.sum(0).tolist(), "f_v103": mo.f.tolist(), "f_reopt": fB.tolist(), "A_msg": str(rA.message), "b_v103": mo.b.tolist(), "b_reopt": rB.x[-4:].tolist()}
        print(nom, lado, "Δf por δ:", np.round(fB - mo.f, 3).tolist(), "| N:", [int(v) for v in y.sum(0)], "| A:", rA.message, flush=True)
(Path(__file__).resolve().parents[1] / "salida" / "detalle_v107.json").write_text(json.dumps(out, indent=1))
