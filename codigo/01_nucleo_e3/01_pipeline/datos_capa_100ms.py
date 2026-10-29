"""Lectura de la capa canónica 100 ms (202 columnas) y construcción de bins para E1/E3 (v36).

Convenciones (verificadas empíricamente en 2026-06-29, bloque de ajuste):
- Estado del libro en t = fila con ts_ms == t (incluye actualizaciones hasta t; causal). Con esa regla
  solo ~1,4 % de los trades caen al lado contrario del libro; filas posteriores ya reflejan el impacto.
- Respuesta: eventos agresores (trades de trades_event con el mismo event_time_us y lado, precio extremo)
  con event_time_us en [t, t+Δ). Lado ask <- compradores; bid <- vendedores. Cruce: precio >= mid(1+δ)
  (ask) o <= mid(1-δ) (bid). Cruce != fill.
- Un bin es válido si state_valid y target_trade_data_valid_next_100ms son verdaderos en todas sus filas.
- Ninguna columna target_* entra en X. tod/dow tampoco: el tiempo entra por h(t).
- Candados: solo fechas de bloques abiertos en PARTICION_ANTEPROYECTO.json; reserva y fin de capa bloqueados.
"""

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np
import pyarrow.parquet as pq

V = Path(__file__).resolve().parents[1]
PARTICION = json.load(open(V / "02_configuracion" / "PARTICION_ANTEPROYECTO.json"))
CAPA = Path("/Users/santiagorueda/Documents/UNI/Semiparametric Market Making") / PARTICION["capa"]

GRUPOS_X: Dict[str, List[str]] = {
    "libro": ["spread_bps", "imbalance_top1", "imbalance_top5", "imbalance_top20", "imbalance_weighted_top20",
              "microprice_premium_bps", "depth_bid_top5", "depth_ask_top5", "depth_bid_top20", "depth_ask_top20",
              "book_slope_bid_ticks_per_btc_top20", "book_slope_ask_ticks_per_btc_top20",
              "depth_entropy_bid_top20", "depth_entropy_ask_top20", "book_age_ms"],
    "ofi": ["ofi_weighted_top1", "ofi_weighted_top5", "ofi_weighted_top20", "ofi_top5_weighted"],
    "volatilidad": ["realized_vol_1000ms", "realized_vol_5000ms", "realized_vol_10000ms", "realized_vol_60000ms",
                    "mid_change_bps_100ms"],
    "flujo": [f"past_{q}_{s}_sum_{w}ms" for q in ("n", "vol") for s in ("buy", "sell") for w in (1000, 5000, 30000, 60000)]
             + [f"past_signed_volume_sum_{w}ms" for w in (1000, 5000, 30000, 60000)],
}
COLUMNAS_BASE = ["ts_ms", "state_valid", "target_trade_data_valid_next_100ms", "mid"]


def rol_de_fecha(d: date) -> str:
    for nombre, b in PARTICION["bloques"].items():
        if date.fromisoformat(b["desde"]) <= d <= date.fromisoformat(b["hasta"]):
            return nombre
    return "fuera_de_particion"


def verificar_acceso(d: date) -> str:
    r = PARTICION["reserva_bloqueada"]
    if date.fromisoformat(r["desde"]) <= d <= date.fromisoformat(r["hasta"]):
        raise PermissionError(f"{d}: reserva bloqueada")
    rol = rol_de_fecha(d)
    if rol not in PARTICION["bloques_abiertos"]:
        raise PermissionError(f"{d}: bloque '{rol}' cerrado (abiertos: {PARTICION['bloques_abiertos']})")
    return rol


def fechas_de_bloque(nombre: str) -> List[date]:
    b = PARTICION["bloques"][nombre]
    d, fin, out = date.fromisoformat(b["desde"]), date.fromisoformat(b["hasta"]), []
    while d <= fin:
        out.append(d)
        d += timedelta(days=1)
    return out


def eventos_agresor(event_time_us: np.ndarray, precio: np.ndarray, compra: np.ndarray):
    """Agrupa trades consecutivos con el mismo event_time_us y lado; precio extremo del grupo."""
    if len(event_time_us) == 0:
        return event_time_us, precio, compra
    nuevo = np.ones(len(event_time_us), bool)
    nuevo[1:] = (event_time_us[1:] != event_time_us[:-1]) | (compra[1:] != compra[:-1])
    g = np.cumsum(nuevo) - 1
    n = g[-1] + 1
    t_ev = event_time_us[nuevo]
    c_ev = compra[nuevo]
    p_max = np.full(n, -np.inf)
    p_min = np.full(n, np.inf)
    np.maximum.at(p_max, g, precio)
    np.minimum.at(p_min, g, precio)
    return t_ev, np.where(c_ev, p_max, p_min), c_ev


