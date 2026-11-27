"""Conferências exatas dos casos fixos da aplicação técnica assistida."""
from fractions import Fraction
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "notebooks"))
from aplicar_fundamentos_quantitativos import (
    plans, solve_probability, solve_estimation, solve_hypotheses, solve_regression,
)


class FundamentosAplicadosTest(unittest.TestCase):
    def test_contingencia_e_posterior_por_fracao_exata(self):
        r, checks, _, _ = solve_probability(plans()["M02-01"]["inputs"])
        self.assertTrue(all(checks.values()))
        self.assertEqual([r[key] for key in ("true_positive", "false_negative", "false_positive", "true_negative")], [340, 60, 588, 19012])
        self.assertAlmostEqual(r["event_given_positive"], float(Fraction(85, 232)))

    def test_intervalos_usam_t_fornecido_e_explicitam_arredondamento(self):
        r, checks, _, _ = solve_estimation(plans()["M02-02"]["inputs"])
        self.assertTrue(all(checks.values()))
        self.assertEqual(r["mean"], 21)
        self.assertAlmostEqual(r["sample_variance"], float(Fraction(20, 3)))
        self.assertGreater(r["prediction_interval_using_given_t"][1], r["mean_ci_using_given_t"][1])
        self.assertNotEqual(r["t_given"], r["t_scipy"])
        self.assertAlmostEqual(r["separate_ar1_scenario"]["n_eff_approximate"], 18)

    def test_hipotese_bloco_e_familia_separada_sem_fabricar_horas(self):
        r, checks, _, _ = solve_hypotheses(plans()["M02-03"]["inputs"])
        self.assertTrue(all(checks.values()))
        self.assertEqual(r["block_count"], 6)
        self.assertAlmostEqual(r["mean_difference"], float(Fraction(13, 12)))
        self.assertTrue(r["reject_h0_nominal"])
        self.assertEqual(r["separate_family"]["rejected"], [True, False, False])
        self.assertFalse(r["hourly_series_fabricated"])

    def test_regressao_normalizacao_gradiente_posto_e_estabilidade(self):
        r, checks, _, _ = solve_regression(plans()["M02-04"]["inputs"])
        self.assertTrue(all(checks.values()))
        np.testing.assert_allclose(r["ols_beta"], [2, 1.25], rtol=0, atol=1e-12)
        np.testing.assert_allclose(r["ridge_beta"], [2, float(Fraction(10, 9))], rtol=0, atol=1e-12)
        self.assertEqual(r["n_lambda"], 1)
        self.assertEqual(r["deficient_rank"], 2)
        self.assertGreater(r["one_step_demonstrations"][1]["mse_after_one_step"], r["initial_mse"])
        self.assertFalse(r["future_autocorrelation_measured"])


if __name__ == "__main__":
    unittest.main()
