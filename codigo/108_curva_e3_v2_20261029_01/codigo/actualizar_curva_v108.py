#!/usr/bin/env python3
"""v108: modelos finales v108 = v103 con la curva de E3 tesis y E3-fkX reoptimizada con modelo_f_v2 (ver PLAN_V108.md)."""
import copy, hashlib, json, pickle, sys, time
from pathlib import Path
import numpy as np
R = Path(__file__).resolve().parents[1]; RR = R.parent
assert hashlib.sha256((R / "PLAN_V108.md").read_bytes()).hexdigest() == (R / "PLAN_V108.sha256").read_text().split()[0]
sys.path.insert(0, str(RR / "101_test_p1_20261029_01" / "codigo")); sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_v101 as T  # noqa: E402
from modelo_f_v2 import paso_curva, ModeloFKXv2  # noqa: E402
from modelo_f import ll_f_filas  # noqa: E402
p103 = RR / "103_modelos_finales_20261029_01" / "modelos" / "modelos_finales_v103.pkl"
P = pickle.load(open(p103, "rb")); MOD, deltas, cols = P["MOD"], P["deltas"], P["cols"]; V = T.V
t0 = time.time(); aj = [T.dia_aj(d) for d in T.fechas("2026-06-29", "2026-09-03")]
hora = np.concatenate([b["hora_utc"] for b in aj]).astype(int); e = np.concatenate([b["exposicion_s"] for b in aj]); X49 = np.vstack([b["X49"] for b in aj])
NUEVO = copy.deepcopy(MOD); res = {}
for nom in ("E3-fkX+B", "E3-fkX"):
    X = X49 if nom == "E3-fkX+B" else np.ascontiguousarray(X49[:, :44])
    for lado in ("ask", "bid"):
        mo = MOD[nom][lado]; y = np.vstack([b["conteos"][lado] for b in aj]).astype(float)
        Z = V.est(V.covariables(X49[:, :44], cols, lado), MOD["mu"][lado], MOD["sd"][lado]); eta = mo.eta(X, hora)
        a, f, b, opt = paso_curva(eta, Z, y, e, deltas, mo.f, mo.b)
        if not opt.success:
            raise SystemExit(f"{nom} {lado}: no converge ({opt.message}); se detiene según el plan")
        nm = ModeloFKXv2.__new__(ModeloFKXv2); nm.__dict__.update(copy.deepcopy(mo.__dict__)); nm.f, nm.b, nm.c0 = f, b, mo.c0 + a
        nm.optimizador = {"success": True, "nit": int(opt.nit), "mensaje": str(opt.message)}
        ll_old = float(ll_f_filas(eta, mo._m(Z)[:, None] * mo.f[None, :], y, e).sum()); ll_new = float(ll_f_filas(nm.eta(X, hora), nm._m(Z)[:, None] * f[None, :], y, e).sum())
        NUEVO[nom][lado] = nm
        res[f"{nom}|{lado}"] = {"nit": int(opt.nit), "mensaje": str(opt.message), "ganancia_ll_por_segundo": (ll_new - ll_old) / len(y),
                               "f_v103": [round(v, 4) for v in mo.f], "f_v108": [round(v, 4) for v in f], "b_v103": [round(v, 5) for v in mo.b], "b_v108": [round(v, 5) for v in b],
                               "recorte_activo_segundos": int((np.abs(Z @ b) >= 5).sum()), "max_abs_zb": float(np.abs(Z @ b).max())}
        print(nom, lado, json.dumps(res[f"{nom}|{lado}"]), flush=True); del y
p = R / "modelos" / "modelos_finales_v108.pkl"; pickle.dump({"MOD": NUEVO, "deltas": deltas, "cols": cols, "modelos": P["modelos"], "base": "v103 + curva v108"}, open(p, "wb"))
man = {"hora": time.strftime("%Y-%m-%d %H:%M:%S %z"), "base": "modelos_finales_v103.pkl (sha " + hashlib.sha256(p103.read_bytes()).hexdigest()[:16] + ")",
       "cambio": "curva f(δ) y b de E3-fkX+B y E3-fkX reoptimizadas con modelo_f_v2 (gradiente con recorte, convergencia comprobada)",
       "pkl_sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "segundos": round(time.time() - t0), "resultados": res}
(R / "modelos" / "MANIFIESTO_v108.json").write_text(json.dumps(man, indent=1)); print("GUARDADO", man["pkl_sha256"][:16], flush=True)
