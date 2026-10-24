import hashlib
import json
from pathlib import Path
import re
import sys
import numpy as np
import pandas as pd


def encontrar_arquivos_execucao() -> tuple[Path, Path]:
    """Localiza automaticamente requests.csv e verification.json no projeto

    ou a partir do caminho informado no terminal.
    """
    cwd = Path.cwd().resolve()
    script_dir = Path(__file__).parent.resolve()

    # 1. Permite passar a pasta diretamente via argumento: python diagnostico_servico.py <caminho_da_pasta>
    if len(sys.argv) > 1:
        alvo = Path(sys.argv[1]).resolve()
        if alvo.is_file() and alvo.name == "requests.csv":
            return alvo, alvo.parent / "verification.json"
        elif alvo.is_dir():
            p_csv = alvo / "requests.csv"
            p_json = alvo / "verification.json"
            if p_csv.exists():
                return p_csv, p_json

    # 2. Busca direta no diretório atual e na pasta do script
    for base in [cwd, script_dir]:
        p_csv = base / "requests.csv"
        p_json = base / "verification.json"
        if p_csv.exists():
            return p_csv, p_json

    # 3. Busca em pastas de relatórios/telemetria conhecidas
    telemetria_dir = cwd / "reports" / "service"
    if telemetria_dir.exists():
        encontrados = sorted(list(telemetria_dir.rglob("requests.csv")))
        if encontrados:
            p_csv = encontrados[-1]
            p_json = p_csv.parent / "verification.json"
            print(f"Execução localizada em: {p_csv.parent}")
            return p_csv, p_json

    # 4. Busca recursiva genérica no repositório
    for base in [cwd, script_dir]:
        encontrados = sorted(list(base.rglob("requests.csv")))
        if encontrados:
            p_csv = encontrados[-1]
            p_json = p_csv.parent / "verification.json"
            print(f"Execução localizada em: {p_csv.parent}")
            return p_csv, p_json

    raise FileNotFoundError(
        "O arquivo 'requests.csv' não foi encontrado.\n"
        "Informe o caminho da pasta da execução diretamente:\n"
        "  python .\\notebooks\\diagnostico_servico.py .\\reports\\service\\...\n"
    )


