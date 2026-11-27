"""Contas pequenas de top-k, sem pesos, geração ou implementação de referência."""

import importlib.util
import math
from pathlib import Path
import unittest

import numpy as np


PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "m11_1_amostragem_autoral", PROJECT / "notebooks/m11_1_amostragem_autoral.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
selecionar_token_top_k = MODULE.selecionar_token_top_k


class TestSelecionarTokenTopK(unittest.TestCase):
    def assert_token(self, logits, *, temperatura, k, u, expected):
        token = selecionar_token_top_k(logits, temperatura=temperatura, k=k, u=u)
        self.assertIs(type(token), int)
        self.assertEqual(token, expected)
        return token

    def test_empate_no_corte_prioriza_menores_ids(self):
        self.assert_token((0.0, 0.0, 0.0), temperatura=1.0, k=2, u=0.0, expected=0)
        self.assert_token((0.0, 0.0, 0.0), temperatura=1.0, k=2,
                          u=math.nextafter(1.0, 0.0), expected=1)

    def test_fronteira_exata_da_cdf_vai_para_proxima_massa(self):
        self.assert_token((0.0, 0.0, 0.0), temperatura=1.0, k=2, u=0.5, expected=1)

    def test_exponenciais_estaveis_e_temperatura_mudam_escolha(self):
        logits = (-100.0, 1000.0, 999.0)
        self.assert_token(logits, temperatura=1.0, k=2, u=0.8, expected=2)
        self.assert_token(logits, temperatura=0.5, k=2, u=0.8, expected=1)

    def test_top_um_so_pode_escolher_o_maior_logit(self):
        for u in (0.0, 0.5, 0.999, math.nextafter(1.0, 0.0)):
            with self.subTest(u=u):
                self.assert_token((-100.0, 1000.0, 999.0), temperatura=9.0, k=1,
                                  u=u, expected=1)

    def test_underflow_nao_concede_massa_a_candidatos_zero(self):
        for u in (0.0, 0.9, 0.999999, math.nextafter(1.0, 0.0)):
            with self.subTest(u=u):
                self.assert_token((1000.0, -2000.0, -4000.0), temperatura=1.0, k=3,
                                  u=u, expected=0)

    def test_fallback_perto_de_um_usa_ultimo_peso_positivo(self):
        logits = (0.0, -37.0, -37.0, -37.0, -37.0, -1000.0)
        weights = [math.exp(value) for value in logits]
        u = math.nextafter(1.0, 0.0)
        # fsum preserva a massa minúscula que uma soma sequencial pode perder.
        sequential = 0.0
        for weight in weights:
            sequential += weight
        self.assertGreater(u * math.fsum(weights), sequential)
        self.assertEqual(weights[-1], 0.0)
        self.assertGreater(weights[-2], 0.0)
        self.assert_token(logits, temperatura=1.0, k=6, u=u, expected=4)

    def test_tupla_e_lista_permanecem_inalteradas(self):
        original = (-100.0, 1000.0, 999.0)
        as_list = list(original)
        self.assert_token(original, temperatura=1.0, k=2, u=0.8, expected=2)
        self.assert_token(as_list, temperatura=1.0, k=2, u=0.8, expected=2)
        self.assertEqual(original, (-100.0, 1000.0, 999.0))
        self.assertEqual(as_list, list(original))

    def test_array_somente_leitura_e_id_python_int(self):
        logits = np.array([-100.0, 1000.0, 999.0])
        before = logits.copy()
        logits.flags.writeable = False
        self.assert_token(logits, temperatura=1.0, k=2, u=0.8, expected=2)
        np.testing.assert_array_equal(logits, before)
        self.assertFalse(logits.flags.writeable)

    def test_translacao_constante_dos_logits_preserva_escolha(self):
        logits = (-3.0, 0.0, 5.0, 4.0)
        for temperature in (0.5, 1.0):
            for u in (0.0, 0.25, 0.5, 0.9, math.nextafter(1.0, 0.0)):
                original = selecionar_token_top_k(logits, temperatura=temperature, k=3, u=u)
                for shift in (-1000.0, 1000.0):
                    with self.subTest(temperatura=temperature, u=u, deslocamento=shift):
                        translated = tuple(value + shift for value in logits)
                        self.assert_token(translated, temperatura=temperature, k=3,
                                          u=u, expected=original)

    def test_k_fora_do_contrato_e_rejeitado(self):
        for k in (0, -1, 4, 1.5, True, np.int64(2)):
            with self.subTest(k=repr(k)), self.assertRaises(ValueError):
                selecionar_token_top_k((1.0, 2.0, 3.0), temperatura=1.0, k=k, u=0.5)

    def test_temperatura_fora_do_contrato_e_rejeitada(self):
        for temperature in (0.0, -1.0, math.nan, math.inf, -math.inf):
            with self.subTest(temperatura=temperature), self.assertRaises(ValueError):
                selecionar_token_top_k((1.0, 2.0, 3.0), temperatura=temperature, k=2, u=0.5)

    def test_uniforme_fora_do_intervalo_e_rejeitada(self):
        for u in (-0.01, 1.0, math.nan, math.inf, -math.inf):
            with self.subTest(u=u), self.assertRaises(ValueError):
                selecionar_token_top_k((1.0, 2.0, 3.0), temperatura=1.0, k=2, u=u)

    def test_logits_vazios_ou_nao_finitos_sao_rejeitados(self):
        for logits in ((), (math.nan, 0.0), (math.inf, 0.0), (-math.inf, 0.0)):
            with self.subTest(logits=logits), self.assertRaises(ValueError):
                selecionar_token_top_k(logits, temperatura=1.0, k=1, u=0.5)


if __name__ == "__main__":
    unittest.main()
