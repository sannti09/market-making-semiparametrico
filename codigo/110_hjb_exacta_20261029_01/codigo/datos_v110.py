"""v110: carga común (plan verificado, modelos v108 verificados por sha, día de entrenamiento 3 sep, σ_t, formas por modelo)."""
import hashlib, json, pickle, sys, time
from datetime import date
from pathlib import Path
import numpy as np, pyarrow.parquet as pq
R = Path(__file__).resolve().parents[1]; RR = R.parent; SAL = R / "salida"
assert hashlib.sha256((R / "PLAN_V110.md").read_bytes()).hexdigest() == (R / "PLAN_V110.sha256").read_text().split()[0], "PLAN_V110 modificado"
assert hashlib.sha256((R / "ENMIENDA_V110B.md").read_bytes()).hexdigest() == (R / "ENMIENDA_V110B.sha256").read_text().split()[0], "ENMIENDA_V110B modificada"
sys.path.insert(0, str(RR / "108_curva_e3_v2_20261029_01" / "codigo")); sys.path.insert(0, str(RR / "101_test_p1_20261029_01" / "codigo")); sys.path.insert(0, str(RR / "102_walk_forward_20261029_01" / "codigo"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_v101 as T  # noqa: E402  (solo funciones; no carga modelos v103)
import wf_v102 as W  # noqa: E402
T.SAL = SAL
_p = RR / "108_curva_e3_v2_20261029_01" / "modelos" / "modelos_finales_v108.pkl"
assert hashlib.sha256(_p.read_bytes()).hexdigest() == json.loads((_p.parent / "MANIFIESTO_v108.json").read_text())["pkl_sha256"], "pkl v108 no coincide con el manifiesto"
P = pickle.load(open(_p, "rb")); MOD, deltas, cols = P["MOD"], P["deltas"], P["cols"]
MODELOS = ["E3-fkX+B", "E3-fkX", "E3", "E1+X49", "E2m+S", "E2m+h-f", "E2+S", "E1+S", "E2+h-f", "E1+h-f", "E1"]
FKX = ("E3-fkX+B", "E3-fkX")
DIAS_RANGO = [date(2026, 8, 3), date(2026, 8, 10), date(2026, 8, 17), date(2026, 8, 24), date(2026, 8, 31), date(2026, 9, 3)]
G, Q, UNIDAD, HS = 0.01, 10, 0.01, (10, 60)
LOG = []
def log(m, f="log_v110.txt"):
    LOG.append(f"[{time.strftime('%H:%M:%S')}] {m}"); print(LOG[-1], flush=True); (SAL / f).write_text("\n".join(LOG))

def sigma_causal(t0, m0):
    """σ_t como v106: EWMA (semivida 60 s) del cuadrado del retorno de 1 s del mid (bps), piso 1e-3."""
    r = np.zeros(len(t0)); seg = (np.diff(t0) == 1000) & np.isfinite(m0[1:]) & np.isfinite(m0[:-1]); r[1:][seg] = 1e4 * np.log(m0[1:][seg] / m0[:-1][seg])
    a = 1 - 0.5 ** (1 / 60); v = np.empty(len(r)); acc = 0.465 ** 2
    for i, x in enumerate(r.tolist()):
        acc = (1 - a) * acc + a * x * x; v[i] = acc
    return np.maximum(np.sqrt(v), 1e-3)

def dia_entrenamiento(d=date(2026, 9, 3)):
    """Día de entrenamiento (por defecto 3 sep): L por lado y modelo, σ_t, mask ok."""
    assert d <= date(2026, 9, 3)
    b = T.dia_aj(d); pk = T.M.cargar(str(RR / "99_colab_e1_e2_20261029_01" / "paquete"), d)
    b["lam2"] = T.M.lambda_bins(MOD["H2"], pk); b["lam1"] = T.M.lambda_bins(MOD["H1"], pk)
    L = {l: W.lls(MOD, b, l, cols, deltas) for l in ("ask", "bid")}
    t0 = np.asarray(b["t_ms"], np.int64)
    fe = pq.read_table(T.N.DAT / "market_features_100ms" / f"binance_market_features_100ms_BTCUSDT_{d.isoformat()}.parquet", columns=["ts_ms", "state_valid", "mid"])
    ts = fe["ts_ms"].to_numpy(); sv = fe["state_valid"].to_numpy(zero_copy_only=False).astype(bool); mid = np.where(sv, fe["mid"].to_numpy(zero_copy_only=False).astype(float), np.nan)
    m0 = mid[((t0 - ts[0]) // 100).astype(np.int64)]
    ok = np.isfinite(m0)
    return {"L": L, "sg": sigma_causal(t0, m0), "ok": ok, "n": len(t0)}

def forma_modelo(L, lado, m):
    """Forma normalizada g (9,) del modelo/lado. Devuelve dict: tipo 'fija' (g, desviación máx. entre segundos) o 'm' (f, m (n,), error de reproducción)."""
    Lm = L[lado][m]; g = Lm - Lm[:, [0]]
    if m in FKX:
        f = np.asarray(MOD[m][lado].f, float); mm = g[:, -1] / f[-1]
        return {"tipo": "m", "f": f, "m": mm, "err_repr": float(np.abs(g - mm[:, None] * f[None, :]).max())}
    med = np.median(g, 0)
    return {"tipo": "fija", "g": med, "dev_max": float(np.abs(g - med[None, :]).max())}
