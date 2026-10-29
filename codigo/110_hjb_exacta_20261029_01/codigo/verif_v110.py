#!/usr/bin/env python3
"""v110: verificaciones (a)-(d) SOLO con entrenamiento (3 sep y días de rango de m). Plan: PLAN_V110.md + ENMIENDA_V110B.md."""
import hashlib, json, pickle, sys, time
import numpy as np
import datos_v110 as D
import hjb_general as HG
from datos_v110 import MOD, MODELOS, FKX, deltas, G, Q, log, SAL

DJ = np.nonzero(np.isin(deltas, [0.5, 1.0, 2.0, 3.0, 5.0]))[0]
def exp_local(L):
    x = deltas[DJ]; xc = x - x.mean(); y = L[:, DJ]; s = (y - y.mean(1, keepdims=True)) @ xc / (xc @ xc)
    return y.mean(1) - s * x.mean(), -s

def forma_seg(sh, i):
    if sh["tipo"] == "fija": return HG.forma(sh["g"], deltas)
    F = HG.forma_por_fila(sh["f"], sh["m"][[i]], deltas)
    return {"k": F["k"][0], "c": F["c"][0], "lo": F["lo"], "hi": F["hi"]}

def resolver_exacto(sh_a, sh_b, i, La0, Lb0, sg):
    Fa, Fb = forma_seg(sh_a, i), forma_seg(sh_b, i)
    th = HG.estacionario_general(G, Fa, Fb, float(np.exp(La0[i])), float(np.exp(Lb0[i])), float(sg[i]), Q)[0]
    p = HG.pol_desde_theta(th)[None, :]
    Da, Db = HG.deltas_desde_p(p, Fa, Fb, G)
    return Da[0], Db[0], p[0]

def estad(e):
    e = np.asarray(e); return {"p50": float(np.percentile(e, 50)), "p99": float(np.percentile(e, 99)), "max": float(e.max()), "n": int(e.size)}

