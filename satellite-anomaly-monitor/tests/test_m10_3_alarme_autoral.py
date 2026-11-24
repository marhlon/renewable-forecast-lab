"""Contraprovas manuais da confirmação causal de inícios de alarme."""

import importlib.util
from pathlib import Path
import unittest

import numpy as np


PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "m10_3_alarme_autoral", PROJECT / "notebooks/m10_3_alarme_autoral.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
iniciar_alarmes = MODULE.iniciar_alarmes


class TestIniciarAlarmes(unittest.TestCase):
    def assert_starts(self, scores, usable, threshold, consecutive, expected):
        result = iniciar_alarmes(scores, usable, limiar=threshold, consecutivos=consecutive)
        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(result.dtype, np.dtype(bool))
        self.assertEqual(result.shape, np.shape(scores))
        self.assertEqual(np.flatnonzero(result).tolist(), expected)
        return result

    def test_devolutiva_nove_instantes_com_lacuna_finita(self):
        scores = np.array([.70, .80, .90, .95, .88, .89, .65, .71, .71])
        usable = np.ones(9, dtype=bool)
        usable[3] = False
        self.assert_starts(scores, usable, .70, 2, [1, 5, 8])

    def test_igualdade_ao_limiar_conta(self):
        self.assert_starts(np.array([.70, .70, .70]), np.ones(3, dtype=bool), .70, 2, [1])

    def test_queda_abaixo_do_limiar_reinicia(self):
        scores = np.array([.80, .69, .80, .80, .69, .80, .80])
        self.assert_starts(scores, np.ones(7, dtype=bool), .70, 2, [3, 6])

    def test_sequencia_longa_emite_um_unico_inicio(self):
        self.assert_starts(np.full(8, .90), np.ones(8, dtype=bool), .70, 2, [1])

    def test_confirmacao_unica_marca_primeiro_ponto_de_cada_sequencia(self):
        scores = np.array([.80, .90, .95, .60, .80, .90])
        self.assert_starts(scores, np.ones(6, dtype=bool), .70, 1, [0, 4])

    def test_tres_confirmacoes_sem_retroceder_carimbo(self):
        scores = np.array([.80, .80, .80, .80, .60, .80, .80, .80])
        self.assert_starts(scores, np.ones(8, dtype=bool), .70, 3, [2, 7])

    def test_lacunas_nan_e_nao_utilizavel_finito_reiniciam(self):
        scores = np.array([.80, np.nan, .80, .99, .80, .80])
        usable = np.array([True, False, True, False, True, True])
        self.assert_starts(scores, usable, .70, 2, [5])

    def test_argumentos_somente_leitura_sao_preservados(self):
        scores = np.array([.80, np.nan, .90, .95, .96])
        usable = np.array([True, False, True, True, True])
        before_scores, before_usable = scores.copy(), usable.copy()
        scores.flags.writeable = False
        usable.flags.writeable = False
        self.assert_starts(scores, usable, .70, 2, [3])
        np.testing.assert_array_equal(scores, before_scores)
        np.testing.assert_array_equal(usable, before_usable)
        self.assertFalse(scores.flags.writeable)
        self.assertFalse(usable.flags.writeable)

    def test_futuro_nao_altera_inicios_ja_emitidos(self):
        scores = np.array([.70, .80, .90, .95, .88, .89, .65, .71, .71])
        usable = np.ones(9, dtype=bool)
        usable[3] = False
        for consecutive in (1, 2, 3):
            full = iniciar_alarmes(scores, usable, limiar=.70, consecutivos=consecutive)
            for length in range(1, len(scores) + 1):
                with self.subTest(consecutivos=consecutive, prefixo=length):
                    prefix = iniciar_alarmes(
                        scores[:length], usable[:length], limiar=.70, consecutivos=consecutive
                    )
                    np.testing.assert_array_equal(prefix, full[:length])

    def test_sequencia_curta_nao_confirma(self):
        self.assert_starts(np.array([.90, .95]), np.ones(2, dtype=bool), .70, 3, [])


if __name__ == "__main__":
    unittest.main()
