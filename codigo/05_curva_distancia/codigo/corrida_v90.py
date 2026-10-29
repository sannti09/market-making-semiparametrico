#!/usr/bin/env python3
"""v90: E3 vs E3-kX vs E3-f (vs E3-fkX). Ajuste 29 jun–12 jul, inclusión 13–16 jul, evaluación 17 jul–3 sep (sin 22–25 ago: sin capa).
Plan: PLAN_V90.md (sha256 en PLAN_V90.sha256). Cargador: copia importada de v58 (capas v1/v2) con tope 3 sep."""
import hashlib, json, sys, time
from datetime import date
from pathlib import Path
import numpy as np

AQUI = Path(__file__).resolve().parent; R90 = AQUI.parent; RR = R90.parent
sys.path.insert(0, str(AQUI)); sys.path.insert(0, str(RR / "02_conteos_respuesta" / "01_codigo"))
sys.path.insert(0, str(RR / "06_modulacion_estado")); sys.path.insert(0, str(RR / "01_nucleo_e3" / "01_pipeline"))
import cargador_v58 as C  # noqa: E402
from metricas import auc  # noqa: E402
from convenciones import DISTANCIAS_BPS_DEF  # noqa: E402
from modelo_e3_semiparametrico import ModeloE3Semiparametrico  # noqa: E402
from modelo_kx import ModeloKX  # noqa: E402
from modelo_f import ModeloF, ModeloFKX, ll_f_filas  # noqa: E402

assert hashlib.sha256((R90 / "PLAN_V90.md").read_bytes()).hexdigest() == (R90 / "PLAN_V90.sha256").read_text().split()[0]
C.restringir(date(2026, 9, 3))
SAL = R90 / "salida"; CAC = SAL / "cache"; CAC.mkdir(parents=True, exist_ok=True)
PARAMS = dict(learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=2000, max_iter=300, l2_regularization=1.0)
USAR_H = {"ask": True, "bid": False}
REF_V45 = {"ask": -418255, "bid": -468377}
LOGS = []


def log(m):
    s = f"[{time.strftime('%H:%M:%S')}] {m}"; print(s, flush=True); LOGS.append(s)
    (SAL / "corrida_v90.log").write_text("\n".join(LOGS))


def bins(d):
    p = CAC / f"bins_{d}.npz"
    if p.exists():
        z = np.load(p, allow_pickle=True)
        return {k: z[k] for k in z.files} | {"conteos": {"ask": z["c_ask"], "bid": z["c_bid"]}, "columnas_x": list(z["cols"])}
    b = C.construir_bins_v58(d, DISTANCIAS_BPS_DEF)
    if b.get("faltante"):
        return None
    np.savez(p, X=b["X"], hora_utc=b["hora_utc"], exposicion_s=b["exposicion_s"], deltas_bps=b["deltas_bps"],
             c_ask=b["conteos"]["ask"], c_bid=b["conteos"]["bid"], cols=np.array(b["columnas_x"]))
    return bins(d)


def covariables(X, cols, lado):   # idéntico a v47
    ix = {c: i for i, c in enumerate(cols)}
    prof = "depth_ask_top5" if lado == "ask" else "depth_bid_top5"
    return np.column_stack([X[:, ix["realized_vol_10000ms"]], np.log1p(X[:, ix["past_n_buy_sum_5000ms"]] + X[:, ix["past_n_sell_sum_5000ms"]]),
                            np.log(np.maximum(X[:, ix[prof]], 1e-9)), X[:, ix["imbalance_top5"]]])


def est(Z, mu, sd):
    z = (Z - mu) / sd
    return np.where(np.isfinite(z), z, 0.0)


def log_lam(nombre, mod, X, Z, hora, deltas):
    if nombre == "E3":
        return mod.eta(X, hora)[:, None] - mod.k * deltas[None, :]
    if nombre == "E3-kX":
        return mod.eta(X, hora)[:, None] - mod._kb(Z)[:, None] * deltas[None, :]
    return mod.log_lam(X, hora, deltas, Z)


def medir(nombre, mod, d, lado, mu, sd, deltas, jd):
    X, h, c, e = d["X"].astype(float), d["hora_utc"].astype(int), d["conteos"][lado], d["exposicion_s"]
    Z = est(covariables(X, d["columnas_x"], lado), mu, sd)
    L = log_lam(nombre, mod, X, Z, h, deltas)
    lam = np.exp(L) * e[:, None]
    ll = float((c * L - lam).sum())
    y = c[:, jd] > 0
    return {"ll": ll, "n": int(len(h)), "O": c.sum(0).astype(float).tolist(), "E": lam.sum(0).tolist(),
            "auc2": float(auc(1 - np.exp(-lam[:, jd]), y))}


def oe_resumen(O, E):
    r = np.log(np.asarray(O) / np.asarray(E))
    return {"log_OE": r.tolist(), "max_abs": float(np.abs(r).max()), "media_abs": float(np.abs(r).mean())}


