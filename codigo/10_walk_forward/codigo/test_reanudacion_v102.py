#!/usr/bin/env python3
"""Comprueba que reanudar wf_v102.correr() reproduce eventos_v102.npy y por_dia_v102.json completos.
Sustituye ajustar/evaluar por versiones simuladas (sin datos ni ajustes): solo prueba el guardado y la reanudación.
Uso: python test_reanudacion_v102.py [ruta/eventos_v102.npy]   (con la ruta, reparte por días las filas reales; sin ella, sintéticas)"""
import shutil, sys, tempfile, types
from datetime import date, timedelta
from pathlib import Path
import numpy as np

def fechas(a, b):
    d, o = date.fromisoformat(a), []
    while d <= date.fromisoformat(b): o.append(d); d += timedelta(days=1)
    return o

sys.modules["test_v101"] = types.SimpleNamespace(M=None, V=None, C94=None, fechas=fechas)  # evita cargar datos al importar
sys.path.insert(0, str(Path(__file__).resolve().parent))
import wf_v102 as W  # noqa: E402

if len(sys.argv) > 1:
    REAL = np.load(sys.argv[1])
else:
    rng = np.random.default_rng(0)
    REAL = np.vstack([np.column_stack([np.full(n, k), rng.normal(size=(n, 26))]) for k, n in zip(range(1, 6), (40, 0, 75, 31, 58))])

def ajustar(fin):
    return None, None, None

def evaluar(MOD, deltas, cols, dias, k, tipo, evs):
    if evs is not None:  # un bloque por día, de tamaño desigual (algún día sin eventos)
        for bloque in np.array_split(REAL[REAL[:, 0] == k], len(dias)): evs.append(bloque)
    return [{"fecha": str(d), "n": 1, "fold": k, "tipo": tipo} for d in dias]

W.ajustar, W.evaluar = ajustar, evaluar

def corrida(sal):
    W.SAL, W.LOG[:] = sal, []
    W.correr()
    return np.load(sal / "eventos_v102.npy"), (sal / "por_dia_v102.json").read_text()

with tempfile.TemporaryDirectory() as tmp:
    a = Path(tmp) / "completa"; a.mkdir()
    E, F = corrida(a)
    assert np.array_equal(E, REAL, equal_nan=True), "la corrida completa no reproduce los eventos"
    for k in range(1, 6):
        assert np.array_equal(np.load(a / f"fold{k}_ev.npy"), REAL[REAL[:, 0] == k], equal_nan=True), f"fold{k}_ev.npy incompleto"
    for nombre, quitar in (("interrumpida tras la ventana 2", (3, 4, 5)), ("todas las ventanas guardadas", ())):
        b = Path(tmp) / nombre; shutil.copytree(a, b); (b / "eventos_v102.npy").unlink()
        for k in quitar: (b / f"fold{k}.json").unlink(); (b / f"fold{k}_ev.npy").unlink()
        E2, F2 = corrida(b)
        assert np.array_equal(E2, E, equal_nan=True) and F2 == F, f"reanudación ({nombre}) distinta de la corrida completa"
        print(f"ok: reanudación {nombre}: {len(E2)} filas, idénticas")
print(f"ok: {len(E)} filas; cada fold{{k}}_ev.npy contiene todos los días de su ventana")
