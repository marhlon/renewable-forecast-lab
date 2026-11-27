"""Referência determinística para as quatro classes. Nada aqui gera texto."""
from decimal import Decimal

CODES = ("BELOW", "ISOLATED", "ELIGIBLE", "INSUFFICIENT")


def numero(x):
    if not isinstance(x, str):
        raise ValueError("Use decimais em texto para não arredondar antes da decisão.")
    d = Decimal(x)
    if not d.is_finite() or not 0 <= d <= 1:
        raise ValueError("Os escores deste recorte devem estar em [0,1].")
    return d


def decidir(caso):
    if caso["usable"] is False:
        return "INSUFFICIENT"
    if caso["usable"] is not True or type(caso["k"]) is not int or caso["k"] not in (1, 2):
        raise ValueError("Disponibilidade ou número de leituras inválido.")
    cutoff, s1 = numero(caso["cutoff"]), numero(caso["s1"])
    s2 = numero(caso["s2"]) if caso["s2"] is not None else None
    if (s2 is not None and s2 > s1) or (caso["k"] == 1 and s2 is not None):
        raise ValueError("O melhor par não pode superar o pico; k=1 não usa esse campo.")
    if s1 < cutoff:
        return "BELOW"
    if caso["k"] == 2 and (s2 is None or s2 < cutoff):
        return "ISOLATED"
    return "ELIGIBLE"


def ler_codigo(texto):
    """Só a primeira linha não vazia, igual a uma das quatro classes."""
    candidate = next((line.strip() for line in texto.splitlines() if line.strip()), None)
    return candidate if candidate in CODES else None
