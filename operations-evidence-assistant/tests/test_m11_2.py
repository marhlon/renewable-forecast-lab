"""Contratos que protegem a comparação e impedem publicar números alterados."""
from pathlib import Path
import sys
import unittest
from copy import deepcopy

P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/"src"))
sys.path.insert(0,str(P/"scripts"))

from opevid.estruturado_m11_2 import Fonte, aplicar_autoria, avaliar_resposta
from opevid.contraprovas_m11_2 import exercitar
from opevid.prompts_m11_2 import mensagens
from laboratorio_m11_2 import escolha, resumo


class ExperimentoTest(unittest.TestCase):
    def test_fixtures_pin_all_rejection_stages(self):
        rows=exercitar()
        self.assertEqual(len(rows),16)
        self.assertEqual({r["etapa"] for r in rows},{"json_invalido","esquema_invalido","divergencia","fiel"})

    def test_input_inconsistente_nao_produz_fallback_falso(self):
        src={"id":"x","cutoff":"0.7","s1":"0.6","s2":"0.8","k":2,"usable":True}
        Fonte.model_validate(src)
        with self.assertRaises(ValueError):
            avaliar_resposta("{}",src)

    def test_detect_mutation_in_author_hook(self):
        def mutates(got,want):
            got["refs"].clear()
            return []
        got={"refs":["s2"]}
        original=deepcopy(got)
        with self.assertRaisesRegex(ValueError,"modificou"):
            aplicar_autoria(mutates,got,deepcopy(got))
        self.assertEqual(got,original)

    def test_prompts_removing_example_recovers_exactly_the_same_instruction(self):
        caso={"id":"x","cutoff":"0.7","s1":"0.6","s2":None,"k":1,"usable":True}
        a,b=[mensagens(v,caso) for v in ("zero_shot","um_exemplo")]
        self.assertEqual(a[0],b[0])
        minus="\n".join(l for l in b[1]["content"].split("\n") if not l.startswith(("Example record:","Example response:")))
        self.assertEqual(a[1]["content"],minus)

    def test_selection_ties_are_explicit_and_counts_do_not_merge_fallback(self):
        def row(stage,origin):
            return {"etapa":stage,"publicado":{"origem":origin},"tokens_entrada":10,"tokens_novos":8}
        r1=resumo([row("json_invalido","fallback"), row("divergencia","fallback"),
                   row("fiel","conferido")],"desenvolvimento","zero_shot")
        r2=dict(r1,prompt="um_exemplo",fiel=0,tokens_novos=1)
        labels=("zero_shot","um_exemplo")
        self.assertEqual(escolha([r1,r2],labels),"zero_shot")
        self.assertEqual(escolha([r1,dict(r1,prompt="um_exemplo",tokens_novos=23)],labels),"um_exemplo")
        self.assertEqual(escolha([dict(r1,prompt="um_exemplo"),r1],labels),"zero_shot")
        self.assertEqual((r1["json_ok"],r1["esquema_ok"],r1["fiel"],r1["fallback"],r1["publicado_conferido"]),(2,2,1,2,3))


if __name__=="__main__":
    unittest.main()
