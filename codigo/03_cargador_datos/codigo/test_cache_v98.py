"""Regresión de la caché de bins: python -m unittest test_cache_v98 -v.

No lee datos de mercado: solo sustituye el constructor de bins, conservando
la lectura, validación y publicación de la caché reales.
"""
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import numpy as np

import cargador_v98 as N


class TestCache(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cac = Path(self.tmp.name)
        self.d = date(2026, 7, 1)
        self.path = self.cac / f"bins_{self.d}.npz"
        self.cache_patch = patch.object(N, "CAC", self.cac)
        self.cache_patch.start(); self.addCleanup(self.cache_patch.stop)
        constructor_patch = patch.object(N, "construir", side_effect=self.fixture)
        self.constructor = constructor_patch.start(); self.addCleanup(constructor_patch.stop)

    @staticmethod
    def fixture(d, deltas):
        deltas = np.asarray(deltas, float)
        y = np.broadcast_to(deltas, (2, len(deltas))).copy()
        return {"t_ms": np.array([0, 1000]), "X": np.array([[1.], [2.]]),
                "hora_utc": np.array([0, 0]), "exposicion_s": np.ones(2),
                "deltas_bps": deltas, "conteos": {"ask": y, "bid": y.copy()},
                "columnas_x": ["x"]}

    def test_reutiliza_solo_rejilla_equivalente(self):
        a = N.bins(self.d, [1, .5, 1]); b = N.bins(self.d, [.5, 1])
        self.assertEqual(self.constructor.call_count, 1)
        np.testing.assert_array_equal(a["conteos"]["ask"], b["conteos"]["ask"])
        np.testing.assert_array_equal(b["deltas_bps"], [.5, 1])

    def test_cambio_de_distancias_con_igual_longitud(self):
        N.bins(self.d, [.5, 1]); b = N.bins(self.d, [2, 3])
        self.assertEqual(self.constructor.call_count, 2)
        np.testing.assert_array_equal(b["deltas_bps"], [2, 3])
        np.testing.assert_array_equal(b["conteos"]["ask"], [[2, 3], [2, 3]])
        np.testing.assert_array_equal(N.bins(self.d, [2, 3])["deltas_bps"], [2, 3])
        self.assertEqual(self.constructor.call_count, 2)

    def test_cache_truncada_se_reconstruye(self):
        self.path.write_bytes(b"PK\x03\x04archivo incompleto")
        b = N.bins(self.d, [.5, 1])
        self.assertEqual(self.constructor.call_count, 1)
        np.testing.assert_array_equal(b["deltas_bps"], [.5, 1])

    def test_columnas_de_conteos_incompatibles(self):
        N.bins(self.d, [.5, 1])
        with np.load(self.path) as z:
            arrays = dict(z)
        arrays["c_ask"] = arrays["c_ask"][:, :1]
        np.savez(self.path, **arrays)
        b = N.bins(self.d, [.5, 1])
        self.assertEqual(self.constructor.call_count, 2)
        self.assertEqual(b["conteos"]["ask"].shape, (2, 2))

    def test_escritura_fallida_preserva_archivo_anterior(self):
        N.bins(self.d, [.5, 1]); anterior = self.path.read_bytes()
        with patch.object(N.np, "savez", side_effect=OSError("disco lleno")):
            with self.assertRaises(OSError): N.bins(self.d, [2, 3])
        self.assertEqual(self.path.read_bytes(), anterior)
        self.assertEqual(list(self.cac.glob("*.tmp")), [])
        np.testing.assert_array_equal(N.bins(self.d, [2, 3])["deltas_bps"], [2, 3])

    def test_rechaza_distancias_vacias_o_no_finitas(self):
        for deltas in ([], [float("nan")], [float("inf")]):
            with self.assertRaises(ValueError): N.bins(self.d, deltas)
        self.constructor.assert_not_called()


if __name__ == "__main__":
    unittest.main()
