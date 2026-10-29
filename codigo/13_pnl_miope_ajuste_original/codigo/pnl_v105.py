#!/usr/bin/env python3
"""v105: PnL de market making (AS miope δ* = argmax λ̂(δ)·δ) en el test 4–20 sep con los modelos congelados v103. Ver PLAN_V105.md."""
import hashlib, json, sys
from pathlib import Path
import numpy as np, pyarrow.parquet as pq
R = Path(__file__).resolve().parents[1]; RR = R.parent; SAL = R / "salida"
assert hashlib.sha256((R / "PLAN_V105.md").read_bytes()).hexdigest() == (R / "PLAN_V105.sha256").read_text().split()[0]
sys.path.insert(0, str(RR / "12_test_predictivo_ajuste_original" / "codigo"))
import test_v104 as V4  # noqa: E402  (modelos v103 verificados por sha; no ejecuta nada al importar)
T, W, MOD, deltas, cols = V4.T, V4.W, V4.MOD, V4.deltas, V4.cols
MODELOS = ["E3-fkX+B", "E3-fkX", "E3", "E1+X49", "E2m+S", "E2m+h-f", "E2+S", "E1+S", "E2+h-f", "E1+h-f", "E1"]
FIJOS = {"δ fijo 0,5": 0.5, "δ fijo 2": 2.0, "δ fijo 5": 5.0}
QMAX, UNIDAD, HS = 10, 0.01, (10, 60)

