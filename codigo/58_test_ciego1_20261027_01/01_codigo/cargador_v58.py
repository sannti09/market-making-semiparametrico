"""v58: cargador de bins 1 s sobre la capa canónica 100 ms para el test ciego 1 (solo código nuevo; reutiliza v37 sin editarlo).

Igual que v52 salvo:
- GUARDIA ÚNICO `verificar_acceso_v58` (todo acceso a Parquet pasa por él; también el de E2 vía parche de V37.verificar_acceso):
    * 2026-06-29..2026-08-21 -> capa local v1.
    * 2026-08-26..2026-09-15 -> capa extendida v2, y SOLO si la compuerta está cerrada con éxito
      (salida/CALIBRACION_V58.json + salida/SHA256_COMPUERTA.txt coincidentes).
    * 22-25 ago y cualquier fecha > 2026-09-15 -> PermissionError (reserva / ciego 2).
  El guardia fija además V37.CAPA según la capa de la fecha (E2 lee trades a través de V37.CAPA).
- fin_capa: v1 usa el fin de partición de v37 (24 ago 12:00); v2 no tiene recorte.
- La fila 0 de 2026-06-29 (inicio de la capa v1) conserva su OFI nulo como en v37/v45/v52. La primera fila de v2 (26 ago)
  no tiene excepción: si trae OFI nulo se excluye (regla de la unión).
"""
import hashlib
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

BASE = Path(__file__).resolve().parents[2]
SAL = Path(__file__).resolve().parents[1] / "salida"
sys.path.insert(0, str(BASE / "37_correcciones_revision_astra_v36_20261026_01" / "01_pipeline"))
import datos_capa_100ms as V37  # noqa: E402
from datos_capa_100ms import COLUMNAS_BASE, GRUPOS_X, eventos_agresor  # noqa: E402

COMP1 = Path("/Users/santiagorueda/Documents/UNI/Semiparametric Market Making/Comparativa 1")
CAPA_V1 = COMP1 / "binance_canonical_100ms_unified_v1_20260629_20260824T12"
CAPA_V2 = COMP1 / "binance_canonical_100ms_ext_v2_20260826_20261006"
assert V37.CAPA == CAPA_V1

V1_DESDE, V1_HASTA = date(2026, 6, 29), date(2026, 8, 21)
V2_DESDE, V2_HASTA = date(2026, 8, 26), date(2026, 9, 15)
DESDE_V52 = V1_DESDE
_TOPE = [V2_HASTA]          # restringir() reduce el tope (smoke test)
ACCESOS = []                # registro de fechas leídas (auditoría)
LAG_FILAS = 2


def restringir(hasta: date):
    _TOPE[0] = min(hasta, V2_HASTA)


def compuerta_cerrada() -> bool:
    """Compuerta: CALIBRACION_V58.json existe y su sha256 coincide con SHA256_COMPUERTA.txt."""
    cal, sh = SAL / "CALIBRACION_V58.json", SAL / "SHA256_COMPUERTA.txt"
    if not (cal.exists() and sh.exists()):
        return False
    return hashlib.sha256(cal.read_bytes()).hexdigest() == sh.read_text().split()[0]


def capa_de(d: date) -> Path:
    if V1_DESDE <= d <= V1_HASTA:
        return CAPA_V1
    if V2_DESDE <= d <= V2_HASTA:
        return CAPA_V2
    raise PermissionError(f"{d}: fuera de las capas permitidas (reserva 22-25 ago / ciego 2 desde 16 sep)")


def verificar_acceso_v58(d: date) -> str:
    if d > _TOPE[0]:
        raise PermissionError(f"{d}: por encima del tope vigente {_TOPE[0]}")
    capa = capa_de(d)                      # lanza PermissionError en reserva y > 15 sep
    if capa is CAPA_V2 and not compuerta_cerrada():
        raise PermissionError(f"{d}: el test ciego no se abre antes de cerrar la compuerta (CALIBRACION_V58.json + sha256)")
    V37.CAPA = capa
    ACCESOS.append(d.isoformat())
    return "v1" if capa is CAPA_V1 else "v2"


V37.verificar_acceso = verificar_acceso_v58   # E2 (modelo_e2_binned.eventos_dia) usa este nombre en tiempo de llamada


def fechas(desde: str, hasta: str):
    d, fin, out = date.fromisoformat(desde), date.fromisoformat(hasta), []
    while d <= fin:
        out.append(d)
        d += timedelta(days=1)
    return out


def _archivos_features(d: date, capa: Path):
    f = capa / "market_features_100ms"
    unico = f / f"binance_market_features_100ms_BTCUSDT_{d.isoformat()}.parquet"
    if unico.exists():
        return [unico]
    partes = [f / f"binance_market_features_100ms_BTCUSDT_{d.isoformat()}_{s}.parquet" for s in ("00-12", "12-00")]
    return partes if all(p.exists() for p in partes) else []


