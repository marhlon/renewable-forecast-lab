import importlib.util
from pathlib import Path
import sys,unittest
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"notebooks"))
from bloco2_risco_core import *

class RiscoBloco2Test(unittest.TestCase):
    def test_cqr_rank_and_expansion(self):
        q=np.tile([2.,5.,8.],(9,1)); y=np.array([5.]*7+[10.,12.])
        correction,rank=correcao_cqr(y,q)
        self.assertEqual(rank,8);self.assertEqual(correction,2.)
        self.assertEqual(metricas_intervalo(y,q,correction)["coverage"],8/9)
    def test_quantile_reordering_without_input_mutation(self):
        q=np.array([[3.,1.,2.]])
        np.testing.assert_array_equal(ordenar_quantis(q),[[1.,2.,3.]])
        np.testing.assert_array_equal(q,[[3.,1.,2.]])
    def test_pinball_manual(self):
        result=metricas_intervalo([0.,10.],[[1.,5.,9.],[1.,5.,9.]])
        self.assertAlmostEqual(result["pinball_p50"],2.5)
        self.assertEqual(result["coverage"],0.)
        self.assertEqual(result["interval_score"],18.)
        expanded=metricas_intervalo([0.,10.],[[1.,5.,9.],[1.,5.,9.]],correcao=1.)
        self.assertAlmostEqual(expanded["pinball_p10"],.5)
        self.assertAlmostEqual(expanded["pinball_p90"],.5)
        self.assertEqual(expanded["coverage"],1.)
    def test_probability_and_alarm_manual(self):
        y=[0,1,0,1];p=[.1,.8,.7,.2]
        self.assertAlmostEqual(metricas_probabilidade(y,p)["brier"],.295)
        result=metricas_alarmes(y,[0,1,1,0])
        self.assertEqual((result["tp"],result["fp"],result["fn"],result["tn"],result["cost"]),(1,1,1,1,5))
    def test_budget_is_causal_and_per_day(self):
        origins=pd.date_range("2026-01-01",periods=48,freq="h")
        p=np.ones(48)*.7
        result=alarmes_causais(origins,p,.5)
        self.assertEqual(result[:24].sum(),6);self.assertEqual(result[24:].sum(),6)
        np.testing.assert_array_equal(result[:15],alarmes_causais(origins[:15],p[:15],.5))
        p[15:]=0
        np.testing.assert_array_equal(result[:15],alarmes_causais(origins,p,.5)[:15])
    def test_no_alarm_is_explicit_policy(self):
        o=pd.date_range("2026-01-01",periods=4,freq="h")
        chosen,rows=selecionar_politica(o,[0,0,0,0],[.8]*4,[.1,.5])
        self.assertIsNone(chosen["threshold"]);self.assertEqual(chosen["cost"],0)
    def test_reject_bad_clocks_or_scores(self):
        o=["2026-01-02","2026-01-01"]
        with self.assertRaises(ValueError): alarmes_causais(o,[.2,.3],.5)
        with self.assertRaises(ValueError): logit_features([1.2])
    def test_logit_is_finite_at_boundaries(self):
        self.assertTrue(np.isfinite(logit_features([0.,1.])).all())

if __name__=="__main__": unittest.main()
