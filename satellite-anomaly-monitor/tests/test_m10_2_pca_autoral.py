"""Contas manuais do resíduo PCA; sem ajuste e sem implementação de referência."""

import importlib.util
from pathlib import Path
import unittest

import numpy as np


PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "m10_2_pca_autoral", PROJECT / "notebooks/m10_2_pca_autoral.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
erro_pca_por_amostra = MODULE.erro_pca_por_amostra


class TestErroPcaPorAmostra(unittest.TestCase):
    def test_conta_manual_com_centro_nao_zero(self):
        result = erro_pca_por_amostra(
            np.array([[3.0, 1.0]]), np.array([1.0, 0.0]), np.array([[0.0, 1.0]])
        )
        np.testing.assert_allclose(result, [4.0], rtol=0, atol=1e-12)
        self.assertEqual(np.shape(result), (1,))

    def test_base_retangular_rotacionada(self):
        center = np.array([2.0, -1.0, 4.0])
        components = np.array([[1 / np.sqrt(2), 1 / np.sqrt(2), 0], [0, 0, 1]])
        x = center + np.array([[3.0, 3.0, 7.0], [2.0, -2.0, 4.0], [-1.0, 1.0, 0.0]])
        # O plano retém a diagonal dos dois primeiros canais e todo o terceiro.
        # Sobram (0,0,0), (2,-2,0) e (-1,1,0): energias 0, 8 e 2.
        result = erro_pca_por_amostra(x, center, components)
        np.testing.assert_allclose(result, [0.0, 8.0, 2.0], rtol=0, atol=1e-12)
        self.assertEqual(np.shape(result), (3,))

    def test_escore_e_soma_por_linha_nao_media_ou_escore_global(self):
        x = np.array([[100.0, 2.0, 3.0], [-100.0, 4.0, -5.0], [0.0, 0.0, 0.0]])
        result = erro_pca_por_amostra(x, np.zeros(3), np.array([[1.0, 0.0, 0.0]]))
        np.testing.assert_allclose(result, [13.0, 41.0, 0.0], rtol=0, atol=1e-12)
        self.assertEqual(np.shape(result), (3,))

    def test_centro_do_ajuste_e_reutilizado_em_cada_batch(self):
        x = np.array([[1.0, 20.0], [2.0, 20.0]])
        center = np.array([0.0, 10.0])
        components = np.array([[1.0, 0.0]])
        together = erro_pca_por_amostra(x, center, components)
        separate = np.concatenate([
            erro_pca_por_amostra(x[:1], center, components),
            erro_pca_por_amostra(x[1:], center, components),
        ])
        # Recentrar pela média do batch apagaria o deslocamento 20 - 10.
        np.testing.assert_allclose(together, [100.0, 100.0], rtol=0, atol=1e-12)
        np.testing.assert_allclose(separate, together, rtol=0, atol=1e-12)

    def test_entradas_readonly_permanecem_inalteradas(self):
        # View não contígua: a função deve calcular sem editar sua entrada.
        storage = np.array([[3.0, 70.0, 1.0, 80.0], [4.0, 90.0, 2.0, 100.0]])
        x = storage[:, ::2]
        center = np.array([1.0, 0.0])
        components = np.array([[0.0, 1.0]])
        before = [a.copy() for a in (x, center, components)]
        for array in (x, center, components):
            array.flags.writeable = False
        result = erro_pca_por_amostra(x, center, components)
        np.testing.assert_allclose(result, [4.0, 9.0], rtol=0, atol=1e-12)
        for array, original in zip((x, center, components), before):
            np.testing.assert_array_equal(array, original)
            self.assertFalse(array.flags.writeable)

    def test_translacao_congruente_nao_muda_residuo(self):
        center = np.array([2.0, -1.0, 4.0])
        x = center + np.array([[3.0, 3.0, 7.0], [2.0, -2.0, 4.0]])
        components = np.array([[1 / np.sqrt(2), 1 / np.sqrt(2), 0], [0, 0, 1]])
        shift = np.array([500.0, -37.0, 12.0])
        original = erro_pca_por_amostra(x, center, components)
        translated = erro_pca_por_amostra(x + shift, center + shift, components)
        np.testing.assert_allclose(original, [0.0, 8.0], rtol=0, atol=1e-12)
        np.testing.assert_allclose(translated, original, rtol=0, atol=1e-12)

    def test_transferencia_duas_componentes_retidas(self):
        x = np.array([[3.0, 3.0, 3.0], [1.0, 1.0, -2.0]])
        components = np.array([
            np.array([1.0, 1.0, 1.0]) / np.sqrt(3),
            np.array([1.0, -1.0, 0.0]) / np.sqrt(2),
        ])
        result = erro_pca_por_amostra(x, np.zeros(3), components)
        # A pertence ao plano; B é perpendicular a ambas as direções.
        np.testing.assert_allclose(result, [0.0, 6.0], rtol=0, atol=1e-12)

    def test_transferencia_base_completa_reconstroi_os_dois_pontos(self):
        x = np.array([[3.0, 3.0, 3.0], [1.0, 1.0, -2.0]])
        components = np.array([
            np.array([1.0, 1.0, 1.0]) / np.sqrt(3),
            np.array([1.0, -1.0, 0.0]) / np.sqrt(2),
            np.array([1.0, 1.0, -2.0]) / np.sqrt(6),
        ])
        result = erro_pca_por_amostra(x, np.zeros(3), components)
        np.testing.assert_allclose(result, [0.0, 0.0], rtol=0, atol=1e-12)


if __name__ == "__main__":
    unittest.main()
