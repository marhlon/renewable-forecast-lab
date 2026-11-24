"""M08.3: GRU pequena, estado reiniciado por janela e avaliacao por exemplo.

Este modulo nao carrega dados, nao treina ao importar e nao depende do notebook.
"""
from __future__ import annotations

import math
import torch
from torch import nn


class GRU24h(nn.Module):
    """[B,24,1] -> GRU [B,24,16] -> estado final [B,16] -> [B,1]."""

    def __init__(self, hidden_size: int = 16, dropout: float = 0.1):
        super().__init__()
        self.gru = nn.GRU(input_size=1, hidden_size=hidden_size,
                          num_layers=1, batch_first=True, bidirectional=False)
        # Dropout explicito na cabeca: o dropout interno da GRU e entre camadas.
        self.dropout = nn.Dropout(dropout)
        self.head = nn.Linear(hidden_size, 1)

    def forward(self, x):
        if x.ndim != 3 or x.shape[1:] != (24, 1) or len(x) == 0:
            raise ValueError('GRU24h espera um lote nao vazio com shape [B,24,1].')
        # Sem h_0 fornecido, a GRU usa zeros novos para cada janela/chamada.
        # Nao armazenar hidden em self: os lotes de ajuste sao embaralhados.
        _, hidden = self.gru(x)
        return self.head(self.dropout(hidden[-1]))


def avaliar_lotes(modelo, loader):
    """Avaliador recebido no M08.2, preservando inclusive modos mistos."""
    modos_anteriores = [(modulo, modulo.training) for modulo in modelo.modules()]
    total_exemplos = 0
    soma_quadrados = 0.0
    try:
        modelo.eval()
        with torch.no_grad():
            for x, y in loader:
                previsao = modelo(x)
                if y.ndim != 2 or y.shape[1] != 1 or previsao.shape != y.shape:
                    raise ValueError('Previsao e alvo devem ter o mesmo shape [B,1].')
                residuo = (previsao - y).to(dtype=torch.float64)
                if not torch.isfinite(residuo).all().item():
                    raise ValueError('Residuo de avaliacao nao finito.')
                soma_quadrados += residuo.square().sum().item()
                if not math.isfinite(soma_quadrados):
                    raise ValueError('Soma dos erros quadraticos nao finita.')
                total_exemplos += y.shape[0]
        if total_exemplos == 0:
            raise ValueError('Nao e possivel avaliar um loader vazio.')
        return {'rows': total_exemplos, 'mse': soma_quadrados / total_exemplos}
    finally:
        for modulo, modo_anterior in modos_anteriores:
            modulo.training = modo_anterior
