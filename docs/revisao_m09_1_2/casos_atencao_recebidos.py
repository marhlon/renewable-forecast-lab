"""Contas pequenas e contraprovas para atenção escalada com máscara."""
import unittest
import numpy as np
from notebooks.m09_atencao_autoral import atencao_escalada

class AtencaoEscaladaTest(unittest.TestCase):
    def test_conta_manual_e_escala_pela_dimensao(self):
        q=np.array([[[1.,0.]]]);k=np.array([[[np.sqrt(2.)*np.log(3.),0.],[0.,0.]]]);v=np.array([[[10.],[30.]]])
        r=atencao_escalada(q,k,v)
        self.assertEqual(set(r),{'pesos','saida'})
        np.testing.assert_allclose(r['pesos'],[[[.75,.25]]],atol=1e-14,rtol=0)
        np.testing.assert_allclose(r['saida'],[[[15.]]],atol=1e-14,rtol=0)
    def test_mascara_exclui_chave_antes_da_normalizacao(self):
        r=atencao_escalada(np.ones((1,1,1)),np.array([[[1000.],[0.]]]),np.array([[[10.],[30.]]]),np.array([[False,True]]))
        np.testing.assert_array_equal(r['pesos'],[[[0.,1.]]]);np.testing.assert_array_equal(r['saida'],[[[30.]]])
    def test_prefixos_bloqueiam_perturbacao_posterior(self):
        q=np.zeros((1,3,2));v=np.array([[[0.],[6.],[12.]]]);m=np.tri(3,dtype=bool)
        livre=atencao_escalada(q,q,v);causal=atencao_escalada(q,q,v,m);changed=v.copy();changed[:,-1]+=300
        c2=atencao_escalada(q,q,changed,m);l2=atencao_escalada(q,q,changed)
        np.testing.assert_allclose(livre['saida'][0,:,0],[6.,6.,6.],atol=1e-14,rtol=0)
        np.testing.assert_allclose(causal['saida'][0,:,0],[0.,3.,6.],atol=1e-14,rtol=0)
        np.testing.assert_array_equal(causal['saida'][:,:-1],c2['saida'][:,:-1])
        np.testing.assert_array_equal(livre['saida'][:,-1],causal['saida'][:,-1])
        self.assertTrue(np.all(l2['saida'][:,:-1]>livre['saida'][:,:-1]))
    def test_lotes_retangulares_readonly_e_eixo_das_chaves(self):
        q=np.zeros((2,2,4));k=np.zeros((2,3,4));v=np.array([[[1.,10.],[2.,20.],[3.,30.]],[[100.,1000.],[200.,2000.],[300.,3000.]]])
        m=np.array([[True,False,False],[False,True,True]]);args=(q,k,v,m);saved=[a.copy() for a in args]
        for a in args:a.setflags(write=False)
        r=atencao_escalada(*args)
        self.assertEqual(r['pesos'].shape,(2,2,3));self.assertEqual(r['saida'].shape,(2,2,2));self.assertEqual(r['saida'].dtype,np.float64)
        np.testing.assert_array_equal(r['pesos'].sum(axis=-1),np.ones((2,2)))
        np.testing.assert_array_equal(r['saida'],[[[1.,10.],[2.5,25.]],[[100.,1000.],[250.,2500.]]])
        for a,b in zip(args,saved):np.testing.assert_array_equal(a,b)
    def test_scores_grandes_sem_overflow_no_softmax(self):
        with np.errstate(over='raise',invalid='raise'):
            r=atencao_escalada(np.full((1,2,1),1000.),np.array([[[1000.],[999.]]]),np.array([[[1.],[2.]]]))
        np.testing.assert_array_equal(r['pesos'],[[[1.,0.],[1.,0.]]]);np.testing.assert_array_equal(r['saida'],[[[1.],[1.]]])
    def test_rejeita_dimensoes_mascaras_e_valores_invalidos(self):
        base=[np.zeros((2,3,4)),np.zeros((2,5,4)),np.zeros((2,5,2))]
        cases=[(0,np.zeros((3,4))),(0,np.zeros((2,0,4))),(1,np.zeros((1,5,4))),(1,np.zeros((2,5,3))),(2,np.zeros((2,4,2))),(2,np.full((2,5,2),np.nan))]
        for i,bad in cases:
            with self.subTest(indice=i,shape=bad.shape):
                args=base.copy();args[i]=bad
                with self.assertRaises(ValueError):atencao_escalada(*args)
        for m in (np.ones((3,5),dtype=int),np.ones((2,3,5),dtype=bool),np.ones((3,4),dtype=bool),np.array([[True]*5,[False]*5,[True]*5])):
            with self.subTest(mascara_shape=m.shape):
                with self.assertRaises(ValueError):atencao_escalada(*base,m)

if __name__=='__main__':unittest.main()