def _conteos(t_ev, p_ev, c_ev, t0, m, deltas, delta_s):
    out = {}
    for lado, sel in (("ask", c_ev), ("bid", ~c_ev)):
        tl, pl = t_ev[sel], p_ev[sel]
        a = np.searchsorted(tl, t0 * 1000, side="left")
        b = np.searchsorted(tl, (t0 + int(round(delta_s * 1000))) * 1000, side="left")
        cnt = np.zeros((len(t0), len(deltas)), np.int32)
        for j in np.nonzero(b > a)[0]:
            pj = pl[a[j]:b[j]]
            if lado == "ask":
                cnt[j] = (pj[:, None] >= m[j] * (1 + deltas[None, :] / 1e4)).sum(0)
            else:
                cnt[j] = (pj[:, None] <= m[j] * (1 - deltas[None, :] / 1e4)).sum(0)
        out[lado] = cnt
    return out


def construir_bins_v58(d: date, deltas_bps, delta_s: float = 1.0, paso_s: float = 1.0):
    rol = verificar_acceso_v58(d)
    capa = capa_de(d)
    cols_x = [c for g in GRUPOS_X for c in GRUPOS_X[g]]
    archivos = _archivos_features(d, capa)
    if not archivos:
        return {"fecha": d.isoformat(), "faltante": True, "motivo": "sin archivo de features"}
    tb = pa.concat_tables([pq.read_table(a, columns=COLUMNAS_BASE + cols_x) for a in archivos]) if len(archivos) > 1 \
        else pq.read_table(archivos[0], columns=COLUMNAS_BASE + cols_x)
    ts = tb["ts_ms"].to_numpy()
    if np.any(np.diff(ts) <= 0):
        o = np.argsort(ts, kind="stable")
        tb = tb.take(pa.array(o))
        ts = tb["ts_ms"].to_numpy()
    cobertura = {"filas": int(len(ts)), "saltos_distintos_de_100ms": int((np.diff(ts) != 100).sum()),
                 "archivos": [a.name for a in archivos], "capa": rol}
    if capa is CAPA_V1:
        fin_capa = int(datetime.fromisoformat(V37.PARTICION["fin_exclusivo_capa_utc"].replace("Z", "+00:00")).timestamp() * 1000)
    else:
        fin_capa = np.iinfo(np.int64).max
    Xfull = np.column_stack([tb[c].to_numpy(zero_copy_only=False).astype(float) for c in cols_x])
    i_ofi = [cols_x.index(c) for c in GRUPOS_X["ofi"]]
    ofi_nulo = np.isnan(Xfull[:, i_ofi]).any(1)
    if d == DESDE_V52:
        ofi_nulo[0] = False   # primera fila de la capa v1 (no es unión): v37/v45/v52 la conservan
    valido = (tb["state_valid"].to_numpy(zero_copy_only=False).astype(bool)
              & tb["target_trade_data_valid_next_100ms"].to_numpy(zero_copy_only=False).astype(bool)
              & (ts < fin_capa) & ~ofi_nulo)
    cobertura["filas_ofi_nulo_excluidas"] = int(ofi_nulo.sum())
    mid = tb["mid"].to_numpy(zero_copy_only=False).astype(float)
    n_sub, paso = int(round(delta_s * 10)), int(round(paso_s * 10))
    cv = np.concatenate([[0], np.cumsum(~valido)])
    inicios = np.arange(0, len(ts) - n_sub + 1, paso)
    ok = ((cv[inicios + n_sub] - cv[inicios]) == 0) & np.isfinite(mid[inicios])
    lag_idx = np.maximum(inicios - LAG_FILAS, 0)
    ok &= ~ofi_nulo[lag_idx]
    ini = inicios[ok]
    t0 = ts[ini]
    X, Xlag = Xfull[ini], Xfull[lag_idx[ok]]
    tr = pq.read_table(capa / "trades_event" / f"binance_trades_events_BTCUSDT_{d.isoformat()}.parquet",
                       columns=["event_time_us", "price", "aggressor_buy"])
    t_ev, p_ev, c_ev = eventos_agresor(tr["event_time_us"].to_numpy(), tr["price"].to_numpy(),
                                       tr["aggressor_buy"].to_numpy(zero_copy_only=False).astype(bool))
    deltas = np.array(sorted(set(float(x) for x in deltas_bps)))
    m = mid[ini]
    conteos = _conteos(t_ev, p_ev, c_ev, t0, m, deltas, delta_s)
    conteos100 = _conteos(t_ev, p_ev, c_ev, t0, m, deltas, 0.1)
    hora = ((t0 // 1000) % 86400) // 3600
    return {"fecha": d.isoformat(), "rol": rol, "faltante": False, "t_ms": t0, "X": X, "X_lag": Xlag, "columnas_x": cols_x,
            "conteos": conteos, "conteos_100ms": conteos100, "deltas_bps": deltas,
            "exposicion_s": np.full(len(ini), delta_s), "hora_utc": hora, "n_bins_nominales": len(inicios),
            "n_bins_validos": int(ok.sum()), "n_eventos_agresor": int(len(t_ev)), "cobertura": cobertura}
