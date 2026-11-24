"""Equivalência e contraprovas de acesso para os blocos Transformer didáticos."""

import math
import unittest

import torch
from torch import nn
from torch.nn import functional as F

from renewable_forecast.transformer_blocks import (
    DecoderBlock,
    EncoderBlock,
    MultiHeadAttention,
    TransformerDidatico,
    causal_mask,
    sinusoidal_positions,
)


def copiar_atencao_para_pytorch(origem, destino):
    """Une Q/K/V separados no armazenamento empilhado usado por nn.MultiheadAttention."""
    with torch.no_grad():
        destino.in_proj_weight.copy_(torch.cat([
            origem.q_proj.weight, origem.k_proj.weight, origem.v_proj.weight,
        ], dim=0))
        destino.in_proj_bias.copy_(torch.cat([
            origem.q_proj.bias, origem.k_proj.bias, origem.v_proj.bias,
        ], dim=0))
        destino.out_proj.load_state_dict(origem.out_proj.state_dict())


def copiar_encoder_para_pytorch(origem, destino):
    copiar_atencao_para_pytorch(origem.attention, destino.self_attn)
    for nome in ("linear1", "linear2", "norm1", "norm2"):
        getattr(destino, nome).load_state_dict(getattr(origem, nome).state_dict())


def copiar_decoder_para_pytorch(origem, destino):
    copiar_atencao_para_pytorch(origem.self_attention, destino.self_attn)
    copiar_atencao_para_pytorch(origem.cross_attention, destino.multihead_attn)
    for nome in ("linear1", "linear2", "norm1", "norm2", "norm3"):
        getattr(destino, nome).load_state_dict(getattr(origem, nome).state_dict())


class TransformerBlocksTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(2)

    def setUp(self):
        torch.manual_seed(1902)

    def assertClose(self, atual, esperado, atol=1e-12):
        torch.testing.assert_close(atual, esperado, rtol=0, atol=atol)

    def test_mascara_e_codificacao_posicional_com_dimensao_impar(self):
        mascara = causal_mask(5)
        self.assertEqual(mascara.dtype, torch.bool)
        self.assertTrue(torch.equal(mascara, torch.ones(5, 5, dtype=torch.bool).tril()))
        posicoes = sinusoidal_positions(5, 7, dtype=torch.float64)
        self.assertEqual(posicoes.shape, (5, 7))
        self.assertEqual(posicoes.dtype, torch.float64)
        self.assertClose(posicoes[0], torch.tensor([0., 1., 0., 1., 0., 1., 0.], dtype=torch.float64), atol=0)
        self.assertAlmostEqual(posicoes[1, 0].item(), math.sin(1.), places=14)
        self.assertAlmostEqual(posicoes[1, 1].item(), math.cos(1.), places=14)
        self.assertAlmostEqual(posicoes[1, 2].item(), math.sin(10000. ** (-2. / 7.)), places=14)
        self.assertAlmostEqual(posicoes[1, 6].item(), math.sin(10000. ** (-6. / 7.)), places=14)

    def test_multiplas_cabecas_equivalem_ao_pytorch_retangular(self):
        atual = MultiHeadAttention(d_model=8, n_heads=2, dropout=.2).double().eval()
        referencia = nn.MultiheadAttention(8, 2, dropout=.2, batch_first=True).double().eval()
        copiar_atencao_para_pytorch(atual, referencia)
        q, k, v = torch.randn(2, 3, 8, dtype=torch.float64), torch.randn(2, 5, 8, dtype=torch.float64), torch.randn(2, 5, 8, dtype=torch.float64)
        permitidas = torch.tensor([[True, True, False, False, True],
                                   [True, False, True, True, False],
                                   [False, True, True, False, True]])
        for mascara in (None, permitidas):
            with self.subTest(mascara=mascara is not None), torch.no_grad():
                saida, pesos = atual(q, k, v, allowed_mask=mascara)
                esperada, pesos_esperados = referencia(q, k, v,
                    attn_mask=None if mascara is None else ~mascara,
                    need_weights=True, average_attn_weights=False)
                self.assertEqual(saida.shape, (2, 3, 8))
                self.assertEqual(pesos.shape, (2, 2, 3, 5))
                self.assertClose(saida, esperada)
                self.assertClose(pesos, pesos_esperados)
                self.assertClose(pesos.sum(dim=-1), torch.ones(2, 2, 3, dtype=torch.float64))
                if mascara is not None:
                    bloqueadas = (~mascara)[None, None].expand_as(pesos)
                    self.assertTrue(torch.all(pesos.masked_select(bloqueadas) == 0))

    def test_encoder_pos_norma_equivale_ao_pytorch(self):
        atual = EncoderBlock(d_model=8, n_heads=2, d_ff=20, dropout=.2).double().eval()
        referencia = nn.TransformerEncoderLayer(d_model=8, nhead=2,
            dim_feedforward=20, dropout=.2, activation="relu", layer_norm_eps=1e-5,
            batch_first=True, norm_first=False).double().eval()
        copiar_encoder_para_pytorch(atual, referencia)
        x = torch.randn(2, 5, 8, dtype=torch.float64)
        for mascara in (None, causal_mask(5)):
            with self.subTest(causal=mascara is not None), torch.no_grad():
                saida = atual(x, allowed_mask=mascara)
                esperada = referencia(x, src_mask=None if mascara is None else ~mascara)
                self.assertClose(saida, esperada)
                com_trace, trace = atual(x, allowed_mask=mascara, return_trace=True)
                self.assertClose(com_trace, saida, atol=0)
                self.assertIsInstance(trace, dict)

    def test_decoder_pos_norma_equivale_ao_pytorch_com_cross_attention(self):
        atual = DecoderBlock(d_model=8, n_heads=2, d_ff=20, dropout=.2).double().eval()
        referencia = nn.TransformerDecoderLayer(d_model=8, nhead=2,
            dim_feedforward=20, dropout=.2, activation="relu", layer_norm_eps=1e-5,
            batch_first=True, norm_first=False).double().eval()
        copiar_decoder_para_pytorch(atual, referencia)
        x, memoria = torch.randn(2, 3, 8, dtype=torch.float64), torch.randn(2, 5, 8, dtype=torch.float64)
        self_mask = causal_mask(3)
        memory_mask = torch.ones(3, 5, dtype=torch.bool)
        memory_mask[0, -1] = False
        with torch.no_grad():
            saida = atual(x, memoria, self_mask=self_mask, memory_mask=memory_mask)
            esperada = referencia(x, memoria, tgt_mask=~self_mask, memory_mask=~memory_mask)
            self.assertClose(saida, esperada)
            com_trace, trace = atual(x, memoria, self_mask=self_mask,
                                    memory_mask=memory_mask, return_trace=True)
            self.assertClose(com_trace, saida, atol=0)
            self.assertIsInstance(trace, dict)

    def test_decoder_causal_preserva_prefixos_com_memoria_fixa(self):
        modelo = DecoderBlock(d_model=8, n_heads=2, d_ff=16, dropout=.3).double().eval()
        x, memoria = torch.randn(2, 5, 8, dtype=torch.float64), torch.randn(2, 7, 8, dtype=torch.float64)
        alterado = x.clone()
        alterado[:, 3:] += 10. * torch.randn_like(alterado[:, 3:])
        with torch.no_grad():
            original = modelo(x, memoria)
            posterior = modelo(alterado, memoria)
            livre = modelo(x, memoria, self_mask=torch.ones(5, 5, dtype=torch.bool))
            livre_alterado = modelo(alterado, memoria, self_mask=torch.ones(5, 5, dtype=torch.bool))
        self.assertClose(original[:, :3], posterior[:, :3])
        self.assertGreater((livre[:, :3] - livre_alterado[:, :3]).abs().max().item(), 1e-6)

    def test_encoder_livre_e_causal_tem_acessos_diferentes(self):
        modelo = EncoderBlock(d_model=8, n_heads=2, d_ff=16, dropout=.3).double().eval()
        x = torch.randn(2, 5, 8, dtype=torch.float64)
        alterado = x.clone()
        alterado[:, 3:] += 10. * torch.randn_like(alterado[:, 3:])
        with torch.no_grad():
            livre, livre_alterado = modelo(x), modelo(alterado)
            causal = modelo(x, allowed_mask=causal_mask(5))
            causal_alterado = modelo(alterado, allowed_mask=causal_mask(5))
        self.assertGreater((livre[:, :3] - livre_alterado[:, :3]).abs().max().item(), 1e-6)
        self.assertClose(causal[:, :3], causal_alterado[:, :3])

    def test_residuais_e_layernorm_atuam_por_token(self):
        modelo = EncoderBlock(d_model=8, n_heads=2, d_ff=16, dropout=0.).double().eval()
        with torch.no_grad():
            modelo.attention.out_proj.weight.zero_()
            modelo.attention.out_proj.bias.zero_()
            modelo.linear2.weight.zero_()
            modelo.linear2.bias.zero_()
            modelo.norm1.weight.copy_(torch.linspace(.7, 1.3, 8, dtype=torch.float64))
            modelo.norm1.bias.copy_(torch.linspace(-.2, .2, 8, dtype=torch.float64))
            modelo.norm2.weight.copy_(torch.linspace(.8, 1.2, 8, dtype=torch.float64))
        x = torch.randn(2, 4, 8, dtype=torch.float64)
        alterado = x.clone()
        alterado[:, -1] += torch.arange(8, dtype=torch.float64) * 10
        with torch.no_grad():
            primeiro = F.layer_norm(x, (8,), modelo.norm1.weight, modelo.norm1.bias, modelo.norm1.eps)
            esperado = F.layer_norm(primeiro, (8,), modelo.norm2.weight, modelo.norm2.bias, modelo.norm2.eps)
            saida = modelo(x)
            outra = modelo(alterado)
        self.assertClose(saida, esperado)
        self.assertClose(saida[:, :-1], outra[:, :-1], atol=0)

    def test_posicao_fixa_quebra_equivariancia_do_conteudo(self):
        modelo = MultiHeadAttention(d_model=8, n_heads=2, dropout=0.).double().eval()
        x = torch.randn(1, 5, 8, dtype=torch.float64)
        ordem = torch.tensor([3, 0, 4, 1, 2])
        pos = sinusoidal_positions(5, 8, dtype=torch.float64)[None]
        with torch.no_grad():
            sem_pos, _ = modelo(x, x, x)
            permutado, _ = modelo(x[:, ordem], x[:, ordem], x[:, ordem])
            com_pos, _ = modelo(x + pos, x + pos, x + pos)
            conteudo_permutado = x[:, ordem] + pos
            com_pos_permutado, _ = modelo(conteudo_permutado, conteudo_permutado, conteudo_permutado)
        self.assertClose(permutado, sem_pos[:, ordem])
        self.assertGreater((com_pos_permutado - com_pos[:, ordem]).abs().max().item(), 1e-6)

    def test_ultima_consulta_pode_mudar_apos_empilhar_blocos(self):
        primeiro = EncoderBlock(d_model=8, n_heads=2, d_ff=16, dropout=0.).double().eval()
        segundo = EncoderBlock(d_model=8, n_heads=2, d_ff=16, dropout=0.).double().eval()
        x = torch.randn(1, 5, 8, dtype=torch.float64)
        mascara = causal_mask(5)
        with torch.no_grad():
            livre_1 = primeiro(x)
            causal_1 = primeiro(x, allowed_mask=mascara)
            livre_2 = segundo(livre_1)
            causal_2 = segundo(causal_1, allowed_mask=mascara)
        self.assertClose(livre_1[:, -1], causal_1[:, -1])
        self.assertGreater((livre_2[:, -1] - causal_2[:, -1]).abs().max().item(), 1e-6)

    def test_wrapper_formas_estado_e_entradas_preservados(self):
        modelo = TransformerDidatico(input_size=1, d_model=8, n_heads=2,
            d_ff=16, n_layers=2, dropout=.2).double().eval()
        source, queries = torch.randn(2, 7, 1, dtype=torch.float64), torch.randn(2, 3, 1, dtype=torch.float64)
        originais = [source.clone(), queries.clone()]
        estado = {nome: valor.clone() for nome, valor in modelo.state_dict().items()}
        gradientes = []
        for parametro in modelo.parameters():
            parametro.grad = torch.full_like(parametro, 7.)
            gradientes.append(parametro.grad)
        modos = [modulo.training for modulo in modelo.modules()]
        with torch.no_grad():
            resultado = modelo(source, queries)
            memoria, traces_encoder = modelo.encode(source)
            decoder, traces_decoder = modelo.decode(queries, memoria)
        self.assertEqual(resultado["memory"].shape, (2, 7, 8))
        self.assertEqual(resultado["decoder"].shape, (2, 3, 8))
        self.assertEqual(resultado["source_embedding"].shape, (2, 7, 8))
        self.assertEqual(resultado["query_embedding"].shape, (2, 3, 8))
        self.assertEqual(len(resultado["encoder_traces"]), 2)
        self.assertEqual(len(resultado["decoder_traces"]), 2)
        self.assertEqual(len(traces_encoder), 2)
        self.assertEqual(len(traces_decoder), 2)
        self.assertClose(resultado["memory"], memoria, atol=0)
        self.assertClose(resultado["decoder"], decoder, atol=0)
        self.assertTrue(torch.equal(source, originais[0]))
        self.assertTrue(torch.equal(queries, originais[1]))
        for nome, valor in modelo.state_dict().items():
            self.assertClose(valor, estado[nome], atol=0)
        for parametro, gradiente in zip(modelo.parameters(), gradientes):
            self.assertIs(parametro.grad, gradiente)
            self.assertTrue(torch.all(parametro.grad == 7.))
        self.assertEqual(modos, [modulo.training for modulo in modelo.modules()])

    def test_gradientes_atravessam_encoder_e_decoder_sem_atualizar_pesos(self):
        modelo = TransformerDidatico(input_size=1, d_model=8, n_heads=2,
            d_ff=16, n_layers=2, dropout=0.).double().eval()
        source = torch.randn(2, 5, 1, dtype=torch.float64, requires_grad=True)
        queries = torch.randn(2, 3, 1, dtype=torch.float64, requires_grad=True)
        estado = {nome: valor.clone() for nome, valor in modelo.state_dict().items()}
        resultado = modelo(source, queries)["decoder"]
        coeficientes = torch.randn_like(resultado)
        (resultado * coeficientes).sum().backward()
        for entrada in (source, queries):
            self.assertIsNotNone(entrada.grad)
            self.assertTrue(torch.isfinite(entrada.grad).all())
            self.assertGreater(entrada.grad.abs().max().item(), 0.)
        for parametro in modelo.parameters():
            self.assertIsNotNone(parametro.grad)
            self.assertTrue(torch.isfinite(parametro.grad).all())
        for nome, valor in modelo.state_dict().items():
            self.assertClose(valor, estado[nome], atol=0)

    def test_dimensoes_e_mascaras_invalidas_sao_recusadas(self):
        for d_model, heads in ((8, 0), (0, 2), (10, 3)):
            with self.subTest(d_model=d_model, heads=heads):
                with self.assertRaises(ValueError):
                    MultiHeadAttention(d_model=d_model, n_heads=heads)
        modelo = MultiHeadAttention(d_model=8, n_heads=2).double().eval()
        q, k, v = torch.zeros(2, 3, 8, dtype=torch.float64), torch.zeros(2, 5, 8, dtype=torch.float64), torch.zeros(2, 5, 8, dtype=torch.float64)
        casos = [
            (q[0], k, v, None),
            (q, k[:1], v, None),
            (q, k[..., :7], v, None),
            (q, k, v[:, :4], None),
            (q, k, v, torch.ones(3, 5)),
            (q, k, v, torch.ones(2, 3, 5, dtype=torch.bool)),
            (q, k, v, torch.zeros(3, 5, dtype=torch.bool)),
            (q, k, torch.full_like(v, float("nan")), None),
        ]
        for indice, (query, key, value, mascara) in enumerate(casos):
            with self.subTest(caso=indice):
                with self.assertRaises(ValueError):
                    modelo(query, key, value, allowed_mask=mascara)


if __name__ == "__main__":
    unittest.main()
