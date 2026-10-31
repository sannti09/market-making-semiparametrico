#!/usr/bin/env python3
"""Comprueba que reanudar wf_v102.correr() reproduce eventos_v102.npy y por_dia_v102.json completos.
Sustituye ajustar/evaluar por versiones simuladas (sin datos ni ajustes): solo prueba el guardado y la reanudación.
Uso: python test_reanudacion_v102.py [ruta/eventos_v102.npy]   (con la ruta, reparte por días las filas reales; sin ella, sintéticas)"""
import json, shutil, sys, tempfile, types
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

AJUSTADOS = []
def ajustar(fin):
    AJUSTADOS.append(next(k for k, fold in enumerate(W.FOLDS, 1) if fold[0] == fin))
    return None, None, None

def evaluar(MOD, deltas, cols, dias, k, tipo, evs):
    if evs is not None:  # un bloque por día, de tamaño desigual (algún día sin eventos)
        for bloque in np.array_split(REAL[REAL[:, 0] == k], len(dias)): evs.append(bloque)
    return [{"fecha": str(d), "n": 1, "fold": k, "tipo": tipo} for d in dias]

W.ajustar, W.evaluar = ajustar, evaluar

def corrida(sal):
    W.SAL, W.LOG[:] = sal, []; AJUSTADOS.clear()
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
    # Todos los checkpoints existen, pero se interrumpió antes del agregado final.
    for nombre in ("agregado ausente", "agregado desactualizado", "eventos agregados truncados"):
        b = Path(tmp) / nombre; shutil.copytree(a, b)
        if nombre == "agregado ausente":
            (b / "por_dia_v102.json").unlink()
        elif nombre == "agregado desactualizado":
            parcial = [r for r in json.loads(F) if r["fold"] < 5]
            (b / "por_dia_v102.json").write_text(json.dumps(parcial))
        else:
            (b / "eventos_v102.npy").write_bytes(b"interrumpido")
        E2, F2 = corrida(b)
        assert np.array_equal(E2, E, equal_nan=True) and F2 == F, nombre
        assert AJUSTADOS == [], f"{nombre}: no debe volver a entrenar ventanas válidas"
        print(f"ok: {nombre}: ambos agregados reconstruidos sin ajustes")
    # Una pareja parcial, corrupta o de otra ventana se reconstruye por completo.
    for nombre, k in (("NPY ausente", 1), ("JSON ausente", 3), ("JSON corrupto", 3),
                      ("NPY corrupto", 4), ("filas incompletas", 4), ("eventos de otra ventana", 5)):
        b = Path(tmp) / nombre; shutil.copytree(a, b)
        if nombre == "NPY ausente": (b / f"fold{k}_ev.npy").unlink()
        elif nombre == "JSON ausente": (b / f"fold{k}.json").unlink()
        elif nombre == "JSON corrupto": (b / f"fold{k}.json").write_text("{")
        elif nombre == "NPY corrupto": (b / f"fold{k}_ev.npy").write_bytes(b"interrumpido")
        elif nombre == "filas incompletas":
            filas = json.loads((b / f"fold{k}.json").read_text())
            (b / f"fold{k}.json").write_text(json.dumps(filas[:-1]))
        else:
            ev = np.load(b / f"fold{k}_ev.npy"); ev[:, 0] = 1
            np.save(b / f"fold{k}_ev.npy", ev)
        E2, F2 = corrida(b)
        assert np.array_equal(E2, E, equal_nan=True) and F2 == F, nombre
        assert AJUSTADOS == [k], f"{nombre}: solo debe reconstruirse la ventana {k}"
        print(f"ok: {nombre}: ventana {k} reconstruida y resto reutilizado")
print(f"ok: {len(E)} filas; cada fold{{k}}_ev.npy contiene todos los días de su ventana")
