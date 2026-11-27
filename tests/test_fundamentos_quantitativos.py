"""Contas pequenas e contratos numéricos dos laboratórios sintéticos M02."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

import numpy as np


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "notebooks"))
from laboratorio_probabilidade import (
    intervalos_normais, momentos_discretos, probabilidade_positiva,
    tamanho_efetivo_ar1, teste_melhoria_blocos,
)
from laboratorio_regressao_fundamentos import (
    ajustar_linear, diagnosticar_residuos, matriz_design, objetivo_gradiente,
)


class FundamentosTest(unittest.TestCase):
    def test_bayes_nao_inverte_a_condicao(self):
        self.assertAlmostEqual(probabilidade_positiva(.01, .9, .05), 90 / 585, places=14)
        self.assertLess(probabilidade_positiva(.01, .9, .05), .9)
        self.assertGreater(probabilidade_positiva(.1, .9, .05), probabilidade_positiva(.01, .9, .05))

    def test_probabilidade_invalida_e_evento_condicionante_nulo(self):
        for args in ((-.1, .9, .05), (.01, 1.1, .05), (0, .9, 0), (np.nan, .9, .05)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                probabilidade_positiva(*args)

    def test_momentos_discretos_conta_manual(self):
        mean, variance = momentos_discretos([0, 1, 2], [.5, .3, .2])
        self.assertAlmostEqual(mean, .7)
        self.assertAlmostEqual(variance, .61)

    def test_distribuicao_incompleta_nao_e_normalizada_silenciosamente(self):
        with self.assertRaises(ValueError):
            momentos_discretos([0, 1], [.4, .4])
        with self.assertRaises(ValueError):
            momentos_discretos([0, 1], [-.1, 1.1])

    def test_ic_media_e_pi_tem_alvos_e_larguras_distintos(self):
        result = intervalos_normais([8, 10, 12])
        self.assertEqual(result["media"], 10)
        self.assertEqual(result["variancia_n_menos_1"], 4)
        self.assertAlmostEqual(result["erro_padrao"], 2 / np.sqrt(3))
        self.assertAlmostEqual(result["t_critico"], 4.3026527299, places=8)
        ci_half = result["ic_media_superior"] - result["media"]
        pi_half = result["pi_observacao_superior"] - result["media"]
        self.assertAlmostEqual(pi_half / ci_half, 2)

    def test_intervalo_nao_aceita_coluna_ou_n_unitario(self):
        for values in ([2], [[1], [2]], [1, np.nan]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                intervalos_normais(values)

    def test_n_efetivo_casos_de_covariancia_conhecida(self):
        self.assertEqual(tamanho_efetivo_ar1(12, 0), 12)
        self.assertAlmostEqual(tamanho_efetivo_ar1(2, .5), 2 / 1.5)
        self.assertLess(tamanho_efetivo_ar1(48, .8), 48)

    def test_teste_por_blocos_preserva_media_e_usa_numero_de_blocos(self):
        d = np.array([0., 2., 1., 3.])
        before = d.copy()
        result = teste_melhoria_blocos(d, tamanho_bloco=2, efeito_minimo=0., alpha=.05)
        self.assertEqual(result["n_blocos"], 2)
        self.assertEqual(result["media_diferenca"], 1.5)
        self.assertAlmostEqual(result["erro_padrao_blocos"], .5)
        self.assertAlmostEqual(result["t"], 3)
        np.testing.assert_array_equal(d, before)

    def test_h0_incorpora_o_efeito_minimo_e_nao_apenas_zero(self):
        d = [0., 2., 1., 3., 2., 4.]
        zero = teste_melhoria_blocos(d, tamanho_bloco=2, efeito_minimo=0., alpha=.05)
        one = teste_melhoria_blocos(d, tamanho_bloco=2, efeito_minimo=1., alpha=.05)
        self.assertGreater(one["p_unilateral"], zero["p_unilateral"])
        self.assertFalse(one["rejeita_h0"])

    def test_lacuna_de_bloco_nao_e_descartada_para_caber_o_teste(self):
        with self.assertRaises(ValueError):
            teste_melhoria_blocos([1, 2, 3], tamanho_bloco=2, efeito_minimo=0., alpha=.05)
        with self.assertRaises(ValueError):
            teste_melhoria_blocos([2, 2, 2, 2], tamanho_bloco=2, efeito_minimo=0., alpha=.05)

    def test_ols_e_ridge_conferem_com_conta_manual(self):
        x = matriz_design([-1, 0, 1])
        y = np.array([1., 2., 4.])
        np.testing.assert_allclose(ajustar_linear(x, y), [7 / 3, 3 / 2], atol=1e-12)
        np.testing.assert_allclose(ajustar_linear(x, y, regularizacao=1 / 3), [7 / 3, 1], atol=1e-12)

    def test_gradiente_fora_do_otimo_por_diferencas_finitas(self):
        x = matriz_design([-1, 0, 1])
        y = np.array([1., 2., 4.])
        beta = np.array([.3, -.4])
        for regularization in (0., .3):
            with self.subTest(regularization=regularization):
                _, gradient = objetivo_gradiente(x, y, beta, regularizacao=regularization)
                numerical = np.empty(2)
                for j in range(2):
                    increment = np.eye(2)[j] * 1e-6
                    high = objetivo_gradiente(x, y, beta + increment, regularizacao=regularization)[0]
                    low = objetivo_gradiente(x, y, beta - increment, regularizacao=regularization)[0]
                    numerical[j] = (high - low) / 2e-6
                np.testing.assert_allclose(gradient, numerical, rtol=0, atol=1e-8)

    def test_intercepto_nao_e_penalizado(self):
        x = matriz_design([-1, 0, 1])
        y = np.array([1., 2., 4.])
        beta = np.array([2., 3.])
        _, g0 = objetivo_gradiente(x, y, beta)
        _, g1 = objetivo_gradiente(x, y, beta, regularizacao=.5)
        np.testing.assert_allclose(g1 - g0, [0, 3], atol=1e-12)

    def test_shapes_invalidos_nao_criam_broadcast_n_por_n(self):
        x = matriz_design([-1, 0, 1])
        with self.assertRaises(ValueError):
            ajustar_linear(x, np.array([[1.], [2.], [4.]]))
        with self.assertRaises(ValueError):
            objetivo_gradiente(x, [1, 2, 4], [[.3], [-.4]])

    def test_posto_deficiente_nao_identifica_coeficientes_separados(self):
        x = matriz_design(np.array([[-1, -2], [0, 0], [1, 2]]))
        beta = ajustar_linear(x, [1, 2, 4])
        self.assertEqual(np.linalg.matrix_rank(x), 2)
        np.testing.assert_allclose(x @ beta, x @ (beta + [0, 2, -1]), atol=1e-12)

    def test_entradas_preservadas_em_ajuste_e_objetivo(self):
        x = matriz_design([-1, 0, 1])
        y = np.array([1., 2., 4.])
        beta = np.array([.3, -.4])
        before = deepcopy((x, y, beta))
        ajustar_linear(x, y, regularizacao=.2)
        objetivo_gradiente(x, y, beta, regularizacao=.2)
        for got, original in zip((x, y, beta), before):
            np.testing.assert_array_equal(got, original)

    def test_residuos_constantes_nao_fabricam_correlacao(self):
        result = diagnosticar_residuos([1, 2, 3], [1, 2, 3])
        self.assertEqual(result["rmse"], 0)
        self.assertIsNone(result["autocorrelacao_lag1"])
        self.assertIsNone(result["durbin_watson_descritivo"])


if __name__ == "__main__":
    unittest.main()
