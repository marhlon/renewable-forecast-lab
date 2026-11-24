"""Contraprovas de calendário, eixos e níveis na seleção dos quantis."""

from datetime import datetime, timezone
import unittest

import numpy as np

from notebooks.m09_alinhamento_autoral import alinhar_quantis


class AlinhamentoQuantisTest(unittest.TestCase):
    def setUp(self):
        self.niveis = np.array([0.1, 0.5, 0.9], dtype=np.float64)
        self.fim = np.array(["2026-07-03T02:00:00"], dtype="datetime64[ns]")
        self.alvo = self.fim + np.timedelta64(1, "h")

    def test_leads_por_exemplo_e_indices_primeiro_ultimo(self):
        niveis = np.array([.01, .1, .25, .5, .75, .9, .99])
        batch, quantil, passo = np.indices((4, 7, 30))
        forecast = (10000 * batch + 100 * quantil + passo).astype(np.float64)
        fim = np.full(4, np.datetime64("2026-07-03T02:00:00", "ns"))
        leads = np.array([26, 5, 1, 30])
        alvos = fim + leads.astype("timedelta64[h]")
        resultado = alinhar_quantis(forecast, niveis, fim, alvos)
        self.assertEqual(set(resultado), {"lead_hours", "index_zero_based", "p10", "p50", "p90"})
        for valor in resultado.values():
            self.assertIsInstance(valor, np.ndarray)
            self.assertEqual(valor.shape, (4,))
        np.testing.assert_array_equal(resultado["lead_hours"], [26, 5, 1, 30])
        np.testing.assert_array_equal(resultado["index_zero_based"], [25, 4, 0, 29])
        np.testing.assert_array_equal(resultado["p10"], [125., 10104., 20100., 30129.])
        np.testing.assert_array_equal(resultado["p50"], [325., 10304., 20300., 30329.])
        np.testing.assert_array_equal(resultado["p90"], [525., 10504., 20500., 30529.])

    def test_timestamps_sem_fuso_em_formatos_distintos(self):
        forecast = np.array([[[10., 11., 12., 13., 14.],
                              [20., 21., 22., 23., 24.],
                              [30., 31., 32., 33., 34.]]])
        formatos = [
            (["2026-07-03 02:15:00"], ["2026-07-03 07:15:00"]),
            (np.array(["2026-07-03T02:15"], dtype="datetime64[m]"),
             np.array(["2026-07-03T07:15"], dtype="datetime64[ns]")),
            ([datetime(2026, 7, 3, 2, 15)], [datetime(2026, 7, 3, 7, 15)]),
        ]
        for fim, alvo in formatos:
            with self.subTest(tipo=type(fim[0]).__name__):
                resultado = alinhar_quantis(forecast, self.niveis, fim, alvo)
                np.testing.assert_array_equal(resultado["lead_hours"], [5])
                np.testing.assert_array_equal(resultado["index_zero_based"], [4])
                np.testing.assert_array_equal(resultado["p50"], [24.])

    def test_preserva_todas_entradas_somente_leitura(self):
        forecast = np.arange(2 * 3 * 5, dtype=np.float64).reshape(2, 3, 5)
        niveis = self.niveis.copy()
        fim = np.array(["2026-07-03T02:00:00", "2026-07-04T02:00:00"], dtype="datetime64[ns]")
        alvo = fim + np.array([1, 5], dtype="timedelta64[h]")
        entradas = (forecast, niveis, fim, alvo)
        copias = [entrada.copy() for entrada in entradas]
        for entrada in entradas:
            entrada.setflags(write=False)
        resultado = alinhar_quantis(*entradas)
        np.testing.assert_array_equal(resultado["p50"], [5., 24.])
        for entrada, copia in zip(entradas, copias):
            np.testing.assert_array_equal(entrada, copia)
            self.assertFalse(entrada.flags.writeable)

    def test_quantile_levels_correspondencia_unica_e_tolerancia_absoluta(self):
        forecast = np.array([[[10.], [50.], [90.]]])
        niveis_proximos = self.niveis + np.array([5e-13, -5e-13, 5e-13])
        resultado = alinhar_quantis(forecast, niveis_proximos, self.fim, self.alvo)
        np.testing.assert_array_equal(resultado["p10"], [10.])
        np.testing.assert_array_equal(resultado["p50"], [50.])
        np.testing.assert_array_equal(resultado["p90"], [90.])
        casos = [
            np.array([.1, .4, .9]),
            np.array([.1 + 2e-12, .5, .9]),
            np.array([.1, .5 - 5e-13, .5 + 5e-13, .9]),
            np.array([.1 - 5e-13, .1 + 5e-13, .5, .9]),
        ]
        for niveis in casos:
            with self.subTest(niveis=niveis.tolist()):
                with self.assertRaises(ValueError):
                    alinhar_quantis(np.zeros((1, len(niveis), 1)), niveis, self.fim, self.alvo)

    def test_quantile_levels_exigem_ordem_intervalo_e_finitude(self):
        casos = [
            np.array([.1, .5, .5, .9]),
            np.array([.1, .9, .5]),
            np.array([0., .1, .5, .9]),
            np.array([-.1, .1, .5, .9]),
            np.array([.1, .5, .9, 1.]),
            np.array([.1, .5, .9, 1.1]),
            np.array([.1, .5, .9, np.nan]),
            np.array([.1, .5, .9, np.inf]),
        ]
        for niveis in casos:
            with self.subTest(niveis=niveis.tolist()):
                antes = niveis.copy()
                with self.assertRaises(ValueError):
                    alinhar_quantis(np.zeros((1, len(niveis), 1)), niveis, self.fim, self.alvo)
                np.testing.assert_array_equal(niveis, antes)

    def test_dimensoes_batch_e_finitude_do_forecast(self):
        forecast = np.zeros((1, 3, 5))
        nao_finito = forecast.copy()
        nao_finito[0, 0, -1] = np.nan
        casos = [
            (forecast[0], self.niveis, self.fim, self.alvo),
            (np.zeros((0, 3, 5)), self.niveis, self.fim[:0], self.alvo[:0]),
            (np.zeros((1, 3, 0)), self.niveis, self.fim, self.alvo),
            (np.zeros((1, 2, 5)), self.niveis, self.fim, self.alvo),
            (forecast, self.niveis[None, :], self.fim, self.alvo),
            (forecast, self.niveis, self.fim[None, :], self.alvo),
            (forecast, self.niveis, self.fim, np.repeat(self.alvo, 2)),
            (nao_finito, self.niveis, self.fim, self.alvo),
            (np.full_like(forecast, np.inf), self.niveis, self.fim, self.alvo),
        ]
        for indice, argumentos in enumerate(casos):
            with self.subTest(caso=indice):
                with self.assertRaises(ValueError):
                    alinhar_quantis(*argumentos)

    def test_trajetoria_curta_alvo_nao_posterior_e_delta_nao_horario(self):
        forecast = np.zeros((1, 3, 25))
        alvos_invalidos = [
            self.fim + np.timedelta64(26, "h"),
            self.fim.copy(),
            self.fim - np.timedelta64(1, "h"),
            self.fim + np.timedelta64(90, "m"),
            self.fim + np.timedelta64(1, "h") + np.timedelta64(1, "ns"),
        ]
        for alvo in alvos_invalidos:
            with self.subTest(alvo=str(alvo[0])):
                with self.assertRaises(ValueError):
                    alinhar_quantis(forecast, self.niveis, self.fim, alvo)

    def test_rejeita_nat_e_textos_de_data_invalidos(self):
        forecast = np.zeros((1, 3, 5))
        casos = [
            (np.array(["NaT"], dtype="datetime64[ns]"), self.alvo),
            (self.fim, np.array(["NaT"], dtype="datetime64[ns]")),
            (["data-invalida"], self.alvo),
            (self.fim, ["data-invalida"]),
            ([""], self.alvo),
        ]
        for fim, alvo in casos:
            with self.subTest(fim=str(fim), alvo=str(alvo)):
                with self.assertRaises(ValueError):
                    alinhar_quantis(forecast, self.niveis, fim, alvo)

    def test_nao_ordena_ou_recorta_previsoes_cruzadas_e_negativas(self):
        forecast = np.zeros((2, 3, 2))
        forecast[0, :, 0] = [5., -2., -8.]
        forecast[1, :, 1] = [-100., 30., -20.]
        copia = forecast.copy()
        fim = np.repeat(self.fim, 2)
        alvos = fim + np.array([1, 2], dtype="timedelta64[h]")
        resultado = alinhar_quantis(forecast, self.niveis, fim, alvos)
        np.testing.assert_array_equal(resultado["p10"], [5., -100.])
        np.testing.assert_array_equal(resultado["p50"], [-2., 30.])
        np.testing.assert_array_equal(resultado["p90"], [-8., -20.])
        np.testing.assert_array_equal(forecast, copia)

    def test_rejeita_fuso_explicito_sem_converter_silenciosamente(self):
        forecast = np.zeros((1, 3, 5))
        casos = [
            ([datetime(2026, 7, 3, 2, tzinfo=timezone.utc)], [datetime(2026, 7, 3, 3, tzinfo=timezone.utc)]),
            (["2026-07-03T02:00:00Z"], ["2026-07-03T03:00:00Z"]),
            (["2026-07-03T02:00:00+00:00"], ["2026-07-03T03:00:00+00:00"]),
            (["2026-07-03T02:00:00-03:00"], ["2026-07-03T03:00:00-03:00"]),
            (self.fim, [datetime(2026, 7, 3, 3, tzinfo=timezone.utc)]),
        ]
        for fim, alvo in casos:
            with self.subTest(fim=str(fim), alvo=str(alvo)):
                with self.assertRaises(ValueError):
                    alinhar_quantis(forecast, self.niveis, fim, alvo)


if __name__ == "__main__":
    unittest.main()
