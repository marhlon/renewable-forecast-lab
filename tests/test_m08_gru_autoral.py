"""Casos calculados à mão para as portas e a atualização de uma célula GRU."""

import unittest

import numpy as np

from notebooks.m08_gru_autoral import passo_gru


class PassoGruTest(unittest.TestCase):
    def test_exemplo_escalar_com_estado_nao_nulo(self):
        saida = passo_gru(
            np.zeros((1, 1)), np.array([[0.8]]),
            np.zeros((3, 1)), np.zeros((3, 1)),
            np.array([0.0, np.log(3.0), np.arctanh(-0.2)]), np.zeros(3),
        )
        for nome, valor in {"r": 0.5, "z": 0.75, "n": -0.2, "h": 0.55}.items():
            np.testing.assert_allclose(saida[nome], [[valor]], rtol=0, atol=1e-15)

    def test_portas_neutras_e_entradas_somente_leitura(self):
        h = np.arange(12, dtype=np.float64).reshape(4, 3) / 10.0
        entradas = [np.zeros((4, 2)), h, np.zeros((9, 2)),
                    np.zeros((9, 3)), np.zeros(9), np.zeros(9)]
        copias = [valor.copy() for valor in entradas]
        for valor in entradas:
            valor.setflags(write=False)
        saida = passo_gru(*entradas)
        self.assertEqual(set(saida), {"r", "z", "n", "h"})
        for valor in saida.values():
            self.assertEqual(valor.shape, (4, 3))
            self.assertEqual(valor.dtype, np.float64)
        np.testing.assert_array_equal(saida["r"], np.full((4, 3), 0.5))
        np.testing.assert_array_equal(saida["z"], np.full((4, 3), 0.5))
        np.testing.assert_array_equal(saida["n"], np.zeros((4, 3)))
        np.testing.assert_array_equal(saida["h"], h / 2)
        for antes, depois in zip(copias, entradas):
            np.testing.assert_array_equal(antes, depois)

    def test_reset_multiplica_afim_com_vies_depois_da_matriz(self):
        weight_hh = np.zeros((6, 2))
        weight_hh[4:] = [[1.0, 2.0], [-3.0, 4.0]]
        bias_ih = np.array([-np.log(3.0), np.log(3.0), 0., 0., 0., 0.])
        bias_hh = np.array([0., 0., 0., 0., 1., -2.])
        saida = passo_gru(np.zeros((1, 1)), np.array([[2., 3.]]),
                          np.zeros((6, 1)), weight_hh, bias_ih, bias_hh)
        np.testing.assert_allclose(saida["r"], [[0.25, 0.75]], atol=1e-15, rtol=0)
        # Termo recorrente [9,4], após reset [2.25,3].
        candidato = np.tanh([[2.25, 3.0]])
        np.testing.assert_allclose(saida["n"], candidato, atol=1e-15, rtol=0)
        np.testing.assert_allclose(saida["h"], 0.5 * candidato + [[1., 1.5]],
                                   atol=1e-15, rtol=0)

    def test_sigmoide_saturada_sem_overflow(self):
        with np.errstate(over="raise", invalid="raise"):
            saida = passo_gru(
                np.zeros((1, 1)), np.array([[0.4, 0.8]]),
                np.zeros((6, 1)), np.zeros((6, 2)),
                np.array([1000., -1000., -1000., 1000., 0., 0.]), np.zeros(6),
            )
        np.testing.assert_array_equal(saida["r"], [[1., 0.]])
        np.testing.assert_array_equal(saida["z"], [[0., 1.]])
        np.testing.assert_array_equal(saida["h"], [[0., 0.8]])

    def test_rejeita_dimensoes_incompativeis_e_valores_nao_finitos(self):
        validas = [np.zeros((2, 1)), np.zeros((2, 3)), np.zeros((9, 1)),
                   np.zeros((9, 3)), np.zeros(9), np.zeros(9)]
        for indice, invalida in ((0, np.zeros(2)), (1, np.zeros((1, 3))),
                                 (2, np.zeros((6, 1))), (3, np.zeros((9, 2))),
                                 (4, np.zeros((1, 9))), (5, np.full(9, np.nan))):
            with self.subTest(indice=indice):
                entradas = validas.copy()
                entradas[indice] = invalida
                with self.assertRaises(ValueError):
                    passo_gru(*entradas)


if __name__ == "__main__":
    unittest.main()
