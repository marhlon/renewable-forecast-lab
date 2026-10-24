# M06 — revisão do diagnóstico de serviço

Marlon Alves Bomfim · Renewcast · 05/10/2026

## Entrega reconhecida

A execução `1c51054df97b439fa22c7d2dcc9f6edd` foi auditada nos arquivos enviados: cliente, servidor, requisições conciliadas, resumo, manifesto, incidentes e código autoral. Os quatro hashes de entrada conferem. Há 46 chamadas em cliente/servidor, uma de aquecimento e 45 medidas. As chaves medidas são únicas e os registros correspondem por request_id.

Seu cálculo das fases normal e incident está correto. Os dez IDs de incidentes também: cinco rejeições, três sucessos lentos e duas falhas. Priorizar os 5xx é defensável. A revisão abaixo trata de contrato, denominador e interpretação da causa. Esses pontos não anulam o que foi demonstrado.

| Fase | 2xx | 4xx | 5xx | Elegíveis | Taxa 5xx | Mediana dos sucessos (ms) | P95 dos sucessos (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|
| normal |20|0|0|20|0%|36,02250|43,845195|
| invalid_payload |0|5|0|0|Indefinida|Indefinida|Indefinido|
| incident |18|0|2|20|10%|35,30995|800,741300|

## Quatro mudanças e por que elas importam

**1. Ausência de denominador não vira zero.** Na fase invalid_payload, `5xx/(2xx+5xx) = 0/0`. A taxa fica NaN. Mediana e P95 também ficam NaN porque não há resposta bem-sucedida. A taxa de rejeição pode ser calculada: `5/5 = 100%`. Isso distingue uma medição sem falhas de uma fase sem dados elegíveis.

No cálculo autoral, mantenha a lógica das máscaras. O ponto a alterar é o ramo vazio:

```python
taxa_falha = c_5xx / total_elegiveis if total_elegiveis else np.nan
mediana = float(np.median(duracoes_2xx)) if len(duracoes_2xx) else np.nan
p95 = float(np.percentile(duracoes_2xx, 95)) if len(duracoes_2xx) else np.nan
```

**2. Hash pertence a um campo específico.** Procurar o SHA-256 ou MD5 em qualquer texto do JSON aceita, por exemplo, o hash correto numa observação, mesmo se o hash oficial do arquivo divergir. A relação exigida é:

```python
esperado = metadata["output_sha256"]["requests.csv"]
calculado = hashlib.sha256(requests_path.read_bytes()).hexdigest()
if calculado != esperado:
    raise ValueError("requests.csv diverge do manifesto")
```

Na revisão, cada um dos quatro arquivos recebe essa comparação pelo seu nome exato. Isso verifica consistência com o manifesto; não autentica a autoria do manifesto.

**3. A causa está identificada como injeção.** As duas requisições prioritárias são:

| request_id | Status | Duração (ms) | fault_injection | error_type |
|---|---:|---:|---|---|
|2edffe09155646bfbb27d5e43ecaf82f|500|0,4430|error|ausente|
|4fb0af4d1177493a9c1472605e844cb9|500|0,7331|error|ausente|

O middleware do laboratório retorna intencionalmente HTTP 500 antes do estimador. Portanto, esta evidência não pede que você procure uma exceção não tratada como se ela já estivesse comprovada. O diagnóstico apropriado é: **a instrumentação detectou a falha controlada, registrou seus IDs e acionou a regra de taxa de falha**. Em um incidente real de causa desconhecida, os mesmos IDs serviriam para localizar os logs e investigar.

Também há uma violação de latência. Os três sucessos lentos têm a marca `slow`; não existe evidência aqui para atribuir o atraso a E/S, ao tamanho do modelo ou à carga concorrente. A medição anterior da fase normal não é uma medição posterior de recuperação.

**4. O caminho precisa identificar a execução escolhida.** O último resultado de `sorted(rglob(...))` é o último nome em ordem lexicográfica. Pastas com UUID não ficam ordenadas por data. Além disso, um caminho explícito inválido precisa produzir erro, sem trocar silenciosamente de experimento. O notebook revisado usa `--run-dir` ou o ponteiro `latest_run.json` definido na aula.

## O que a cauda ensina neste caso

Na fase incident, 15 dos 18 sucessos não receberam atraso. Por isso a mediana permaneceu em 35,31 ms enquanto o P95 foi a 800,74 ms. As falhas 500, por sua vez, foram rápidas. Misturar respostas rápidas que falharam com a latência dos sucessos pode esconder o problema.

O P95 usa interpolação linear. Com 18 durações ordenadas, a posição de índice zero é `(18−1)×0,95 = 16,15`. Aqui, os valores adjacentes são 799,4021 e 808,3301 ms:

```text
P95 = 0,85 × 799,4021 + 0,15 × 808,3301 = 800,7413 ms
```

Esse é um resumo das chamadas observadas, não uma promessa sobre 95% das próximas chamadas.

Nas 38 respostas medidas bem-sucedidas, a probabilidade é a mesma para o mesmo pedido e artefato. Isso apoia repetibilidade desse pedido. Não há alvo novo observado, medição de qualidade preditiva ou evidência para retreinar o classificador.

## Aplicar no projeto

Baixe `renewcast_m06_diagnostico_20261005.zip` para `C:\renewable-forecast-lab`. Ele contém:

- `notebooks/diagnostico_servico.py`: cálculo independente, entradas explícitas e gravação das entregas.
- `docs/Revisao_M06_Diagnostico_Servico.md`: esta revisão.
- `docs/Roteiro_Auditavel_Data_Science.md`: estado atual, versão didática 1.43.
- `docs/evidencias_m06_diagnostico_professor/`: resultados da correção executada pelo professor sobre cópias dos seus arquivos reais e registro das verificações.

Com o ambiente renewable-forecast ativo, na raiz do projeto:

```powershell
if (-not (Test-Path .\notebooks\diagnostico_servico_antes_revisao_20261005.py)) {
    Copy-Item .\notebooks\diagnostico_servico.py .\notebooks\diagnostico_servico_antes_revisao_20261005.py
}
Expand-Archive -LiteralPath .\renewcast_m06_diagnostico_20261005.zip -DestinationPath . -Force
python notebooks/diagnostico_servico.py --run-dir reports/service/CJU_BA5EIGT/h24_event_telemetry_v1/1c51054df97b439fa22c7d2dcc9f6edd
```

A única execução necessária é a inspeção dos arquivos já produzidos. O notebook não inicia o servidor, não gera chamadas e não ajusta o modelo. Os arquivos originais da execução são preservados. O resultado fica em:

```text
reports/service/CJU_BA5EIGT/h24_event_telemetry_v1/
  1c51054df97b439fa22c7d2dcc9f6edd/autoria/
    diagnostico.csv
    incidentes.csv
    decisao.md
    conferencia.json
```

O terminal deve informar `33 comparações com summary.csv; 10 incidentes`. Os NaN da fase invalid_payload são o resultado correto. Leia decisao.md nessa pasta. Para registrar a aplicação no Windows, envie o log e `conferencia.json`; os arquivos originais já foram recebidos. Se editar a interpretação por conta própria, envie também essa alteração, distinguindo-a do texto gerado pelo notebook.

## Verificação e limite do aceite

O professor executou a correção nas cópias dos seus arquivos recebidos. As 33 comparações com o resumo passaram, os dez IDs coincidiram com os seus incidentes e os hashes de entrada permaneceram iguais. Foram verificadas as contraprovas de zero indevido, hash no campo errado, caminho explícito inexistente e ID duplicado, além da leitura do ponteiro correto. Python foi executado; PowerShell/Windows não foi executado neste ambiente.

Autoria reconhecida: contagens, fórmula da taxa, percentis nas fases com sucessos, identificação dos dez incidentes e priorização dos 5xx. A correção dos contratos e o novo texto automático são contribuição do professor. Executar a correção comprova reprodução, não autoria independente dessas alterações.

## Fixação lexical e continuidade

| Termo | Significado aplicado aqui |
|---|---|
| Denominador elegível | 2xx + 5xx; define quais chamadas entram nesta taxa de falha |
| Indefinido | Não houve amostra elegível; não pode ser convertido em sucesso medido |
| Linhagem | Caminho, run_id e hash vinculam o diagnóstico à execução específica |
| Correlação | request_id liga uma falha agregada ao registro de cliente e servidor |
| Sintoma | HTTP 500 e P95 elevado são resultados observáveis |
| Causa registrada | As marcas error/slow e o código de injeção explicam os sintomas deste laboratório |
| Recuperação | Exige uma observação posterior à intervenção; a fase normal anterior não basta |

E78 registra sua execução e o núcleo autoral aceitos. E79 registra esta revisão verificada nos anexos; aplicação pelo aluno ainda pendente. M06 continua em andamento. O roteiro não atribui percentual global nem encerra os outros marcos.

A próxima competência de M06 é versionamento e rollback: identificar qual artefato está ativo, substituir a versão sob um contrato e retornar à anterior deixando um registro verificável. Essa unidade usará a identidade dos artefatos e a telemetria já construídas; não exige refazer a carga desta revisão nem repetir o parecer anterior.
