"""Contraprovas do sincronizador, com resultados manuais e sem dados ESA."""

import importlib.util
from pathlib import Path
import unittest

import numpy as np
import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "m10_sincronizacao_autoral", PROJECT / "notebooks/m10_sincronizacao_autoral.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
sincronizar_causal = MODULE.sincronizar_causal


class TestSincronizarCausal(unittest.TestCase):
    def setUp(self):
        self.t = pd.Timestamp("2007-01-01T00:00:00Z")

    def times(self, seconds):
        return pd.DatetimeIndex([self.t + pd.Timedelta(seconds=s) for s in seconds])

    def source(self, seconds, values, **kwargs):
        return pd.DataFrame({"timestamp": self.times(seconds), "value": values}, **kwargs)

    def test_sem_amostra_anterior_nao_busca_futuro(self):
        result = sincronizar_causal(
            {"c": self.source([10], [8.0])}, self.times([5, 10]), pd.Timedelta(seconds=30)
        )
        self.assertTrue(pd.isna(result.loc[0, "c_sample_time"]))
        self.assertTrue(np.isnan(result.loc[0, "c_age_seconds"]))
        self.assertTrue(np.isnan(result.loc[0, "c_value"]))
        self.assertFalse(result.loc[0, "c_usable"])
        self.assertEqual(result.loc[1, "c_sample_time"], self.t + pd.Timedelta(seconds=10))
        self.assertEqual(result.loc[1, "c_value"], 8.0)
        self.assertTrue(result.loc[1, "c_usable"])

    def test_nan_na_ultima_medicao_nao_recupera_valor_antigo(self):
        source = self.source([0, 10, 20], [4.0, np.nan, 6.0])
        result = sincronizar_causal({"c": source}, self.times([12, 22]), pd.Timedelta(seconds=30))
        self.assertEqual(result.loc[0, "c_sample_time"], self.t + pd.Timedelta(seconds=10))
        self.assertEqual(result.loc[0, "c_age_seconds"], 2.0)
        self.assertTrue(np.isnan(result.loc[0, "c_value"]))
        self.assertFalse(result.loc[0, "c_usable"])
        self.assertEqual(result.loc[1, "c_value"], 6.0)
        self.assertTrue(result.loc[1, "c_usable"])

    def test_expiracao_preserva_evidencia_e_zero_e_valido(self):
        result = sincronizar_causal(
            {"c": self.source([0, 10], [0.0, 10.0])},
            self.times([2, 7, 12]), pd.Timedelta(seconds=5)
        )
        np.testing.assert_allclose(result.c_value, [0.0, np.nan, 10.0], equal_nan=True)
        np.testing.assert_allclose(result.c_age_seconds, [2.0, 7.0, 2.0])
        self.assertEqual(result.c_usable.tolist(), [True, False, True])
        self.assertEqual(result.c_sample_time.iloc[1], self.t)

    def test_limite_de_180_segundos_e_inclusivo(self):
        result = sincronizar_causal(
            {"c": self.source([0], [2.0])}, self.times([0, 180, 181]), pd.Timedelta(seconds=180)
        )
        np.testing.assert_allclose(result.c_value, [2.0, 2.0, np.nan], equal_nan=True)
        np.testing.assert_allclose(result.c_age_seconds, [0.0, 180.0, 181.0])
        self.assertEqual(result.c_usable.tolist(), [True, True, False])
        self.assertTrue(result.c_sample_time.eq(self.t).all())

    def test_tolerancia_zero_exige_amostra_exata(self):
        result = sincronizar_causal(
            {"c": self.source([0], [3.0])}, self.times([0, 1]), pd.Timedelta(0)
        )
        self.assertEqual(result.c_usable.tolist(), [True, False])
        self.assertEqual(result.loc[0, "c_value"], 3.0)
        self.assertTrue(np.isnan(result.loc[1, "c_value"]))
        self.assertEqual(result.loc[1, "c_age_seconds"], 1.0)
        self.assertEqual(result.loc[1, "c_sample_time"], self.t)

    def test_preserva_entradas_desordenadas_e_indice_original(self):
        source = self.source([10, 0], [10.0, 0.0], index=[80, 20])
        source.index.name = "medicao"
        grade = self.times([2, 12]).rename("decisao")
        before_source = source.copy(deep=True)
        before_grade = grade.copy(deep=True)
        tables = {"c": source}
        result = sincronizar_causal(tables, grade, pd.Timedelta(seconds=5))
        pd.testing.assert_frame_equal(source, before_source)
        pd.testing.assert_index_equal(grade, before_grade)
        self.assertIs(tables["c"], source)
        self.assertEqual(list(tables), ["c"])
        np.testing.assert_allclose(result.c_value, [0.0, 10.0])
        self.assertEqual(result.timestamp.tolist(), grade.tolist())

    def test_canais_assincronos_e_perturbacao_do_futuro(self):
        c = self.source([0, 10], [0.0, 10.0])
        d = self.source([1, 11], [100.0, 200.0])
        grade, tolerance = self.times([2, 7, 12]), pd.Timedelta(seconds=5)
        result = sincronizar_causal({"c": c, "d": d}, grade, tolerance)
        np.testing.assert_allclose(result.d_value, [100.0, np.nan, 200.0], equal_nan=True)
        np.testing.assert_allclose(result.d_age_seconds, [1.0, 6.0, 1.0])
        c_changed, d_changed = c.copy(deep=True), d.copy(deep=True)
        c_changed.loc[1, "value"], d_changed.loc[1, "value"] = 999.0, -999.0
        after = sincronizar_causal({"c": c_changed, "d": d_changed}, grade, tolerance)
        pd.testing.assert_frame_equal(result.iloc[:2], after.iloc[:2])
        self.assertEqual(after.loc[2, "c_value"], 999.0)
        self.assertEqual(after.loc[2, "d_value"], -999.0)

    def test_ordem_das_colunas_segue_os_canais(self):
        source = self.source([0], [1.0])
        result = sincronizar_causal({"z": source, "a": source}, self.times([0]), pd.Timedelta(0))
        self.assertEqual(result.columns.tolist(), [
            "timestamp", "z_value", "z_sample_time", "z_age_seconds", "z_usable",
            "a_value", "a_sample_time", "a_age_seconds", "a_usable",
        ])

    def test_fusos_distintos_representam_o_mesmo_instante(self):
        source = pd.DataFrame({
            "timestamp": pd.DatetimeIndex(["2006-12-31T21:00:00-03:00"]), "value": [7.0]
        })
        grade = self.times([0, 1])
        before = source.copy(deep=True)
        result = sincronizar_causal({"c": source}, grade, pd.Timedelta(seconds=1))
        self.assertTrue(result.c_sample_time.eq(self.t).all())
        self.assertEqual(result.c_value.tolist(), [7.0, 7.0])
        self.assertEqual(result.c_age_seconds.tolist(), [0.0, 1.0])
        pd.testing.assert_frame_equal(source, before)

    def test_entradas_invalidas_sao_rejeitadas(self):
        source, grade, tolerance = self.source([0, 10], [0.0, 10.0]), self.times([2, 7, 12]), pd.Timedelta(seconds=5)
        duplicate = pd.concat([source, source.iloc[:1]])
        naive_source = source.copy(deep=True)
        naive_source.timestamp = naive_source.timestamp.dt.tz_localize(None)
        nat_source = source.copy(deep=True)
        nat_source.loc[1, "timestamp"] = pd.NaT
        invalid = [
            (duplicate, grade, tolerance, "amostras duplicadas"),
            (source, grade[::-1], tolerance, "grade invertida"),
            (source, self.times([2, 2]), tolerance, "grade duplicada"),
            (naive_source, grade, tolerance, "amostra sem fuso"),
            (source, grade.tz_localize(None), tolerance, "grade sem fuso"),
            (nat_source, grade, tolerance, "amostra NaT"),
            (source, pd.DatetimeIndex([self.t, pd.NaT]), tolerance, "grade NaT"),
            (source, grade, pd.Timedelta(seconds=-1), "tolerancia negativa"),
            (source, grade, pd.NaT, "tolerancia NaT"),
        ]
        for data, times, tol, name in invalid:
            with self.subTest(case=name), self.assertRaises((ValueError, TypeError)):
                sincronizar_causal({"c": data}, times, tol)


if __name__ == "__main__":
    unittest.main()