def indice_en_rejilla(ts: np.ndarray, t_obj_ms: np.ndarray, paso_ms: int = 100) -> np.ndarray:
    """Fila vigente en t_obj (ts[k] <= t_obj < ts[k] + paso_ms) o -1 si t_obj queda fuera de la cobertura.

    v37: antes se usaba searchsorted(..., "right") - 1 con k < len(ts), que acepta la última fila cuando
    t_obj supera el fin del archivo (o cae tras un hueco de la rejilla). La edad ts[k] -> t_obj queda acotada
    por paso_ms; el llamador debe exigir además state_valid en k.
    """
    t_obj_ms = np.asarray(t_obj_ms)
    k = np.searchsorted(ts, t_obj_ms, side="right") - 1
    kc = np.clip(k, 0, len(ts) - 1)
    cubierto = (k >= 0) & (t_obj_ms - ts[kc] < paso_ms)
    return np.where(cubierto, k, -1)


def construir_bins_dia(d: date, deltas_bps: Sequence[float], delta_s: float = 1.0, paso_s: float = 1.0,
                       grupos: Optional[Sequence[str]] = None, _capa: Optional[Path] = None) -> Dict:
    """Bins [t, t+Δ) cada paso_s en un día. Devuelve X (por bin), conteos por lado y δ, exposición y hora UTC."""
    rol = verificar_acceso(d) if _capa is None else "fixture"
    capa = _capa or CAPA
    grupos = list(grupos or GRUPOS_X)
    cols_x = [c for g in grupos for c in GRUPOS_X[g]]
    tb = pq.read_table(capa / "market_features_100ms" / f"binance_market_features_100ms_BTCUSDT_{d.isoformat()}.parquet",
                       columns=COLUMNAS_BASE + cols_x)
    ts = tb["ts_ms"].to_numpy()
    fin_capa = int(datetime.fromisoformat(PARTICION["fin_exclusivo_capa_utc"].replace("Z", "+00:00")).timestamp() * 1000)
    valido = (tb["state_valid"].to_numpy(zero_copy_only=False).astype(bool)
              & tb["target_trade_data_valid_next_100ms"].to_numpy(zero_copy_only=False).astype(bool)
              & (ts < fin_capa))
    mid = tb["mid"].to_numpy(zero_copy_only=False).astype(float)
    n_sub = int(round(delta_s * 10))
    paso = int(round(paso_s * 10))
    # bin válido si todas sus n_sub filas son válidas
    cv = np.concatenate([[0], np.cumsum(~valido)])
    inicios = np.arange(0, len(ts) - n_sub + 1, paso)
    ok = (cv[inicios + n_sub] - cv[inicios]) == 0
    ok &= np.isfinite(mid[inicios])
    ini = inicios[ok]
    t0 = ts[ini]
    X = np.column_stack([tb[c].to_numpy(zero_copy_only=False).astype(float)[ini] for c in cols_x]) if cols_x else np.zeros((len(ini), 0))

    tr = pq.read_table(capa / "trades_event" / f"binance_trades_events_BTCUSDT_{d.isoformat()}.parquet",
                       columns=["event_time_us", "price", "aggressor_buy"])
    t_ev, p_ev, c_ev = eventos_agresor(tr["event_time_us"].to_numpy(), tr["price"].to_numpy(),
                                       tr["aggressor_buy"].to_numpy(zero_copy_only=False).astype(bool))
    deltas = np.array(sorted(set(float(x) for x in deltas_bps)))
    conteos = {}
    for lado, sel in (("ask", c_ev), ("bid", ~c_ev)):
        tl, pl = t_ev[sel], p_ev[sel]
        a = np.searchsorted(tl, t0 * 1000, side="left")
        b = np.searchsorted(tl, (t0 + int(delta_s * 1000)) * 1000, side="left")
        m = mid[ini]
        cnt = np.zeros((len(ini), len(deltas)), np.int32)
        # extremo del bin por bin (los conteos por δ necesitan todos los eventos; se recorren por bin)
        for j in np.nonzero(b > a)[0]:
            pj = pl[a[j]:b[j]]
            if lado == "ask":
                cnt[j] = (pj[:, None] >= m[j] * (1 + deltas[None, :] / 1e4)).sum(0)
            else:
                cnt[j] = (pj[:, None] <= m[j] * (1 - deltas[None, :] / 1e4)).sum(0)
        conteos[lado] = cnt
    hora = ((t0 // 1000) % 86400) // 3600
    return {"fecha": d.isoformat(), "rol": rol, "t_ms": t0, "X": X, "columnas_x": cols_x, "grupos": grupos,
            "conteos": conteos, "deltas_bps": deltas, "exposicion_s": np.full(len(ini), delta_s), "hora_utc": hora,
            "n_bins_nominales": len(inicios), "n_bins_validos": int(ok.sum()),
            "n_trades": tr.num_rows, "n_eventos_agresor": int(len(t_ev))}
