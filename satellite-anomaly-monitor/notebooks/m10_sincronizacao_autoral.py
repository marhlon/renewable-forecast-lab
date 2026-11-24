"""Retém a última amostra disponível, com limite de idade e origem explícita."""

import numpy as np
import pandas as pd


def _instantes_utc(values, nome):
    """Valida o fuso antes da conversão; não atribui UTC a um relógio ingênuo."""
    instantes = pd.Series(values, copy=True)
    if instantes.empty or instantes.isna().any():
        raise ValueError(f"{nome} exige timestamps válidos e não pode ser vazio.")
    if not isinstance(instantes.dtype, pd.DatetimeTZDtype):
        for value in instantes:
            instante = pd.Timestamp(value)
            if pd.isna(instante) or instante.tzinfo is None or instante.utcoffset() is None:
                raise ValueError(f"{nome} exige timestamps com fuso explícito.")
    return pd.DatetimeIndex(pd.to_datetime(instantes, utc=True)).astype("datetime64[ns, UTC]")


def sincronizar_causal(tabelas, grade, tolerancia):
    """Devolve timestamp e value/sample_time/age_seconds/usable de cada canal.

    A amostra escolhida nunca é posterior à decisão. Ao expirar, somente o
    valor utilizável vira NaN: timestamp e idade continuam como evidência.
    A função não consulta anotações e não modifica as entradas.
    """
    if not isinstance(tabelas, dict) or not tabelas:
        raise ValueError("Informe um dicionário não vazio de canais.")
    limite = pd.Timedelta(tolerancia)
    if pd.isna(limite) or limite < pd.Timedelta(0):
        raise ValueError("A tolerância deve ser uma duração finita não negativa.")
    instantes = _instantes_utc(grade, "grade")
    if instantes.has_duplicates or not instantes.is_monotonic_increasing:
        raise ValueError("A grade deve estar em ordem crescente, sem duplicidades.")

    resultado = pd.DataFrame({"timestamp": instantes})
    colunas = ["timestamp"]
    for canal, fonte in tabelas.items():
        if not isinstance(canal, str) or not canal.isidentifier():
            raise ValueError("Cada canal deve ter um nome identificador.")
        if (not isinstance(fonte, pd.DataFrame) or len(fonte.columns) != 2
                or set(fonte.columns) != {"timestamp", "value"}):
            raise ValueError("Cada canal deve conter exatamente timestamp e value.")

        dados = fonte.loc[:, ["timestamp", "value"]].copy(deep=True)
        dados["timestamp"] = _instantes_utc(dados["timestamp"], canal)
        dados["value"] = pd.to_numeric(dados["value"], errors="raise").astype(float)
        if np.isinf(dados["value"].to_numpy()).any():
            raise ValueError("Valores infinitos não são medições válidas.")
        if dados["timestamp"].duplicated().any():
            raise ValueError(f"O canal {canal} contém instantes duplicados.")
        dados = dados.sort_values("timestamp").reset_index(drop=True)

        valor = f"{canal}_value"
        amostra = f"{canal}_sample_time"
        idade = f"{canal}_age_seconds"
        utilizavel = f"{canal}_usable"
        dados = dados.rename(columns={"timestamp": amostra, "value": valor})
        # Sem tolerance aqui: uma amostra expirada ainda precisa ser identificada.
        resultado = pd.merge_asof(
            resultado, dados, left_on="timestamp", right_on=amostra,
            direction="backward", allow_exact_matches=True,
        )
        resultado[idade] = (resultado["timestamp"] - resultado[amostra]).dt.total_seconds()
        resultado[utilizavel] = (
            resultado[amostra].notna()
            & resultado[idade].between(0, limite.total_seconds(), inclusive="both")
            & resultado[valor].notna()
        )
        # Um NaN na última medição não autoriza recuperar outra amostra mais antiga.
        resultado[valor] = resultado[valor].where(resultado[utilizavel], np.nan)
        colunas.extend([valor, amostra, idade, utilizavel])

    return resultado.loc[:, colunas]
