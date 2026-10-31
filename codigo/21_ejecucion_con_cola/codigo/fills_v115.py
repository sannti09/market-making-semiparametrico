#!/usr/bin/env python3
"""v115 (exploratorio, posterior a los resultados): anatomía de las ejecuciones de la HJB exacta con R0 y R1 para E3 tesis, E3 base y E1.
Separa las ejecuciones por cruce (alguna transacción más allá del precio) de las que solo tocan el precio, y mide la captura frente al mid
de la decisión y el markout a 1, 10 y 60 s. Reutiliza cola_v115 sin editarlo. Uso: python fills_v115.py test|sim"""
import json, sys, time
from datetime import date
import numpy as np
import cola_v115 as C  # noqa: E402  (verifica el plan v115 y sustituye la ejecución de econ_v110)
E, T, Q, UNIDAD = C.E, C.T, C.Q, C.UNIDAD
E.log = lambda m, f=None: print(m, flush=True)   # no sobrescribir los logs de la corrida v115
MODS = ("E3-fkX+B", "E3", "E1"); CAP, FILLS = {}, {(m, rg): [] for m in MODS for rg in ("R0", "R1")}

_pol = E.pol_exacta
def pol_exacta(m, L, sg):
    Da, Db, info = _pol(m, L, sg)
    if m in MODS: CAP[id(Da)] = m
    return Da, Db, info
E.pol_exacta = pol_exacta

def fills(Da, Db, QA, QB, ctx, regla):
    """Misma dinámica que cola_v115.simular_regla (R0 o R1), registrando cada ejecución."""
    m0, ok, ts, mid = ctx["m0"], ctx["ok"], ctx["ts"], ctx["mid"]; bbt, bat = ctx["bbt"], ctx["bat"]
    ea, eb = C.DIA["ask"]["ext"], C.DIA["bid"]["ext"]
    cand = np.nonzero(ok & (((ea > QA.min(1)) | (eb < QB.max(1))) if regla == "R0" else ((ea >= QA.min(1)) | (eb <= QB.max(1)))))[0].tolist()
    q, out = 0, []
    for i in cand:
        precios = {"ask": QA[i, q + Q], "bid": QB[i, q + Q]}   # como simular: ambos precios con el inventario al inicio del segundo
        for lado, s in (("ask", 1), ("bid", -1)):
            p = precios[lado]; t = C.ejecuta(lado, i, p, regla, {"at": 0, "vis": 0, "at_ok": 0})
            if t is None: continue
            X = C.DIA[lado]; a, b = X["ini"][i], X["fin"][i]; tl, pl = X["tl"][a:b], X["pl"][a:b]
            cruce = bool((s * (pl[tl <= t] - p) > 0).any())
            toque = p == (bat[i] if lado == "ask" else bbt[i])
            k = (t - ts[0]) // 100; mh = [mid[min(k + 10 * H, len(mid) - 1)] if k + 10 * H < len(mid) else np.nan for H in (1, 10, 60)]
            out.append((s, cruce, toque, s * (p / 100 - m0[i]) / m0[i] * 1e4, *(s * (p / 100 - x) / (p / 100) * 1e4 for x in mh)))
            q += -s
    return out

_sim = E.simular
def simular(Da, Db, QA, QB, ctx):
    r = _sim(Da, Db, QA, QB, ctx); m = CAP.get(id(Da))
    if m is not None:
        for rg in ("R0", "R1"): FILLS[(m, rg)] += fills(Da, Db, QA, QB, ctx, rg)
    return r
E.simular = simular

def resumir(F):
    A = np.array(F, float).reshape(-1, 7); res = {}   # s, cruce, toque, captura, markout 1/10/60 s
    for nom, sel in (("todas", np.ones(len(A), bool)), ("por_cruce", A[:, 1] == 1), ("solo_toque", A[:, 1] == 0)):
        X = A[sel]; n = len(X)
        res[nom] = {"n": n, "frac": n / max(len(A), 1), "frac_en_mejor_precio": float(X[:, 2].mean()) if n else None,
                    "captura_vs_mid_decision_bps": float(np.nanmean(X[:, 3])) if n else None,
                    **{f"markout_{H}s_bps": (float(np.nanmean(X[:, 4 + j])) if n else None) for j, H in enumerate((1, 10, 60))},
                    **{f"movimiento_{H}s_bps": (float(np.nanmean(X[:, 4 + j] - X[:, 3])) if n else None) for j, H in enumerate((1, 10, 60))}}
    return res

if __name__ == "__main__":
    per = C.PERIODO; assert per in ("test", "sim")
    if per == "test": fechas = T.fechas("2026-09-04", "2026-09-20")
    else:
        T.T0, T.T1, T.guardia_test = date(2026, 9, 21), date(2026, 10, 26), C.S11.guarda_sim; fechas = T.fechas("2026-09-21", "2026-10-26")
    t0 = time.time()
    for d in fechas:
        CAP.clear(); E.dia(d)
        for k in E.PRED: E.PRED[k].clear()
        print(d, f"{time.time() - t0:.0f} s", {f"{m}|{rg}": len(v) for (m, rg), v in FILLS.items()}, flush=True)
    out = {f"{m}|{rg}": resumir(v) for (m, rg), v in FILLS.items()}
    np.savez_compressed(C.SAL / f"fills_v115_{per}.npz", **{f"{m}|{rg}": np.array(v, np.float32).reshape(-1, 7) for (m, rg), v in FILLS.items()})
    (C.SAL / f"fills_v115_{per}.json").write_text(json.dumps(out, indent=1)); print(json.dumps(out, indent=1))
