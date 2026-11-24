"""M09.1: atencao escalada explicita; sem treino, pesos pre-treinados ou forecast."""
import numpy as np


def atencao_escalada(q, k, v, mascara=None):
    """Q[B,L,D], K[B,S,D], V[B,S,Dv]; mascara[L,S], True permite consultar.

    Retorna exatamente pesos[B,L,S] e saida[B,L,Dv]. Nao modifica entradas.
    Cada linha deve permitir pelo menos uma chave; nenhuma imputacao silenciosa.
    """
    q, k, v = (np.asarray(a, dtype=np.float64) for a in (q, k, v))
    if any(a.ndim != 3 or min(a.shape) <= 0 for a in (q, k, v)):
        raise ValueError('Q, K e V devem ser tensores 3D com dimensoes positivas.')
    if q.shape[0] != k.shape[0] or q.shape[0] != v.shape[0] or q.shape[2] != k.shape[2] or k.shape[1] != v.shape[1]:
        raise ValueError('Batch, dimensao Q/K e numero de chaves/valores devem corresponder.')
    if not all(np.isfinite(a).all() for a in (q, k, v)):
        raise ValueError('Q, K e V devem ser finitos.')
    length, source = q.shape[1], k.shape[1]
    if mascara is None:
        allowed = np.ones((length, source), dtype=bool)
    else:
        allowed = np.asarray(mascara)
        if allowed.dtype != np.bool_ or allowed.shape != (length, source):
            raise ValueError('mascara deve ser booleana [L,S]; True permite consultar.')
    if not allowed.any(axis=-1).all():
        raise ValueError('Uma consulta sem nenhuma chave permitida nao define softmax.')
    with np.errstate(over='raise', invalid='raise'):
        scores = (q @ np.swapaxes(k, -1, -2)) / np.sqrt(q.shape[-1])
    # Bloquear antes do softmax: chaves proibidas nao entram no denominador.
    masked = np.where(allowed[None, :, :], scores, -np.inf)
    shifted = masked - masked.max(axis=-1, keepdims=True)
    exp = np.exp(shifted)
    weights = exp / exp.sum(axis=-1, keepdims=True)
    output = weights @ v
    if not np.isfinite(output).all():
        raise ValueError('Saida nao finita.')
    return {'pesos': weights, 'saida': output}
