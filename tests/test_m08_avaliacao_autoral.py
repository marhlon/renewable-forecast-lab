"""Contraprovas do avaliador M08.2, sem treinar redes ou ler dados do projeto."""

import unittest

import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from notebooks.m08_avaliacao_autoral import avaliar_lotes


class ModeloTeste(nn.Module):
    def __init__(self, falha=False, vetor=False):
        super().__init__()
        self.escala = nn.Parameter(torch.ones(()))
        self.dropout = nn.Dropout(0.5)
        self.falha = falha
        self.vetor = vetor

    def forward(self, x):
        if self.training or self.dropout.training or torch.is_grad_enabled():
            raise AssertionError("Esperados eval() e no_grad().")
        if self.falha:
            raise RuntimeError("Falha de forward para testar finally.")
        pred = self.dropout(x[:, 0, :]) * self.escala
        return pred[:, 0] if self.vetor else pred


class AvaliacaoLotesTest(unittest.TestCase):
    def setUp(self):
        self.x = torch.ones(5, 24, 1)
        self.y = torch.tensor([[1.], [1.], [1.], [1.], [11.]])

    def loader(self, x=None, y=None):
        return DataLoader(TensorDataset(self.x if x is None else x,
                                        self.y if y is None else y), batch_size=4)

    def conferir_preservacao(self, modelo, dados, erro=None):
        modelo.escala.grad = torch.tensor(7.)
        gradiente_original = modelo.escala.grad
        modos = [mod.training for mod in modelo.modules()]
        pesos = {key: value.clone() for key, value in modelo.state_dict().items()}
        if erro is None:
            resultado = avaliar_lotes(modelo, dados)
            self.assertEqual(resultado, {"rows": 5, "mse": 20.})
        else:
            with self.assertRaises(erro):
                avaliar_lotes(modelo, dados)
        self.assertEqual(modos, [mod.training for mod in modelo.modules()])
        self.assertIs(modelo.escala.grad, gradiente_original)
        self.assertEqual(modelo.escala.grad.item(), 7.)
        for key, value in modelo.state_dict().items():
            torch.testing.assert_close(value, pesos[key], rtol=0, atol=0)

    def test_ultimo_lote_menor_e_modos(self):
        for treino in (True, False):
            with self.subTest(treino=treino):
                modelo = ModeloTeste().train(treino)
                self.conferir_preservacao(modelo, self.loader())

    def test_modos_mistos_dos_submodulos(self):
        modelo = ModeloTeste().train()
        modelo.dropout.eval()
        self.conferir_preservacao(modelo, self.loader())

    def test_restaura_apos_falha_no_forward(self):
        for treino in (True, False):
            with self.subTest(treino=treino):
                self.conferir_preservacao(ModeloTeste(falha=True).train(treino),
                                          self.loader(), RuntimeError)

    def test_rejeita_alvo_vetor(self):
        self.conferir_preservacao(ModeloTeste(), self.loader(y=self.y[:, 0]), ValueError)

    def test_rejeita_previsao_vetor(self):
        self.conferir_preservacao(ModeloTeste(vetor=True), self.loader(), ValueError)

    def test_rejeita_erros_nao_finitos_e_overflow_da_soma(self):
        for valor in (float('nan'), float('inf'), 1e200):
            with self.subTest(valor=valor):
                y = torch.full((5, 1), valor, dtype=torch.float64)
                self.conferir_preservacao(ModeloTeste(), self.loader(y=y), ValueError)

    def test_rejeita_loader_vazio(self):
        self.conferir_preservacao(ModeloTeste(),
                                  self.loader(x=self.x[:0], y=self.y[:0]), ValueError)

    def test_contexto_externo_de_gradientes(self):
        with torch.enable_grad():
            avaliar_lotes(ModeloTeste(), self.loader())
            self.assertTrue(torch.is_grad_enabled())
        with torch.no_grad():
            avaliar_lotes(ModeloTeste(), self.loader())
            self.assertFalse(torch.is_grad_enabled())


if __name__ == "__main__":
    unittest.main()
