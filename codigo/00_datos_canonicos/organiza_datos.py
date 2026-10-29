"""Organiza la capa canónica BTCUSDT 100 ms (29 jun – 26 oct 2026) en una carpeta única, un archivo por día.
Fuentes (solo lectura): v1 (29 jun – 23 ago), v2 del paquete (24–25 ago), v2 local (26 ago – 6 oct, 16 sep parchado),
v3 del paquete (7–26 oct, 13 oct parchado). Enlace duro si el día es un solo archivo; concatenación si v1 viene en medios días."""
import hashlib, json, os, sys, time
from datetime import date, timedelta
from pathlib import Path
import numpy as np, pyarrow as pa, pyarrow.parquet as pq

C1 = Path('/Users/santiagorueda/Documents/UNI/Semiparametric Market Making/Comparativa 1')
V1 = C1 / 'binance_canonical_100ms_unified_v1_20260629_20260824T12'
V2 = C1 / 'binance_canonical_100ms_ext_v2_20260826_20261006'
PK = Path('/Users/santiagorueda/Downloads/PAQUETE_DESCARGA_20261028')
OUT = Path(sys.argv[1])
assert not OUT.exists(), f'ya existe {OUT}'
CAPAS = {'market_features_100ms': 'binance_market_features_100ms_BTCUSDT_', 'trades_event': 'binance_trades_events_BTCUSDT_'}

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''): h.update(b)
    return h.hexdigest()

def fuentes(capa, d):
    pref = CAPAS[capa]
    if d <= '2026-08-23':
        fs = sorted((V1 / capa).glob(f'{pref}{d}*.parquet')); capa_src = 'v1_unified'
    elif d <= '2026-08-25':
        fs = [PK / 'v2_ago' / capa / f'{pref}{d}.parquet']; capa_src = 'ext_v2 (paquete Drive)'
    elif d <= '2026-10-06':
        fs = [V2 / capa / f'{pref}{d}.parquet']; capa_src = 'ext_v2' + (' (parche 16 sep)' if d == '2026-09-16' and capa == 'market_features_100ms' else '')
    else:
        fs = [PK / 'v3_oct' / capa / f'{pref}{d}.parquet']; capa_src = 'ext_v3' + (' (parche 13 oct)' if d == '2026-10-13' and capa == 'market_features_100ms' else '')
    assert fs and all(f.exists() for f in fs), (capa, d, fs)
    return fs, capa_src

cat, t0 = {}, time.time()
d = date(2026, 6, 29)
while d <= date(2026, 10, 26):
    ds = str(d); cat[ds] = {}
    for capa, pref in CAPAS.items():
        fs, capa_src = fuentes(capa, ds)
        dst = OUT / capa / f'{pref}{ds}.parquet'; dst.parent.mkdir(parents=True, exist_ok=True)
        if len(fs) == 1:
            os.link(fs[0], dst); metodo = 'enlace duro'
        else:
            t = pa.concat_tables([pq.read_table(f) for f in fs])
            pq.write_table(t, dst, compression='zstd'); metodo = f'concatenación de {len(fs)} medios días'
        meta = pq.read_metadata(dst)
        ent = {'capa_origen': capa_src, 'origen': [str(f) for f in fs], 'metodo': metodo, 'filas': meta.num_rows,
               'sha256': sha(dst), 'bytes': dst.stat().st_size}
        if capa == 'market_features_100ms':
            t = pq.read_table(dst, columns=['ts_ms', 'state_valid'])
            ts = t['ts_ms'].to_numpy(); v = t['state_valid'].to_numpy(zero_copy_only=False).astype(bool)
            ent.update({'filas_validas_frac': round(float(v.mean()), 6), 'ts_continuo_100ms': bool(np.all(np.diff(ts) == 100)),
                        'ts_inicio_ok': int(ts[0]) == int(time.mktime(d.timetuple()) - time.timezone) * 1000})
        cat[ds][capa] = ent
    print(ds, cat[ds]['market_features_100ms']['capa_origen'], '|', cat[ds]['market_features_100ms']['metodo'],
          '| filas', cat[ds]['market_features_100ms']['filas'], '| válidas', cat[ds]['market_features_100ms']['filas_validas_frac'],
          f'| {(time.time() - t0) / 60:.1f} min', flush=True)
    d += timedelta(days=1)

(OUT / 'CATALOGO.json').write_text(json.dumps({'creado': time.strftime('%Y-%m-%d %H:%M'), 'simbolo': 'BTCUSDT', 'rejilla_ms': 100,
    'rango': ['2026-06-29', '2026-10-26'], 'dias': cat}, indent=1, ensure_ascii=False))
print('LISTO', len(cat), 'días')