def verificar_hash(arquivo_csv: Path, arquivo_json: Path) -> bool:
    """Verifica a integridade do requests.csv comparando seu SHA-256 (ou MD5)

    com o verification.json, suportando qualquer estrutura no JSON.
    """
    if not arquivo_csv.exists():
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {arquivo_csv}")
    if not arquivo_json.exists():
        raise FileNotFoundError(f"Arquivo verification.json não encontrado: {arquivo_json}")

    with open(arquivo_json, "r", encoding="utf-8") as f:
        texto_json = f.read()

    # Calcula SHA-256 e MD5 do CSV
    sha256 = hashlib.sha256()
    md5 = hashlib.md5()
    with open(arquivo_csv, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
            md5.update(chunk)

    hash_sha256 = sha256.hexdigest().lower()
    hash_md5 = md5.hexdigest().lower()
    texto_json_lower = texto_json.lower()

    # Confirma integridade se o hash calculado estiver presente no JSON
    if hash_sha256 in texto_json_lower or hash_md5 in texto_json_lower:
        print("Integridade confirmada: hash do requests.csv válido.")
        return True

    hashes_no_json = re.findall(r"[a-fA-F0-9]{32,64}", texto_json)
    hash_encontrado = hashes_no_json[0] if hashes_no_json else "Nenhum hash encontrado"

    raise ValueError(
        f"Falha de integridade no arquivo {arquivo_csv.name}!\n"
        f"  Hash Calculado (SHA-256): {hash_sha256}\n"
        f"  Hash no verification.json: {hash_encontrado}"
    )


def calcular_metricas_por_fase(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula contagens (2xx/4xx/5xx), taxa de falha (5xx / (2xx + 5xx)),

    mediana e P95 para respostas bem-sucedidas (2xx) por fase.
    """
    col_fase = next((c for c in ["fase", "phase", "stage"] if c in df.columns), None)
    col_status = next((c for c in ["status_code", "status", "status_http", "http_status"] if c in df.columns), None)
    col_duracao = next(
        (c for c in ["duration_ms", "latencia_ms", "latency_ms", "tempo_ms", "duration"] if c in df.columns),
        None,
    )

    if not col_fase or not col_status or not col_duracao:
        raise KeyError(
            f"Colunas do CSV não reconhecidas. Colunas presentes: {list(df.columns)}"
        )

    fases = df[col_fase].unique()
    metricas = []

    for fase in fases:
        df_fase = df[df[col_fase] == fase]

        c_2xx = int(((df_fase[col_status] >= 200) & (df_fase[col_status] < 300)).sum())
        c_4xx = int(((df_fase[col_status] >= 400) & (df_fase[col_status] < 500)).sum())
        c_5xx = int(((df_fase[col_status] >= 500) & (df_fase[col_status] < 600)).sum())

        # Taxa de falha: 5xx / (2xx + 5xx)
        total_validos = c_2xx + c_5xx
        taxa_falha = (c_5xx / total_validos) if total_validos > 0 else 0.0

        # Respostas bem-sucedidas (2xx)
        duracoes_2xx = df_fase[(df_fase[col_status] >= 200) & (df_fase[col_status] < 300)][col_duracao]

        if not duracoes_2xx.empty:
            mediana = float(np.median(duracoes_2xx))
            p95 = float(np.percentile(duracoes_2xx, 95))
        else:
            mediana = 0.0
            p95 = 0.0

        metricas.append(
            {
                "fase": fase,
                "contagem_2xx": c_2xx,
                "contagem_4xx": c_4xx,
                "contagem_5xx": c_5xx,
                "taxa_falha_5xx": taxa_falha,
                "mediana_ms_2xx": mediana,
                "p95_ms_2xx": p95,
            }
        )

    return pd.DataFrame(metricas)


def gerar_incidentes(df: pd.DataFrame, caminho_saida: Path) -> pd.DataFrame:
    """Gera incidentes.csv contendo chamadas rejeitadas (4xx), falhas (5xx)

    e respostas lentas (2xx > 250ms), preservando o request_id original.
    """
    col_status = next((c for c in ["status_code", "status", "status_http", "http_status"] if c in df.columns), None)
    col_duracao = next(
        (c for c in ["duration_ms", "latencia_ms", "latency_ms", "tempo_ms", "duration"] if c in df.columns),
        None,
    )

    cond_4xx = (df[col_status] >= 400) & (df[col_status] < 500)
    cond_5xx = (df[col_status] >= 500) & (df[col_status] < 600)
    cond_lenta = (df[col_status] >= 200) & (df[col_status] < 300) & (df[col_duracao] > 250)

    df_incidentes = df[cond_4xx | cond_5xx | cond_lenta].copy()

    def categorizar(row):
        st = row[col_status]
        dur = row[col_duracao]
        if 400 <= st < 500:
            return "Rejeição (4xx)"
        elif 500 <= st < 600:
            return "Falha do Servidor (5xx)"
        elif 200 <= st < 300 and dur > 250:
            return "Resposta Lenta (>250ms)"
        return "Outro"

    df_incidentes["tipo_incidente"] = df_incidentes.apply(categorizar, axis=1)

    df_incidentes.to_csv(caminho_saida, index=False)
    print(f"Arquivo de incidentes gerado em: {caminho_saida} ({len(df_incidentes)} registros)")
    return df_incidentes


def tomar_decisao_fundamentada(df_metricas: pd.DataFrame, df_incidentes: pd.DataFrame):
    """Gera a decisão fundamentada aplicando a regra didática:

    - Investigar taxa de falha (5xx) > 1%
    - Investigar P95 > 250 ms
    """
    print("\n" + "=" * 60)
    print("DECISÃO FUNDAMENTADA E DIAGNÓSTICO DO SERVIÇO")
    print("=" * 60)

    fases_alta_falha = df_metricas[df_metricas["taxa_falha_5xx"] > 0.01]
    fases_alto_p95 = df_metricas[df_metricas["p95_ms_2xx"] > 250.0]

    if not fases_alta_falha.empty:
        fase_alvo = fases_alta_falha.sort_values(by="taxa_falha_5xx", ascending=False).iloc[0]
        problema_prioritario = f"Disponibilidade / Falhas do Servidor (5xx) na fase '{fase_alvo['fase']}'"
        registros_suporte = df_incidentes[df_incidentes["tipo_incidente"] == "Falha do Servidor (5xx)"]
        acao_recomendada = (
            f"Investigar logs do servidor na fase '{fase_alvo['fase']}' para identificar exceções "
            f"não tratadas (HTTP 5xx). Taxa de falha atingiu {fase_alvo['taxa_falha_5xx']:.2%} (limite: 1.00%)."
        )
    elif not fases_alto_p95.empty:
        fase_alvo = fases_alto_p95.sort_values(by="p95_ms_2xx", ascending=False).iloc[0]
        problema_prioritario = f"Performance / Latência Elevada (P95 > 250 ms) na fase '{fase_alvo['fase']}'"
        registros_suporte = df_incidentes[df_incidentes["tipo_incidente"] == "Resposta Lenta (>250ms)"]
        acao_recomendada = (
            f"Otimizar processamento e gargalos de E/S na fase '{fase_alvo['fase']}'. "
            f"O P95 atingiu {fase_alvo['p95_ms_2xx']:.2f} ms (limite: 250.00 ms)."
        )
    else:
        problema_prioritario = "Nenhum gargalo crítico (Métricas dentro dos limites)"
        registros_suporte = pd.DataFrame()
        acao_recomendada = "Manter monitoramento contínuo. Nenhum parâmetro violou as regras didáticas."

    print(f"\n1. Problema a Priorizar:\n   {problema_prioritario}")
    print(f"\n2. Registros que Sustentam a Escolha:\n   Total de incidentes correlacionados: {len(registros_suporte)}")
    if not registros_suporte.empty:
        col_req = next((c for c in ["request_id", "id", "req_id"] if c in registros_suporte.columns), None)
        amostra_ids = registros_suporte[col_req].head(5).tolist() if col_req else []
        print(f"   Amostra de request_ids afetados: {amostra_ids}")
    print(f"\n3. Ação a Tomar:\n   {acao_recomendada}")
    print("=" * 60 + "\n")


def main():
    # 1. Localização dinâmica da pasta da execução
    arquivo_csv, arquivo_json = encontrar_arquivos_execucao()
    arquivo_incidentes = arquivo_csv.parent / "incidentes.csv"

    # 2. Leitura e checagem flexível de integridade
    verificar_hash(arquivo_csv, arquivo_json)
    df_requests = pd.read_csv(arquivo_csv)

    # 3. Cálculo de métricas por fase
    df_metricas = calcular_metricas_por_fase(df_requests)
    print("\n--- RESUMO DE MÉTRICAS POR FASE ---")
    print(df_metricas.to_string(index=False))

    # 4. Geração de incidentes.csv
    df_incidentes = gerar_incidentes(df_requests, arquivo_incidentes)

    # 5. Decisão fundamentada
    tomar_decisao_fundamentada(df_metricas, df_incidentes)


if __name__ == "__main__":
    main()