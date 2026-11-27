"""Contraprovas da decisão determinística e do orçamento do laboratório."""
import json
from pathlib import Path
import sys
import unittest

P = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/"src"))
from opevid.amostragem import cabe_no_contexto, conferir_picker, selecionar_token_top_k
from opevid.contrato import decidir, ler_codigo


class ContratoTest(unittest.TestCase):
    def test_casos_cobrem_as_quatro_decisoes(self):
        cases = json.loads((P/"data/casos_m11_1.json").read_bytes())
        self.assertEqual([decidir(case) for case in cases],
                         ["BELOW","INSUFFICIENT","BELOW","ISOLATED","ELIGIBLE","ISOLATED"])

    def test_nao_confunde_saida_com_evidencia(self):
        self.assertIsNone(ler_codigo("I choose BELOW."))
        self.assertIsNone(ler_codigo("The rule is as follows:\nBELOW"))
        self.assertEqual(ler_codigo("\nBELOW\nNo point passed."),"BELOW")
        self.assertEqual(decidir({"usable":False,"s1":"0.995","cutoff":"0.5"}),"INSUFFICIENT")

    def test_correcao_usa_decimal_comparavel_no_limite(self):
        case = {"usable":True,"k":2,"cutoff":"0.7","s1":"0.8","s2":"0.6999999999999999999"}
        self.assertEqual(decidir(case), "ISOLATED")
        self.assertEqual(decidir(dict(case,s2="0.7000000000000000000")), "ELIGIBLE")

    def test_orcamento_inclusivo_e_sem_truncar(self):
        self.assertTrue(cabe_no_contexto(511,1,512))
        self.assertFalse(cabe_no_contexto(512,1,512))
        self.assertFalse(cabe_no_contexto(350,163,512))

    def test_top_k_rejeita_fora_de_dominio(self):
        for kwargs in ({"u":1.}, {"k":True},{"k":4},{"temperatura":0.}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                selecionar_token_top_k((0.0,0.0),**({"u":.1,"k":2,"temperatura":1.0}|kwargs))
        self.assertEqual(conferir_picker(selecionar_token_top_k), 6)


if __name__=="__main__":
    unittest.main()
