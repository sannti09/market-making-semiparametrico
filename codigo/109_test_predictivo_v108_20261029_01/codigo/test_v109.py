#!/usr/bin/env python3
"""v109: evaluación del test 4–20 sep con los modelos v108 (= v103 con la curva de E3-fkX+B y E3-fkX reoptimizada, ver NOTA_V108).
Misma lógica que test_v104. Ver ENMIENDA_V109.md (y preregistro v101)."""
import hashlib, json, pickle, sys
from pathlib import Path
import numpy as np
from sklearn.metrics import roc_auc_score
R = Path(__file__).resolve().parents[1]; RR = R.parent; SAL = R / "salida"
assert hashlib.sha256((R / "ENMIENDA_V109.md").read_bytes()).hexdigest() == (R / "ENMIENDA_V109.sha256").read_text().split()[0]
sys.path.insert(0, str(RR / "101_test_p1_20261029_01" / "codigo")); sys.path.insert(0, str(RR / "102_walk_forward_20261029_01" / "codigo"))
import test_v101 as T  # noqa: E402
import wf_v102 as W  # noqa: E402
T.SAL = SAL
C108 = RR / "108_curva_e3_v2_20261029_01"
p = C108 / "modelos" / "modelos_finales_v108.pkl"
assert hashlib.sha256(p.read_bytes()).hexdigest() == json.loads((p.parent / "MANIFIESTO_v108.json").read_text())["pkl_sha256"]
sys.path.insert(0, str(C108 / "codigo"))  # necesario para deserializar ModeloFKXv2 (modelo_f_v2.py)
P = pickle.load(open(p, "rb")); MOD, deltas, cols = P["MOD"], P["deltas"], P["cols"]
NOMS = ["E3-fkX+B", "E3", "E3-fkX", "E1+h-f", "E1+S", "E1+X49", "E2m+h-f", "E2m+S", "E1", "E2+h-f", "E2+S"]  # 8 del preregistro + 3 informativos

def fase_B():
    jd = int(np.where(deltas == 2.0)[0][0]); por_dia, evs = [], []
    for d in T.fechas("2026-09-04", "2026-09-20"):
        b = T.dia_test(d, deltas, MOD)
        trd = T.pq.read_table(T.N.DAT / "trades_event" / f"binance_trades_events_BTCUSDT_{d.isoformat()}.parquet", columns=["event_time_us", "price", "aggressor_buy"])
        Tev, _, Cev = T.eventos_agresor(trd["event_time_us"].to_numpy(), trd["price"].to_numpy(), trd["aggressor_buy"].to_numpy(zero_copy_only=False).astype(bool))
        b["lam1"] = T.M.lambda_bins(MOD["H1"], {"fecha": d, "t_ms": b["t_ms"], "T_us": Tev.astype(np.int64), "tipo": np.where(Cev, 0, 1).astype(np.int8)})
        r = {"fecha": str(d), "n": len(b["t_ms"])}; L2 = {}
        for lado in ("ask", "bid"):
            L = W.lls(MOD, b, lado, cols, deltas); y = b["conteos"][lado]
            for m in NOMS:
                r[f"ll_{m}_{lado}"] = float((y * L[m] - np.exp(L[m])).sum()); r[f"auc_{m}_{lado}"] = float(roc_auc_score(y[:, jd] > 0, L[m][:, jd]))
                r[f"O_{lado}"] = float(y[:, jd].sum()); r[f"E_{m}_{lado}"] = float(np.exp(L[m][:, jd]).sum()); L2[(m, lado)] = L[m][:, jd]
        por_dia.append(r); i = b["barr_i"]
        evs.append(np.column_stack([b["barr_s"], b["conteos"]["ask"][i, jd], b["conteos"]["bid"][i, jd], b["S"][i, -1]] + [L2[(m, l)][i] for m in NOMS for l in ("ask", "bid")]))
        T.log(f"test {d}: {r['n']} bins, {len(i)} barridos")
    (SAL / "por_dia_test_v109.json").write_text(json.dumps(por_dia, indent=1)); E = np.vstack(evs); np.save(SAL / "eventos_test_v109.npy", E)
    return por_dia, E, NOMS

if __name__ == "__main__":
    T.log("v109: abriendo el test (repetición sobre 4–20 sep, ya consultado) con los modelos v108")
    T.analisis(*fase_B())
