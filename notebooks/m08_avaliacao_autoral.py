"""Avaliação por exemplo para M08.2, com assistência do Codex.

Implementada a pedido de Marlon A. Bomfim. A soma ponderada preserva o peso
correto do último lote; a avaliação não atualiza parâmetros nem gradientes.
"""

import math

import torch


def avaliar_lotes(modelo, loader):
    """Retorna exatamente rows e mse, restaurando os modos mesmo em caso de erro."""
    # Guardar cada módulo também preserva configurações mistas de treino/eval.
    modos_anteriores = [(modulo, modulo.training) for modulo in modelo.modules()]
    total_exemplos = 0
    soma_quadrados = 0.0
    try:
        modelo.eval()
        with torch.no_grad():
            for x, y in loader:
                previsao = modelo(x)
                if y.ndim != 2 or y.shape[1] != 1 or previsao.shape != y.shape:
                    raise ValueError("Previsão e alvo devem ter o mesmo shape [B,1].")

                # O quadrado e a soma são feitos em float64 para a conferência.
                residuo = (previsao - y).to(dtype=torch.float64)
                if not torch.isfinite(residuo).all().item():
                    raise ValueError("Resíduo de avaliação não finito.")
                soma_quadrados += residuo.square().sum().item()
                if not math.isfinite(soma_quadrados):
                    raise ValueError("Soma dos erros quadráticos não finita.")
                total_exemplos += y.shape[0]

        if total_exemplos == 0:
            raise ValueError("Não é possível avaliar um loader vazio.")
        # Dividir por exemplos, não por lotes: o lote menor não ganha peso extra.
        return {"rows": total_exemplos, "mse": soma_quadrados / total_exemplos}
    finally:
        # eval() altera as flags recursivamente; restauramos cada flag original.
        for modulo, modo_anterior in modos_anteriores:
            modulo.training = modo_anterior
