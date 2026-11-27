"""Contas manuais e contraprovas do limite de confirmação, sem dados reais."""

import importlib.util
from pathlib import Path
import unittest

import numpy as np


PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "m10_4_limite_autoral", PROJECT / "notebooks/m10_4_limite_autoral.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
limite_confirmacao = MODULE.limite_confirmacao


class TestLimiteConfirmacao(unittest.TestCase):
    def assert_limit(self, scores, usable, k, expected_value, expected_end):
        result = limite_confirmacao(scores, usable, consecutivos=k)
        self.assertIsInstance(result, dict)
        self.assertEqual(set(result), {"limiar_maximo", "indice_confirmacao"})
        if expected_value is None:
            self.assertIsNone(result["limiar_maximo"])
            self.assertIsNone(result["indice_confirmacao"])
        else:
            self.assertAlmostEqual(result["limiar_maximo"], expected_value, places=12)
            self.assertEqual(result["indice_confirmacao"], expected_end)
            self.assertIsInstance(result["indice_confirmacao"], (int, np.integer))
            self.assertNotIsInstance(result["indice_confirmacao"], (bool, np.bool_))
        return result

    def test_exemplo_nove_posicoes_duas_confirmacoes(self):
        scores = np.array([.70, .80, .90, .95, .88, .89, .65, .71, .71])
        usable = np.array([True, True, True, False, True, True, True, True, True])
        self.assert_limit(scores, usable, 2, .88, 5)

    def test_exemplo_nove_posicoes_uma_confirmacao(self):
        scores = np.array([.70, .80, .90, .95, .88, .89, .65, .71, .71])
        usable = np.array([True, True, True, False, True, True, True, True, True])
        self.assert_limit(scores, usable, 1, .90, 2)

    def test_escores_negativos_nao_sao_substituidos_por_zero(self):
        scores = np.array([-8.0, -2.0, -3.0, -1.0])
        self.assert_limit(scores, np.ones(4, dtype=bool), 2, -3.0, 2)

    def test_empate_conserva_primeiro_indice_final(self):
        self.assert_limit(np.array([5.0, 7.0, 5.0]), np.ones(3, dtype=bool), 2, 5.0, 1)

    def test_lacuna_nao_pode_ser_filtrada_para_unir_horarios(self):
        self.assert_limit(np.array([1.0, 10.0, 2.0]), np.array([True, False, True]), 2, None, None)

    def test_nan_em_posicao_nao_utilizavel_e_ignorado(self):
        self.assert_limit(np.array([np.nan, 8.0, 1.0]), np.array([False, True, True]), 1, 8.0, 1)

    def test_vetor_vazio_nao_tem_janela(self):
        self.assert_limit(np.array([], dtype=float), np.array([], dtype=bool), 1, None, None)

    def test_k_maior_que_comprimento_nao_tem_janela(self):
        self.assert_limit(np.array([1.0]), np.array([True]), 3, None, None)

    def test_readonly_e_entradas_preservadas(self):
        scores = np.array([np.nan, -4.0, -2.0, -3.0, -1.0])
        usable = np.array([False, True, True, True, True])
        before_scores, before_usable = scores.copy(), usable.copy()
        scores.flags.writeable = False
        usable.flags.writeable = False
        self.assert_limit(scores, usable, 2, -3.0, 3)
        np.testing.assert_array_equal(scores, before_scores)
        np.testing.assert_array_equal(usable, before_usable)
        self.assertFalse(scores.flags.writeable)
        self.assertFalse(usable.flags.writeable)

    def test_empates_em_janelas_separadas_preservam_primeiro_fim(self):
        scores = np.array([3.0, 4.0, 1.0, 3.0, 4.0])
        self.assert_limit(scores, np.ones(5, dtype=bool), 2, 3.0, 1)

    def test_limite_e_fronteira_inclusiva_da_existencia_de_inicio(self):
        cases = [
            (np.array([1.0, 2.0, 3.0]), np.ones(3, dtype=bool), 2, 2.0),
            (np.array([-8.0, -2.0, -3.0, -1.0]), np.ones(4, dtype=bool), 2, -3.0),
            (np.array([.8, .9, .95]), np.ones(3, dtype=bool), 3, .8),
        ]

        def has_alarm(scores, usable, threshold, k):
            # Uma máquina de estado mede existência; não calcula mínimos de janelas.
            count = 0
            for score, valid in zip(scores, usable):
                count = count + 1 if valid and score >= threshold else 0
                if count == k:
                    return True
            return False

        for scores, usable, k, expected in cases:
            with self.subTest(escores=scores.tolist(), consecutivos=k):
                result = limite_confirmacao(scores, usable, consecutivos=k)
                self.assertEqual(result["limiar_maximo"], expected)
                self.assertTrue(has_alarm(scores, usable, expected, k))
                self.assertTrue(has_alarm(scores, usable, expected - 1.0, k))
                self.assertFalse(has_alarm(scores, usable, np.nextafter(expected, np.inf), k))

        separated = np.array([1.0, 10.0, 2.0])
        usable = np.array([True, False, True])
        self.assert_limit(separated, usable, 2, None, None)
        for threshold in (-100.0, 0.0, 1.0, 10.0):
            self.assertFalse(has_alarm(separated, usable, threshold, 2))


if __name__ == "__main__":
    unittest.main()
