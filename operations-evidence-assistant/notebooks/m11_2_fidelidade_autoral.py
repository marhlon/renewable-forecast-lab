"""Conferência dos valores e das referências de relatórios já tipados."""

from decimal import Decimal


def conferir_fidelidade(candidato, esperado):
    """Liste todas as divergências com a fonte, sem modificar os objetos."""
    erros = set()

    for campo, codigo in (
        ("id", "id_divergente"),
        ("code", "classe_divergente"),
        ("reason", "razao_sem_suporte"),
    ):
        if candidato[campo] != esperado[campo]:
            erros.add(codigo)

    for campo in ("cutoff", "s1", "s2"):
        recebido, original = candidato[campo], esperado[campo]
        if recebido is None or original is None:
            diferentes = recebido is not original
        else:
            diferentes = Decimal(recebido) != Decimal(original)
        if diferentes:
            erros.add(f"numero_divergente:{campo}")

    referencias = set(candidato["refs"])
    exigidas = set(esperado["refs"])
    if len(referencias) < len(candidato["refs"]):
        erros.add("citacao_repetida")
    erros.update(f"citacao_ausente:{campo}" for campo in exigidas - referencias)
    erros.update(f"citacao_extra:{campo}" for campo in referencias - exigidas)

    return sorted(erros)
