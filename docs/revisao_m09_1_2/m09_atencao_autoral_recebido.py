"""Atenção escalada de uma cabeça, com máscara booleana de acesso às chaves."""
import numpy as np


def atencao_escalada(q, k, v, mascara=None):
    """Q [B,L,D], K [B,S,D], V [B,S,Dv]; máscara [L,S], True permite.

    Retorna pesos [B,L,S] e saída [B,L,Dv], sem modificar as entradas.
    """
    q, k, v = (np.asarray(valor, dtype=np.float64) for valor in (q, k, v))
    if any(valor.ndim != 3 for valor in (q, k, v)):
        raise ValueError("Q, K e V devem ter três dimensões.")
    if any(min(valor.shape) <= 0 for valor in (q, k, v)):
        raise ValueError("As dimensões de Q, K e V devem ser positivas.")
    batch, consultas, dimensao = q.shape
    chaves = k.shape[1]
    if (
        k.shape[0] != batch or v.shape[0] != batch
        or k.shape[2] != dimensao or v.shape[1] != chaves
    ):
        raise ValueError("Batch, dimensão Q/K e quantidade de chaves/valores incompatíveis.")
    if not all(np.isfinite(valor).all() for valor in (q, k, v)):
        raise ValueError("Q, K e V devem conter somente valores finitos.")
    permitidas = None
    if mascara is not None:
        permitidas = np.asarray(mascara)
        if permitidas.dtype != np.bool_ or permitidas.shape != (consultas, chaves):
            raise ValueError("A máscara deve ser booleana [L,S], com True para acesso permitido.")
        if not permitidas.any(axis=1).all():
            raise ValueError("Cada consulta deve permitir pelo menos uma chave.")
    try:
        with np.errstate(over="raise", invalid="raise", under="ignore"):
            scores = np.matmul(q, k.swapaxes(-1, -2)) / np.sqrt(dimensao)
            if permitidas is not None:
                scores = np.where(permitidas[None, :, :], scores, -np.inf)
            scores = scores - np.max(scores, axis=-1, keepdims=True)
            exponenciais = np.exp(scores)
            pesos = exponenciais / np.sum(exponenciais, axis=-1, keepdims=True)
            saida = np.matmul(pesos, v)
    except FloatingPointError as erro:
        raise ValueError("O cálculo da atenção excedeu a faixa numérica disponível.") from erro
    if not np.isfinite(saida).all():
        raise ValueError("A representação calculada deve ser finita.")
    return {"pesos": pesos, "saida": saida}
