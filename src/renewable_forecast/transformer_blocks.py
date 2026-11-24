"""Blocos Transformer explícitos para estudar o fluxo de representações."""

from __future__ import annotations

import math

import torch
from torch import nn


def causal_mask(length: int, device=None):
    """Máscara [L,L]: True permite consultar a própria posição e anteriores."""
    if length <= 0:
        raise ValueError("O comprimento da máscara deve ser positivo.")
    return torch.ones(length, length, dtype=torch.bool, device=device).tril()


def sinusoidal_positions(length: int, d_model: int, *, device=None, dtype=torch.float32):
    """Codificação fixa [L,E], inclusive quando E é ímpar."""
    if length <= 0 or d_model <= 0:
        raise ValueError("Comprimento e dimensão devem ser positivos.")
    if not torch.empty((), dtype=dtype).is_floating_point():
        raise ValueError("A codificação posicional exige um dtype de ponto flutuante.")
    positions = torch.arange(length, dtype=dtype, device=device)[:, None]
    frequencies = torch.exp(
        torch.arange(0, d_model, 2, dtype=dtype, device=device)
        * (-math.log(10000.0) / d_model)
    )
    encoding = torch.zeros(length, d_model, dtype=dtype, device=device)
    encoding[:, 0::2] = torch.sin(positions * frequencies)
    encoding[:, 1::2] = torch.cos(positions * frequencies[: d_model // 2])
    return encoding


def _sequence(x, d_model, name):
    if not isinstance(x, torch.Tensor) or x.ndim != 3:
        raise ValueError(f"{name} deve ser um tensor [B,L,E].")
    if min(x.shape) <= 0 or x.shape[-1] != d_model:
        raise ValueError(f"{name} deve ter dimensões positivas e E={d_model}.")
    if not x.is_floating_point() or not torch.isfinite(x).all().item():
        raise ValueError(f"{name} deve conter valores de ponto flutuante finitos.")


def _allowed(mask, length, source, device):
    if mask is None:
        return torch.ones(length, source, dtype=torch.bool, device=device)
    if not isinstance(mask, torch.Tensor) or mask.dtype != torch.bool:
        raise ValueError("A máscara deve ser um tensor booleano; True permite.")
    if tuple(mask.shape) != (length, source):
        raise ValueError("A máscara deve ter shape [consultas,chaves].")
    if not mask.any(dim=-1).all().item():
        raise ValueError("Cada consulta deve permitir pelo menos uma chave.")
    return mask.to(device=device)


class MultiHeadAttention(nn.Module):
    """Projeções, divisão em cabeças, atenção e concatenação explícitas.

    Retorna a saída [B,L,E] e probabilidades [B,H,L,S] antes do Dropout.
    As probabilidades somam um; durante treino o produto por V usa o Dropout.
    """

    def __init__(self, d_model=16, n_heads=4, dropout=0.1):
        super().__init__()
        if d_model <= 0 or n_heads <= 0 or d_model % n_heads:
            raise ValueError("d_model deve ser positivo e divisível por n_heads.")
        self.d_model, self.n_heads = d_model, n_heads
        self.head_dim = d_model // n_heads
        self.q_proj = nn.Linear(d_model, d_model)
        self.k_proj = nn.Linear(d_model, d_model)
        self.v_proj = nn.Linear(d_model, d_model)
        self.out_proj = nn.Linear(d_model, d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, q, k, v, allowed_mask=None):
        for name, tensor in (("Q", q), ("K", k), ("V", v)):
            _sequence(tensor, self.d_model, name)
        batch, length, _ = q.shape
        source = k.shape[1]
        if k.shape[0] != batch or v.shape[:2] != (batch, source):
            raise ValueError("Batch e quantidade de chaves/valores devem corresponder.")
        if q.dtype != k.dtype or q.dtype != v.dtype or q.device != k.device or q.device != v.device:
            raise ValueError("Q, K e V devem compartilhar dtype e dispositivo.")
        allowed = _allowed(allowed_mask, length, source, q.device)

        def heads(tensor):
            return tensor.reshape(batch, -1, self.n_heads, self.head_dim).transpose(1, 2)

        qh, kh, vh = heads(self.q_proj(q)), heads(self.k_proj(k)), heads(self.v_proj(v))
        scores = (qh @ kh.transpose(-1, -2)) / math.sqrt(self.head_dim)
        scores = scores.masked_fill(~allowed[None, None], float("-inf"))
        weights = torch.softmax(scores, dim=-1)
        if not torch.isfinite(weights).all().item():
            raise ValueError("As probabilidades de atenção devem ser finitas.")
        attended = self.dropout(weights) @ vh
        joined = attended.transpose(1, 2).contiguous().reshape(batch, length, self.d_model)
        output = self.out_proj(joined)
        if not torch.isfinite(output).all().item():
            raise ValueError("A saída da atenção deve ser finita.")
        return output, weights


class EncoderBlock(nn.Module):
    """Atenção livre e FFN, cada uma seguida de residual e LayerNorm (post-norm)."""

    def __init__(self, d_model=16, n_heads=4, d_ff=32, dropout=0.1):
        super().__init__()
        if d_ff <= 0:
            raise ValueError("d_ff deve ser positivo.")
        self.attention = MultiHeadAttention(d_model, n_heads, dropout)
        self.linear1 = nn.Linear(d_model, d_ff)
        self.linear2 = nn.Linear(d_ff, d_model)
        self.norm1 = nn.LayerNorm(d_model, eps=1e-5)
        self.norm2 = nn.LayerNorm(d_model, eps=1e-5)
        self.dropout = nn.Dropout(dropout)
        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)

    def forward(self, x, allowed_mask=None, return_trace=False):
        attention, weights = self.attention(x, x, x, allowed_mask)
        residual_attention = x + self.dropout1(attention)
        after_attention = self.norm1(residual_attention)
        ffn_hidden = torch.relu(self.linear1(after_attention))
        feed_forward = self.linear2(self.dropout(ffn_hidden))
        residual_ffn = after_attention + self.dropout2(feed_forward)
        output = self.norm2(residual_ffn)
        if return_trace:
            return output, {
                "input": x, "attention": attention, "attention_weights": weights,
                "residual_attention": residual_attention, "after_attention": after_attention,
                "ffn_hidden": ffn_hidden, "feed_forward": feed_forward,
                "residual_ffn": residual_ffn, "output": output,
            }
        return output


class DecoderBlock(nn.Module):
    """Self-attention causal, cross-attention à memória e FFN, em post-norm."""

    def __init__(self, d_model=16, n_heads=4, d_ff=32, dropout=0.1):
        super().__init__()
        if d_ff <= 0:
            raise ValueError("d_ff deve ser positivo.")
        self.self_attention = MultiHeadAttention(d_model, n_heads, dropout)
        self.cross_attention = MultiHeadAttention(d_model, n_heads, dropout)
        self.linear1 = nn.Linear(d_model, d_ff)
        self.linear2 = nn.Linear(d_ff, d_model)
        self.norm1 = nn.LayerNorm(d_model, eps=1e-5)
        self.norm2 = nn.LayerNorm(d_model, eps=1e-5)
        self.norm3 = nn.LayerNorm(d_model, eps=1e-5)
        self.dropout = nn.Dropout(dropout)
        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)
        self.dropout3 = nn.Dropout(dropout)

    def forward(self, x, memory, self_mask=None, memory_mask=None, return_trace=False):
        if self_mask is None:
            if x.ndim != 3:
                raise ValueError("O decoder exige uma entrada [B,T,E].")
            self_mask = causal_mask(x.shape[1], device=x.device)
        attended_self, self_weights = self.self_attention(x, x, x, self_mask)
        residual_self = x + self.dropout1(attended_self)
        after_self = self.norm1(residual_self)
        attended_cross, cross_weights = self.cross_attention(after_self, memory, memory, memory_mask)
        residual_cross = after_self + self.dropout2(attended_cross)
        after_cross = self.norm2(residual_cross)
        ffn_hidden = torch.relu(self.linear1(after_cross))
        feed_forward = self.linear2(self.dropout(ffn_hidden))
        residual_ffn = after_cross + self.dropout3(feed_forward)
        output = self.norm3(residual_ffn)
        if return_trace:
            return output, {
                "input": x, "self_attention": attended_self,
                "self_attention_weights": self_weights, "residual_self": residual_self,
                "after_self": after_self, "cross_attention": attended_cross,
                "cross_attention_weights": cross_weights, "residual_cross": residual_cross,
                "after_cross": after_cross, "ffn_hidden": ffn_hidden,
                "feed_forward": feed_forward,
                "residual_ffn": residual_ffn, "output": output,
            }
        return output


