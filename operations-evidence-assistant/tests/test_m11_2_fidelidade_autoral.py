"""Comparações manuais de relatórios sintéticos, sem LLM ou casos reservados."""

from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest


PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "m11_2_fidelidade_autoral", PROJECT / "notebooks/m11_2_fidelidade_autoral.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
conferir_fidelidade = MODULE.conferir_fidelidade


def report():
    return {
        "id": "exemplo_local", "code": "ISOLATED", "cutoff": "0.70",
        "s1": "0.90", "s2": None, "reason": "no_pair",
        "refs": ["k", "s1", "s2", "cutoff"],
    }


class TestConferirFidelidade(unittest.TestCase):
    def assert_issues(self, candidate, expected, issues):
        result = conferir_fidelidade(candidate, expected)
        self.assertIs(type(result), list)
        self.assertTrue(all(type(issue) is str for issue in result))
        self.assertEqual(len(result), len(set(result)), "Erros não podem se repetir.")
        self.assertCountEqual(result, issues)
        return result

    def test_relatorio_fiel_devolve_lista_vazia(self):
        expected = report()
        self.assert_issues(deepcopy(expected), expected, [])

    def test_decimais_com_zeros_adicionais_sao_equivalentes(self):
        expected = report()
        expected["s2"] = "0.00"
        expected["reason"] = "pair_below"
        candidate = deepcopy(expected)
        candidate.update(cutoff="0.700", s1="0.900000", s2="0")
        self.assert_issues(candidate, expected, [])

    def test_decimal_exato_nao_colapsa_diferencas_em_float(self):
        expected = report()
        expected.update(code="ELIGIBLE", s1="0.70", s2="0.70", reason="pair_met",
                        refs=["k", "s2", "cutoff"])
        for key in ("cutoff", "s1", "s2"):
            for value in ("0.6999999999999999999", "0.7000000000000000001"):
                with self.subTest(campo=key, valor=value):
                    candidate = deepcopy(expected)
                    candidate[key] = value
                    self.assert_issues(candidate, expected, [f"numero_divergente:{key}"])

    def test_acumula_todos_os_nove_erros_sem_retorno_antecipado(self):
        expected = report()
        candidate = {
            "id": "outro_local", "code": "ELIGIBLE", "cutoff": "0.71",
            "s1": "0.91", "s2": "0", "reason": "physical_cause",
            "refs": ["k", "s1", "cutoff", "usable", "s1"],
        }
        self.assert_issues(candidate, expected, [
            "id_divergente", "classe_divergente", "numero_divergente:cutoff",
            "numero_divergente:s1", "numero_divergente:s2", "razao_sem_suporte",
            "citacao_repetida", "citacao_ausente:s2", "citacao_extra:usable",
        ])

    def test_null_e_zero_sao_diferentes_nas_duas_direcoes(self):
        expected_zero = report()
        expected_zero.update(code="BELOW", s1="0", s2="0", reason="below", refs=["s1", "cutoff"])
        candidate_null = deepcopy(expected_zero)
        candidate_null.update(s1=None, s2=None)
        self.assert_issues(candidate_null, expected_zero, ["numero_divergente:s1", "numero_divergente:s2"])

        expected_null = report()
        expected_null.update(code="INSUFFICIENT", s1=None, s2=None, reason="unavailable", refs=["usable"])
        candidate_zero = deepcopy(expected_null)
        candidate_zero.update(s1="0", s2="0.0")
        self.assert_issues(candidate_zero, expected_null, ["numero_divergente:s1", "numero_divergente:s2"])

    def test_dois_nulls_coincidem_sem_conversao_decimal(self):
        expected = report()
        expected.update(code="INSUFFICIENT", s1=None, s2=None, reason="unavailable", refs=["usable"])
        self.assert_issues(deepcopy(expected), expected, [])

    def test_ordem_das_referencias_nao_conta(self):
        expected = report()
        candidate = deepcopy(expected)
        candidate["refs"] = ["cutoff", "s2", "k", "s1"]
        self.assert_issues(candidate, expected, [])

    def test_varias_repeticoes_geram_um_unico_codigo(self):
        expected = report()
        candidate = deepcopy(expected)
        candidate["refs"] += ["s1", "cutoff"]
        self.assert_issues(candidate, expected, ["citacao_repetida"])

    def test_cada_referencia_ausente_e_informada(self):
        expected = report()
        candidate = deepcopy(expected)
        candidate["refs"] = []
        self.assert_issues(candidate, expected, [
            "citacao_ausente:k", "citacao_ausente:s1", "citacao_ausente:s2", "citacao_ausente:cutoff",
        ])

    def test_cada_referencia_extra_e_informada(self):
        expected = report()
        expected.update(code="BELOW", s1="0.60", s2="0.50", reason="below", refs=["s1", "cutoff"])
        candidate = deepcopy(expected)
        candidate["refs"] = ["s1", "cutoff", "usable", "k", "s2"]
        self.assert_issues(candidate, expected, ["citacao_extra:usable", "citacao_extra:k", "citacao_extra:s2"])

    def test_ausencia_excesso_e_repeticao_sao_tres_divergencias(self):
        expected = report()
        candidate = deepcopy(expected)
        candidate["refs"] = ["k", "s1", "cutoff", "usable", "s1"]
        self.assert_issues(candidate, expected, [
            "citacao_ausente:s2", "citacao_extra:usable", "citacao_repetida",
        ])

    def test_razao_admitida_no_esquema_pode_nao_ter_suporte(self):
        expected = report()
        for reason in ("physical_cause", "incident_detected"):
            with self.subTest(razao=reason):
                candidate = deepcopy(expected)
                candidate["reason"] = reason
                self.assert_issues(candidate, expected, ["razao_sem_suporte"])

    def test_entradas_e_listas_de_referencias_permanecem_inalteradas(self):
        expected = report()
        candidate = deepcopy(expected)
        candidate["refs"] = ["s1", "cutoff", "usable", "k", "s1"]
        candidate["cutoff"] = "0.700"
        before_candidate, before_expected = deepcopy(candidate), deepcopy(expected)
        original_candidate_refs, original_expected_refs = candidate["refs"], expected["refs"]
        self.assert_issues(candidate, expected, [
            "citacao_repetida", "citacao_ausente:s2", "citacao_extra:usable",
        ])
        self.assertEqual(candidate, before_candidate)
        self.assertEqual(expected, before_expected)
        self.assertIs(candidate["refs"], original_candidate_refs)
        self.assertIs(expected["refs"], original_expected_refs)


if __name__ == "__main__":
    unittest.main()