def main():
    t0 = time.time()
    aj = [bins(d) for d in C.fechas("2026-06-29", "2026-07-12")]
    ca = [bins(d) for d in C.fechas("2026-07-13", "2026-07-16")]
    ev_f = [d for d in C.fechas("2026-07-17", "2026-09-03") if not (date(2026, 8, 22) <= d <= date(2026, 8, 25))]
    deltas, cols = np.asarray(aj[0]["deltas_bps"], float), aj[0]["columnas_x"]
    jd = int(np.where(deltas == 2.0)[0][0])
    hora = np.concatenate([d["hora_utc"] for d in aj]).astype(int); e = np.concatenate([d["exposicion_s"] for d in aj])
    Xa = np.vstack([d["X"] for d in aj]).astype(float)
    log(f"ajuste {len(hora)} bins ({time.time() - t0:.0f}s)")
    res = {"plan_sha256": (R90 / "PLAN_V90.sha256").read_text().split()[0], "deltas": deltas.tolist(), "lados": {}}
    for lado in ("ask", "bid"):
        R = res["lados"][lado] = {}
        c = np.vstack([d["conteos"][lado] for d in aj])
        Za = covariables(Xa, cols, lado); mu, sd = np.nanmean(Za, 0), np.nanstd(Za, 0); sd = np.where(sd > 0, sd, 1.0)
        Zs = est(Za, mu, sd)
        kw = dict(estimador="gbm", usar_h=USAR_H[lado], n_backfit=3, params_gbm=PARAMS)
        M = {"E3": ModeloE3Semiparametrico(**kw).ajustar(Xa, hora, c, e, deltas)}
        M["E3-kX"] = ModeloKX(**kw).ajustar(Xa, Zs, hora, c, e, deltas)
        M["E3-f"] = ModeloF(**kw).ajustar(Xa, hora, c, e, deltas)
        log(f"{lado}: E3 k={M['E3'].k:.4f}; f={np.round(M['E3-f'].f, 3).tolist()}; −kδ={np.round(-M['E3'].k * (deltas - deltas[0]), 3).tolist()} ({time.time() - t0:.0f}s)")
        R["historial"] = {n: m.historial for n, m in M.items()}
        # paso 0 + inclusión en calibración interna
        cal = {n: [medir(n, m, d, lado, mu, sd, deltas, jd) for d in ca] for n, m in M.items()}
        tot = {n: sum(x["ll"] for x in v) for n, v in cal.items()}
        oe0 = {n: oe_resumen(np.sum([x["O"] for x in v], 0), np.sum([x["E"] for x in v], 0)) for n, v in cal.items()}
        R["calibracion_interna"] = {"ll_total": tot, "OE": oe0, "por_dia": cal, "E3_vs_ref_v45": tot["E3"] - REF_V45[lado]}
        log(f"{lado}: cal ll E3 {tot['E3']:.0f} (v45 {REF_V45[lado]}) kX {tot['E3-kX']:.0f} f {tot['E3-f']:.0f}; max|logO/E| E3 {oe0['E3']['max_abs']:.3f} kX {oe0['E3-kX']['max_abs']:.3f}")
        if oe0["E3"]["max_abs"] < 0.05:
            R["paso0"] = "E3 bien calibrado por δ (max|log O/E| < 0,05): se detiene este lado"; log(f"{lado}: paso 0 detiene"); continue
        gana = sum(a["ll"] > b["ll"] for a, b in zip(cal["E3-f"], cal["E3"])); rel = (tot["E3-f"] - tot["E3"]) / abs(tot["E3"])
        R["inclusion_E3f"] = {"dias_ganados": int(gana), "mejora_rel": rel, "incluye": bool(gana >= 3 and rel >= 0.005)}
        log(f"{lado}: inclusión E3-f {gana}/4, {rel * 100:+.3f}% -> {R['inclusion_E3f']['incluye']}")
        if R["inclusion_E3f"]["incluye"]:
            M["E3-fkX"] = ModeloFKX(f_ini=M["E3-f"].f, **kw).ajustar(Xa, Zs, hora, c, e, deltas)
            R["historial"]["E3-fkX"] = M["E3-fkX"].historial
            log(f"{lado}: E3-fkX b={np.round(M['E3-fkX'].b, 3).tolist()} f={np.round(M['E3-fkX'].f, 3).tolist()} ({time.time() - t0:.0f}s)")
        # evaluación
        ev = {n: [] for n in M}
        for d in ev_f:
            b = bins(d)
            if b is None:
                log(f"  {d}: faltante"); continue
            for n, m in M.items():
                ev[n].append(medir(n, m, b, lado, mu, sd, deltas, jd) | {"fecha": str(d)})
        R["evaluacion_por_dia"] = ev
        log(f"{lado}: evaluación {len(ev['E3'])} días ({time.time() - t0:.0f}s)")
    (SAL / "resultados_v90.json").write_text(json.dumps(res, indent=1, default=float))
    log(f"fin {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