class TransformerDidatico(nn.Module):
    """Encoder/decoder empilhados; devolve representações, sem cabeça de previsão.

    Duas camadas post-norm por padrão, sem uma LayerNorm extra após a pilha.
    Os tokens de consulta são entradas sintéticas do exercício, não alvos h24.
    """

    def __init__(self, input_size=1, d_model=16, n_heads=4, d_ff=32, n_layers=2, dropout=0.1):
        super().__init__()
        if input_size <= 0 or n_layers <= 0:
            raise ValueError("input_size e n_layers devem ser positivos.")
        self.input_size, self.d_model = input_size, d_model
        self.source_projection = nn.Linear(input_size, d_model)
        self.query_projection = nn.Linear(input_size, d_model)
        self.encoders = nn.ModuleList([
            EncoderBlock(d_model, n_heads, d_ff, dropout) for _ in range(n_layers)
        ])
        self.decoders = nn.ModuleList([
            DecoderBlock(d_model, n_heads, d_ff, dropout) for _ in range(n_layers)
        ])

    def _embed(self, values, projection, name):
        _sequence(values, self.input_size, name)
        embedded = projection(values)
        position = sinusoidal_positions(
            values.shape[1], self.d_model, device=values.device, dtype=values.dtype,
        )
        return embedded + position[None]

    def encode(self, source):
        memory = self._embed(source, self.source_projection, "Histórico")
        traces = []
        for block in self.encoders:
            memory, trace = block(memory, return_trace=True)
            traces.append(trace)
        return memory, traces

    def decode(self, queries, memory):
        state = self._embed(queries, self.query_projection, "Consultas")
        traces = []
        for block in self.decoders:
            state, trace = block(state, memory, return_trace=True)
            traces.append(trace)
        return state, traces

    def forward(self, source, queries):
        if source.ndim != 3 or queries.ndim != 3 or source.shape[0] != queries.shape[0]:
            raise ValueError("Histórico e consultas devem ter shape [B,L,I] e o mesmo batch.")
        memory, encoder_traces = self.encode(source)
        decoder, decoder_traces = self.decode(queries, memory)
        return {
            "memory": memory, "decoder": decoder,
            "source_embedding": encoder_traces[0]["input"],
            "query_embedding": decoder_traces[0]["input"],
            "encoder_traces": encoder_traces, "decoder_traces": decoder_traces,
        }