def dia(d):
    b = T.dia_test(d, deltas, MOD); t0 = np.asarray(b["t_ms"], np.int64)
    trd = pq.read_table(T.N.DAT / "trades_event" / f"binance_trades_events_BTCUSDT_{d.isoformat()}.parquet", columns=["event_time_us", "price", "aggressor_buy"])
    te, pe, ce = T.eventos_agresor(trd["event_time_us"].to_numpy(), trd["price"].to_numpy(), trd["aggressor_buy"].to_numpy(zero_copy_only=False).astype(bool))
    b["lam1"] = T.M.lambda_bins(MOD["H1"], {"fecha": d, "t_ms": t0, "T_us": te.astype(np.int64), "tipo": np.where(ce, 0, 1).astype(np.int8)})
    L = {l: W.lls(MOD, b, l, cols, deltas) for l in ("ask", "bid")}
    T.guardia_test(d); fe = pq.read_table(T.N.DAT / "market_features_100ms" / f"binance_market_features_100ms_BTCUSDT_{d.isoformat()}.parquet", columns=["ts_ms", "state_valid", "best_bid", "best_ask", "mid"])
    ts = fe["ts_ms"].to_numpy(); sv = fe["state_valid"].to_numpy(zero_copy_only=False).astype(bool)
    mid = np.where(sv, fe["mid"].to_numpy(zero_copy_only=False).astype(float), np.nan)
    bb, ba = fe["best_bid"].to_numpy(zero_copy_only=False).astype(float), fe["best_ask"].to_numpy(zero_copy_only=False).astype(float)
    r0 = ((t0 - ts[0]) // 100).astype(np.int64); m0 = mid[r0]; bbt = np.round(bb[r0] * 100).astype(np.int64); bat = np.round(ba[r0] * 100).astype(np.int64)
    ok = np.isfinite(m0) & (bbt > 0) & (bat > bbt)
    # agresores por bin (cada evento cae en el bin que lo contiene)
    ev = {}
    for lado, sel in (("ask", ce), ("bid", ~ce)):
        tl, pl = te[sel] // 1000, np.round(pe[sel] * 100).astype(np.int64); j = np.searchsorted(t0, tl, side="right") - 1; v = (j >= 0) & (tl < t0[np.maximum(j, 0)] + 1000)
        ev[lado] = (j[v], tl[v], pl[v])
    mid_end = mid[np.nonzero(np.isfinite(mid))[0][-1]]
    def mk(tf, p, s):   # s = +1 vendimos (ask), −1 compramos (bid)
        out = []
        for H in HS:
            k = (tf - ts[0]) // 100 + 10 * H; mh = np.where(k < len(mid), mid[np.minimum(k, len(mid) - 1)], np.nan); out.append(s * (p - mh) / p * 1e4)
        return out
    res = {}
    for nom in MODELOS + list(FIJOS):
        q = {}
        for lado, sg in (("ask", 1), ("bid", -1)):
            if nom in FIJOS: dl = np.full(len(t0), FIJOS[nom])
            else: dl = deltas[np.argmax(np.exp(L[lado][nom]) * deltas[None, :], 1)]
            px = m0 * (1 + sg * dl / 1e4) * 100
            q[lado] = np.maximum(np.ceil(px - 1e-6).astype(np.int64), bbt + 1) if lado == "ask" else np.minimum(np.floor(np.nan_to_num(px) + 1e-6).astype(np.int64), bat - 1)
        # primera ejecución por bin y lado: agresor estrictamente más allá de la cotización
        fills = {}
        for lado in ("ask", "bid"):
            j, tl, pl = ev[lado]; c = ok[j] & ((pl > q[lado][j]) if lado == "ask" else (pl < q[lado][j]))
            jj, pr = np.unique(j[c], return_index=True); fills[lado] = dict(zip(jj.tolist(), tl[c][pr].tolist()))
        inv, cash, F = 0, 0.0, []
        for k in sorted(set(fills["ask"]) | set(fills["bid"])):
            i0 = inv
            if k in fills["ask"] and i0 > -QMAX: p = q["ask"][k] / 100; inv -= 1; cash += p * UNIDAD; F.append((fills["ask"][k], p, 1))
            if k in fills["bid"] and i0 < QMAX: p = q["bid"][k] / 100; inv += 1; cash -= p * UNIDAD; F.append((fills["bid"][k], p, -1))
        F = np.array(F, float).reshape(-1, 3); n = len(F)
        m10, m60 = mk(F[:, 0].astype(np.int64), F[:, 1], F[:, 2]) if n else (np.array([]), np.array([]))
        pnl = cash + inv * mid_end * UNIDAD; nocional = float((F[:, 1] * UNIDAD).sum())
        dl_med = {l: float(np.median(np.where(ok, (q[l] / 100 / np.where(ok, m0, 1) - 1) * 1e4 * (1 if l == "ask" else -1), np.nan)[ok])) for l in ("ask", "bid")}
        res[nom] = {"n": n, "pnl": float(pnl), "nocional": nocional, "s10": float(np.nansum(m10)), "n10": int(np.isfinite(m10).sum()), "s60": float(np.nansum(m60)), "n60": int(np.isfinite(m60).sum()),
                    "inv_fin": inv, "delta_mediana_ask": dl_med["ask"], "delta_mediana_bid": dl_med["bid"]}
    return res

if __name__ == "__main__":
    por_dia = {}
    for d in T.fechas("2026-09-04", "2026-09-20"):
        por_dia[str(d)] = dia(d); r = por_dia[str(d)]
        print(d, " | ".join(f"{m}: {r[m]['n']} ej, {1e4 * r[m]['pnl'] / max(r[m]['nocional'], 1e-9):+.2f} bps" for m in ("E3-fkX+B", "E2m+S", "E1", "δ fijo 0,5")), flush=True)
    (SAL / "por_dia_v105.json").write_text(json.dumps(por_dia, indent=1))
    dias = list(por_dia); nd = len(dias); IDX = np.random.default_rng(20261029).integers(0, nd, size=(2000, nd))
    filas = []
    for nom in MODELOS + list(FIJOS):
        g = lambda k: np.array([por_dia[d][nom][k] for d in dias], float)
        n, pnl, noc, s10, n10, s60, n60 = g("n"), g("pnl"), g("nocional"), g("s10"), g("n10"), g("s60"), g("n60")
        bps = lambda num, den: (num.sum() / den.sum(), *np.percentile(num[IDX].sum(1) / den[IDX].sum(1), [2.5, 97.5]))
        a, b_, c = bps(1e4 * pnl, noc), bps(s10, n10), bps(s60, n60)
        filas.append({"politica": nom, "ejec_dia": float(n.mean()), "pnl_usdt_dia": float(pnl.mean()), "dias_positivos": int((pnl > 0).sum()),
                      "pnl_bps_ejec": a, "mk10": b_, "mk60": c, "delta_mediana": float(np.mean([por_dia[d][nom]["delta_mediana_ask"] for d in dias]))})
    (SAL / "resumen_v105.json").write_text(json.dumps(filas, indent=1))
    lin = ["### PnL de market making en el test (4–20 sep, 17 días; AS miope δ* = argmax λ̂(δ)·δ; 0,01 BTC por orden; |q| ≤ 10; bruto, sin comisiones)", "",
           "| Política | δ mediana (bps) | Ejec./día | PnL/día (USDT) | Días > 0 | PnL por ejec. (bps) [IC95] | Markout 10 s (bps) [IC95] | Markout 60 s (bps) [IC95] |", "|---|---|---|---|---|---|---|---|"]
    for f in filas:
        fm = lambda x: f"{x[0]:+.2f} [{x[1]:+.2f}; {x[2]:+.2f}]"
        lin.append(f"| {f['politica']} | {f['delta_mediana']:.2f} | {f['ejec_dia']:.0f} | {f['pnl_usdt_dia']:+.2f} | {f['dias_positivos']}/17 | {fm(f['pnl_bps_ejec'])} | {fm(f['mk10'])} | {fm(f['mk60'])} |")
    lin += ["", "Comisión maker Binance spot: 10 bps (VIP0) o 7,5 bps (con BNB) por ejecución; el PnL neto = bruto − comisión."]
    (R / "tablas_tesis" / "T6_pnl_test.md").write_text("\n".join(lin) + "\n"); print("\n".join(lin))