if __name__ == "__main__":
    t_ini = time.time(); out = {"hora": time.strftime("%Y-%m-%d %H:%M:%S"), "plan_sha": D.R.joinpath("PLAN_V110.sha256").read_text().split()[0][:16]}
    # ---------- datos de entrenamiento
    d3 = D.dia_entrenamiento(); L, sg, ok = d3["L"], d3["sg"], d3["ok"]
    SH = {m: {l: D.forma_modelo(L, l, m) for l in ("ask", "bid")} for m in MODELOS}
    out["formas"] = {m: {l: ({"tipo": "fija", "dev_max_normalizada": SH[m][l]["dev_max"], "k_tramos": [round(float(x), 4) for x in -np.diff(SH[m][l]["g"]) / np.diff(deltas)]} if SH[m][l]["tipo"] == "fija" else
                          {"tipo": "m", "err_reproduccion_m_f": SH[m][l]["err_repr"], "m_min": float(SH[m][l]["m"][ok].min()), "m_p50": float(np.median(SH[m][l]["m"][ok])), "m_max": float(SH[m][l]["m"][ok].max()),
                           "k_tramos_m1": [round(float(x), 4) for x in -np.diff(SH[m][l]["f"]) / np.diff(deltas)]}) for l in ("ask", "bid")} for m in MODELOS}
    # tramos con k <= K_MIN y fracción de segundos afectados
    flag = {}
    for m in MODELOS:
        for l in ("ask", "bid"):
            sh = SH[m][l]
            if sh["tipo"] == "fija": F = HG.forma(sh["g"], deltas); flag[f"{m}|{l}"] = {"tramos_afectados": int(F["nflag"]), "frac_segundos": 1.0 if F["nflag"] else 0.0}
            else:
                F = HG.forma_por_fila(sh["f"], sh["m"], deltas); fl = F["nflag"][ok] > 0
                flag[f"{m}|{l}"] = {"tramos_afectados_max": int(F["nflag"][ok].max()), "frac_segundos": float(fl.mean())}
    out["k_min_aplicado"] = flag; log(f"formas: dev. máx. de forma fija = {max(SH[m][l]['dev_max'] for m in MODELOS for l in ('ask','bid') if SH[m][l]['tipo']=='fija'):.2e}; segundos con tramo corregido: {max(v['frac_segundos'] for v in flag.values()):.4f}")
    # ---------- rangos de m y k (varios días de entrenamiento)
    mm = {f"{m}|{l}": [] for m in FKX for l in ("ask", "bid")}; kk = {f"{m}|{l}": [] for m in FKX for l in ("ask", "bid")}
    for d in D.DIAS_RANGO:
        dd = d3 if d == D.DIAS_RANGO[-1] else D.dia_entrenamiento(d)
        for m in FKX:
            for l in ("ask", "bid"):
                mm[f"{m}|{l}"].append(D.forma_modelo(dd["L"], l, m)["m"][dd["ok"]]); kk[f"{m}|{l}"].append(exp_local(dd["L"][l][m])[1][dd["ok"]])
        log(f"rango de m: día {d} leído")
    RANGO_M, RANGO_K = {}, {}
    for key in mm:
        lo, hi = np.percentile(np.concatenate(mm[key]), [0.1, 99.9]); RANGO_M[key] = [max(lo * 0.9, 0.05), hi * 1.1]
        lo, hi = np.percentile(np.concatenate(kk[key]), [0.1, 99.9]); RANGO_K[key] = [max(lo * 0.9, 0.05), hi * 1.1]
    for m in FKX: RANGO_K[m] = [min(RANGO_K[f"{m}|ask"][0], RANGO_K[f"{m}|bid"][0]), max(RANGO_K[f"{m}|ask"][1], RANGO_K[f"{m}|bid"][1])]
    out["rango_m"] = RANGO_M; out["rango_k_aprox"] = {m: RANGO_K[m] for m in FKX}; out["dias_rango"] = [str(d) for d in D.DIAS_RANGO]
    json.dump({"m": RANGO_M, "k": {m: RANGO_K[m] for m in FKX}}, open(SAL / "rangos_v110.json", "w"))
    log(f"rangos m: {RANGO_M}")
    A0 = {m: {l: L[l][m][:, 0] for l in ("ask", "bid")} for m in MODELOS}
    rng = np.random.default_rng(20261029); cand = np.nonzero(ok)[0]
    # ---------- (a) exponencial exacta vs v49
    pa_max, casos = 0.0, []
    sets = [("E1", "ask", "bid"), ("E3", "ask", "bid")]
    params = []
    for m in ("E1", "E3"):
        ka = float(-SH[m]["ask"]["g"][-1] / (deltas[-1] - 0.5)); kb = float(-SH[m]["bid"]["g"][-1] / (deltas[-1] - 0.5))
        for i in rng.choice(cand, 3, replace=False): params.append((ka, kb, float(np.exp(A0[m]["ask"][i])), float(np.exp(A0[m]["bid"][i])), float(sg[i])))
    params += [(0.4, 0.9, 0.3, 0.1, 0.4), (0.62, 0.75, 0.05, 0.4, 2.0), (1.1, 0.5, 1.0, 1.0, 0.1), (0.3, 0.3, 0.2, 0.5, 3.0)]
    casos_dom = []
    for ka, kb, Aa, Ab, s in params:
        ga, gb = -ka * (deltas - 0.5), -kb * (deltas - 0.5)
        th49 = HG.H49.estacionario(G, ka, kb, Aa * np.exp(0.5 * ka), Ab * np.exp(0.5 * kb), s, Q)[0]   # A de v49 = intercepto en δ=0
        _lo, _hi = HG.LO_EXT, HG.HI_EXT
        HG.LO_EXT, HG.HI_EXT = -1e3, 1e4          # (a) prueba el algoritmo sin el dominio admisible de la Enmienda B
        th = HG.estacionario_general(G, HG.forma(ga, deltas), HG.forma(gb, deltas), Aa, Ab, s, Q)[0]
        HG.LO_EXT, HG.HI_EXT = _lo, _hi
        e = float(np.abs(HG.pol_desde_theta(th) - HG.pol_desde_theta(th49)).max()); pa_max = max(pa_max, e)
        thd = HG.estacionario_general(G, HG.forma(ga, deltas), HG.forma(gb, deltas), Aa, Ab, s, Q)[0]
        casos.append({"k": [ka, kb], "A": [Aa, Ab], "sig": s, "err": e, "err_con_dominio_-5_40": float(np.abs(HG.pol_desde_theta(thd) - HG.pol_desde_theta(th49)).max()),
                      "delta_max_v49": float(np.nanmax(HG.H49.politica(th49, G, ka, kb)))})
    out["a"] = {"max_abs_dif_theta": pa_max, "n_casos": len(casos), "ok": bool(pa_max < 1e-8), "casos": casos}; log(f"(a) máx |Δ| = {pa_max:.2e}")
    # ---------- (b) H por tramos vs fuerza bruta
    errs, worst = [], None
    for m in MODELOS:
        for l in ("ask", "bid"):
            sh = SH[m][l]
            if sh["tipo"] == "fija": formas = [HG.forma(sh["g"], deltas)]
            else:
                mv = sh["m"][ok]; formas = [forma_seg({"tipo": "m", "f": sh["f"], "m": np.array([x])}, 0) for x in (mv.min(), np.median(mv), mv.max())]
            for F in formas:
                for p in (-3.0, -1.0, 0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 15.0):
                    Hm = float(HG.Hgen(np.array(p), F["k"], F["c"], F["lo"], F["hi"], G)[0]); Hb, _ = HG.H_fuerza_bruta(p, F, G, extra=deltas)
                    e = abs(Hm - Hb) / abs(Hb); errs.append(e)
                    if worst is None or e > worst[0]: worst = (e, m, l, p)
    out["b"] = {"max_err_rel": float(max(errs)), "n": len(errs), "peor": [float(worst[0]), worst[1], worst[2], worst[3]], "ok": bool(max(errs) < 1e-6)}; log(f"(b) err rel máx = {max(errs):.2e} {worst}")
    # ---------- (c) monotonía
    mono, viol = {}, 0
    for m in MODELOS:
        nv = 0
        for i in rng.choice(cand, 20, replace=False):
            Da, Db, _ = resolver_exacto(SH[m]["ask"], SH[m]["bid"], i, A0[m]["ask"], A0[m]["bid"], sg)
            if np.any(np.diff(Db[:-1]) < -1e-9) or np.any(np.diff(Da[1:]) > 1e-9): nv += 1
        mono[m] = nv; viol += nv
    out["c"] = {"segundos_con_violacion_de_20_por_modelo": mono, "ok": viol == 0}; log(f"(c) violaciones: {mono}")
    # ---------- (d) tablas
    ejes2 = [np.linspace(-7.5, 4.5, 81), np.linspace(-5, 5, 41)]
    TAB, ID = {}, {}
    t_tab = time.time()
    for m in MODELOS:
        if m in FKX:
            ra, rb = RANGO_M[f"{m}|ask"], RANGO_M[f"{m}|bid"]
            ej = [np.linspace(-7.5, 4.5, 41), np.linspace(-5, 5, 21), np.linspace(ra[0], ra[1], 9), np.linspace(rb[0], rb[1], 9)]
            ID[m] = m; t = time.time(); TAB[m] = HG.TablaG(G, Q, ej, deltas, SH[m]["ask"]["f"], SH[m]["bid"]["f"]).construir(procesos=8); log(f"tabla 4D {m} ({time.time() - t:.0f} s)")
        else:
            key = "|".join(str(tuple(np.round(SH[m][l]["g"], 6))) for l in ("ask", "bid")); ID[m] = hashlib.md5(key.encode()).hexdigest()[:8]
            if ID[m] not in TAB:
                t = time.time(); TAB[ID[m]] = HG.TablaG(G, Q, ejes2, deltas, SH[m]["ask"]["g"], SH[m]["bid"]["g"]).construir(procesos=8); log(f"tabla 2D {m} id {ID[m]} ({time.time() - t:.0f} s)")
    pk = SAL / "tablas_v110.pkl"; pickle.dump({"tablas": TAB, "id": ID}, open(pk, "wb")); out["tablas_sha256"] = hashlib.sha256(pk.read_bytes()).hexdigest(); out["s_tablas"] = round(time.time() - t_tab)
    errd, okd = {}, True
    for m in MODELOS:
        idx = rng.choice(cand, 150, replace=False); sa, sb = SH[m]["ask"], SH[m]["bid"]
        X = [np.log(sg[idx] ** 2 / np.exp(A0[m]["ask"][idx])), np.log(np.exp(A0[m]["bid"][idx]) / np.exp(A0[m]["ask"][idx]))]
        if m in FKX:
            X += [sa["m"][idx], sb["m"][idx]]; Fa = HG.forma_por_fila(sa["f"], sa["m"][idx], deltas); Fb = HG.forma_por_fila(sb["f"], sb["m"][idx], deltas)
        else: Fa, Fb = HG.forma(sa["g"], deltas), HG.forma(sb["g"], deltas)
        Dat, Dbt, rec = TAB[ID[m]].deltas_exactos(np.column_stack(X), Fa, Fb)
        ea, eb = [], []
        for j, i in enumerate(idx):
            Da, Db, _ = resolver_exacto(sa, sb, i, A0[m]["ask"], A0[m]["bid"], sg); ea.append(np.abs(Dat[j] - Da)); eb.append(np.abs(Dbt[j] - Db))
        ea, eb = np.array(ea), np.array(eb); sl5 = slice(Q - 5, Q + 6)
        e5 = np.concatenate([ea[:, sl5].ravel(), eb[:, sl5].ravel()]); e10 = np.concatenate([ea.ravel(), eb.ravel()]); e5, e10 = e5[np.isfinite(e5)], e10[np.isfinite(e10)]
        errd[m] = {"q<=5": estad(e5), "q<=10": estad(e10), "frac_recortada": rec}
        okd &= errd[m]["q<=5"]["p99"] < 0.05 and errd[m]["q<=10"]["p99"] < 0.1
        log(f"(d) {m}: |q|<=5 p99 {errd[m]['q<=5']['p99']:.4f} max {errd[m]['q<=5']['max']:.4f}; |q|<=10 p99 {errd[m]['q<=10']['p99']:.4f} max {errd[m]['q<=10']['max']:.4f}; recorte {rec:.3f}")
    out["d"] = {"por_modelo": errd, "ok": bool(okd)}
    out["todas_ok"] = bool(out["a"]["ok"] and out["b"]["ok"] and out["c"]["ok"] and out["d"]["ok"]); out["segundos"] = round(time.time() - t_ini)
    (SAL / "verificacion_v110.json").write_text(json.dumps(out, indent=1)); log(f"VERIFICACIONES: a={out['a']['ok']} b={out['b']['ok']} c={out['c']['ok']} d={out['d']['ok']} ({out['segundos']} s)")
