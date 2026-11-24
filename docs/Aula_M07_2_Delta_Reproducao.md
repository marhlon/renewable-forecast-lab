# M07.2 — Corrigir dados sem perder a reprodução do treino

**Problema:** uma medição de geração pode ser revisada depois de usada para construir features e alvos. Se você sobrescrever o arquivo original e repetir o mesmo código, o conjunto de treino pode mudar. Nesta aula você vai tornar essa mudança explícita, preservar a versão anterior e calcular quais exemplos dependem da medição corrigida.

A etapa anterior está tecnicamente aceita: 8.760 origens e 7.485 linhas elegíveis no corte. A autoria de `selecionar_treino` foi recebida e executada. Não repita o laboratório temporal para começar esta unidade.

**Entrega desta unidade:** uma tabela Delta com versões 0 e 1, um registro da versão usada no treino, uma comparação dos exemplos afetados, contraprovas de schema e duplicidade e um pequeno planejador autoral de recálculo. O fluxo de referência está completo; nenhuma função vazia bloqueia a execução.

**Escopo:** Spark 4.0.1 e Delta Lake 4.0.1 na mesma imagem Docker já utilizada. A correção é uma simulação identificada, sobre uma cópia de trabalho; não é uma nova medição ONS. Nenhum modelo será treinado e nenhuma melhoria de MAE será inferida dessa alteração.

## 1. O problema com três relógios

Você já separou origem, alvo e disponibilidade. Agora há uma segunda espécie de disponibilidade: a de uma **revisão** do valor.

Imagine a medição de 10/07/2026 às 01h, inicialmente igual a 165,522 MWmed. Em um cenário hipotético, uma revisão posterior informa 177,522. O instante medido continua sendo 01h. A hora em que soubemos da revisão é outra informação.

| Informação | Pergunta respondida |
|---|---|
| Timestamp da medição | De que hora é a geração? |
| Disponibilidade original assumida | Quando o primeiro valor poderia ter chegado? |
| Disponibilidade da revisão | Quando o valor corrigido passou a ser conhecido? |
| Versão Delta / instante do commit | Em qual estado da nossa tabela a mudança foi gravada? |

**Uma versão Delta não é automaticamente um histórico do que o ONS publicou no passado.** A versão 0 criada hoje contém a cópia disponível hoje. Ela pode já incorporar revisões anteriores. O exercício prova reprodução entre snapshots criados nesta execução; não valida disponibilidade histórica da fonte.

Guardar apenas `timestamp + 2h` e filtrar pelo corte protege contra a utilização precoce do alvo original. Não protege, sozinho, contra revisões futuras incorporadas a valores de timestamps antigos.

## 2. Parquet, Delta e snapshot

Parquet organiza dados em arquivos colunares. Uma tabela Delta combina arquivos de dados com um log transacional em `_delta_log`. O log registra quais arquivos compõem cada versão válida da tabela.

Ao corrigir uma linha, a implementação pode escrever novos arquivos e registrar a substituição dos anteriores. Não interprete a presença de arquivos antigos como linhas duplicadas na tabela: o leitor Delta consulta o log para determinar o snapshot. Ler todos os arquivos físicos como se fossem um Parquet comum pode incluir arquivos que já saíram do estado atual.

Um **commit** publica uma nova versão da tabela. Um **snapshot** representa o estado consistente de uma determinada versão. O **time travel** lê esse estado por versão ou por timestamp do histórico da tabela.

```python
base.write.format('delta').mode('errorifexists').save(str(path))

versao_zero = (
    spark.read.format('delta')
    .option('versionAsOf', 0)
    .load(str(path))
)
```

- `format('delta')` seleciona o leitor/escritor que entende o log.
- `errorifexists` impede que esta criação inicial apague uma tabela existente.
- `versionAsOf=0` fixa a entrada. A leitura implícita da versão atual mudaria após uma correção.
- `path` identifica a tabela; `0` só tem significado junto da identidade dessa tabela.

A transação é da tabela Delta. Ela não torna automaticamente atômicos todos os CSVs, JSONs e outros arquivos do laboratório. Para reprodução também importam código, parâmetros, bibliotecas e política de retenção.

## 3. Preparação e comando exatos

Salve o pacote `renewcast_m07_delta_reproducao.zip` na raiz do projeto e execute:

```powershell
Set-Location C:\renewable-forecast-lab
conda activate renewable-forecast
Expand-Archive -LiteralPath .\renewcast_m07_delta_reproducao.zip -DestinationPath .
python notebooks/laboratorio_delta.py
```

O pacote acrescenta `notebooks/laboratorio_delta.py` e os documentos desta unidade. Não substitui `laboratorio_temporal_spark.py` nem suas funções. Extraia uma vez; nas próximas execuções use somente o comando Python.

O lançador usa a biblioteca padrão no Windows. Na primeira execução baixa dois arquivos oficiais, total aproximado de 7,45 MiB, e verifica seus hashes SHA-256. Eles ficam em `data/external/runtime/delta_4_0_1`. Não há instalação de Spark no Conda nem reconstrução da imagem Docker. O contêiner recebe as dependências por montagem somente para leitura e executa sem rede.

Entradas existentes:

- `data/interim/CJU_BA5EIGT_hourly.parquet` — geração original, somente leitura.
- `reports/scale/CJU_BA5EIGT/laboratorio_temporal/treino_autoria.parquet/` — treino aceito nesta sessão, somente leitura.
- `notebooks/laboratorio_temporal_spark.py` — transformação já conferida; é importada e reaproveitada.
- Recibo da imagem Spark em `reports/scale/CJU_BA5EIGT/m07_1/20261019T230058Z_cf2fe669/host_verification.json`.

Saída única desta configuração: `reports/scale/CJU_BA5EIGT/m07_2_delta/`.

Uma execução concluída é reutilizada quando os hashes de entrada, código, configuração e resultados coincidem. Ela não cria novas cópias a cada comando. Se houver falha parcial, a pasta é preservada para diagnóstico; o programa não a apaga nem apresenta sucesso. Outro experimento usa `--output-dir` explícito.

## 4. Leia o código nesta ordem

Abra `notebooks/laboratorio_delta.py`. As funções pedagógicas ficam antes da seção de infraestrutura.

1. `ler_snapshot`: leitura por versão explícita.
2. `validar_correcoes`: contrato do lote que será aplicado.
3. `aplicar_correcao`: condição de atualização e `MERGE`.
4. `diferencas`: comparação completa, respeitando NULL e tolerância numérica.
5. `executar`: encadeamento de criação, reprodução, contraprovas e análise do impacto.

As funções a partir de `preparar_dependencias` abrem o ambiente e conferem entradas. Não é necessário reescrevê-las para aprender Delta.

O código inicializa a extensão `io.delta.sql.DeltaSparkSessionExtension` e o catálogo `org.apache.spark.sql.delta.catalog.DeltaCatalog`. O pacote Python `delta-spark` não é necessário neste desenho porque utilizamos a API DataFrame e Spark SQL com os JARs correspondentes. Essa escolha reduz a alteração no ambiente que já funciona.

## 5. A correção e a importância da chave

O laboratório acrescenta uma coluna `revisao` à cópia Delta. Os registros originais começam em revisão 0. A correção simulada de 10/07 às 01h recebe revisão 1 e soma 12 MWmed ao valor original.

```sql
MERGE INTO delta.`caminho_da_tabela` AS t
USING correcoes AS s
ON t.din_instante = s.din_instante
WHEN MATCHED AND s.revisao > t.revisao THEN
  UPDATE SET val_geracao = s.val_geracao, revisao = s.revisao
```

- `t` é a tabela de destino e `s` é o lote recebido.
- `ON` define quais registros representam a mesma medição.
- A condição de revisão impede reaplicar uma revisão já incorporada.
- O código atribui o novo valor recebido. Ele não soma 12 novamente a cada reenvio.
- Não existe `WHEN NOT MATCHED`: o contrato desta atividade corrige horas existentes. Inserir horas novas seria outra operação, com outras verificações.

Antes do `MERGE`, o código rejeita duas correções para a mesma chave, valores inválidos, chaves inexistentes, revisão mais antiga e mesma revisão com valor divergente. Delta não substitui essas regras de negócio nem oferece automaticamente uma chave primária única para esta tabela.

O reenvio de um lote idêntico deve preservar os dados. **Idempotência dos dados e contagem de commits são propriedades distintas.** Não escreva uma regra de negócio que dependa de toda operação sem alteração deixar o número da versão necessariamente inalterado.

## 6. O experimento completo

O programa executa a seguinte sequência:

1. Copia a geração para Delta, versão 0, e confere igualdade lógica com o Parquet original.
2. Recalcula as features e a seleção de treino a partir da versão 0; compara todas as colunas com `treino_autoria.parquet`, com tolerância de 1e-9 MWmed para doubles.
3. Escreve `snapshot_treino.json` com identidade relativa da tabela, versão, corte, parâmetros e hash do código de features.
4. Tenta um lote duplicado e uma escrita com coluna extra. Ambos devem ser rejeitados sem publicar alteração na tabela.
5. Aplica uma única correção simulada, criando a versão 1, e compara features/alvos antes e depois.
6. Reabre a versão 0 após a correção e demonstra a reprodução do treino original.
7. Reenvia a correção idêntica e confere que os dados não mudaram.

O teste de schema usa uma escrita `append` com coluna inesperada e evolução automática de schema desativada. A rejeição é deliberada. Acrescentar uma coluna por `mergeSchema=true` não é a solução apropriada para um campo inesperado que ainda não foi aprovado no contrato.

## 7. Antes de executar, derive o impacto

Considere uma medição na hora `t`. Com horizonte `h`, atraso `d` e janela `w`:

- Ela é a geração na hora-limite da origem `o = t + d`.
- Ela participa da média das origens `t+d, t+d+1, ..., t+d+w-1`.
- Ela é o alvo da origem `o = t-h`.

A segunda relação vem de inverter a desigualdade da janela:

\[
o-(d+w-1) \le t \le o-d
\quad\Longrightarrow\quad
t+d \le o \le t+d+w-1.
\]

Para `t = 10/07/2026 01h`, `h=24`, `d=2`, `w=6` e correção +12 MWmed:

| Componente | Origens afetadas | Variação esperada |
|---|---|---:|
| Geração na hora-limite | 10/07 03h | +12 MWmed |
| Média de seis horas | 10/07 03h até 08h | +2 MWmed em cada média |
| Alvo h24 | 09/07 01h | +12 MWmed |

Há **sete origens distintas**, pois a origem 10/07 03h aparece em duas linhas da tabela acima. Não some 1+6+1 como se fossem oito exemplos diferentes.

O treino aceito termina em 10/07 às 03h. Portanto, **duas linhas de treino mudariam** ao reconstruí-lo com a versão corrigida: a origem 09/07 01h, pelo alvo, e a origem 10/07 03h, pelas features. As outras cinco origens alteradas não pertencem à seleção desse corte.

Isso não autoriza substituir retrospectivamente o treino original. A comparação com versão 1 é um cenário contrafactual para expor a dependência dos dados. Se a correção só chegou depois do corte, tratá-la como conhecida naquele instante mudaria o experimento histórico.

## 8. Arquivos e leitura do resultado

| Saída | O que verificar |
|---|---|
| `geracao_delta/` | Tabela versionada, incluindo `_delta_log`. Preserve o conjunto. |
| `snapshot_treino.json` | Versão 0 fixada e 7.485 linhas, sob os dados já conferidos. |
| `impacto_correcao.csv` | Sete origens afetadas; deltas por feature/alvo; duas pertencentes ao treino. |
| `historico_delta.json` | Operações e versões publicadas pelo motor Delta. |
| `conclusao.json` | Reprodução, rejeições e idempotência observadas. |
| `verification.json` | Conferência do lançador Windows, hashes de entradas/saídas e imagem usada. |

A medição original de 10/07 01h é 165,522 MWmed nos valores reconstruídos dos anexos desta sessão. Com +12, esperamos 177,522. Se o arquivo bruto local tiver sido revisado desde a entrega, a comparação com o treino aceito deve detectar a diferença, em vez de forçar os valores esperados.

Não apague arquivos antigos dentro da tabela para “limpar” o diretório. O time travel depende de reter o log e os arquivos exigidos pela versão. `VACUUM` é uma operação com política de retenção, não uma faxina genérica. Não executaremos `VACUUM` nesta aula.

## 9. Sua entrega de programação: planejar o recálculo de um lote

**Arquivo a criar por você:** `notebooks/planejar_recalculo_temporal.py`.

Implemente:

```python
def planejar_recalculo(instantes, *, horizonte, atraso, janela):
    """Retorna dict com conjuntos de datetime: historico, media, alvo e todas."""
```

O objetivo é calcular quais origens precisam ser reprocessadas quando várias medições são corrigidas. Use as dependências derivadas acima e a união de conjuntos. Não leia todo o ano nem recalcule features nesta função. Ela produz um plano de impacto; não altera Delta nem a fonte ONS.

Contrato:

- `instantes` contém datetimes sem fuso, no mesmo eixo do exercício; duplicatas na entrada não podem duplicar origens.
- `horizonte` e `janela` são inteiros positivos, `atraso` é inteiro não negativo; booleanos não são parâmetros válidos.
- Entrada vazia retorna quatro conjuntos vazios.
- `todas` é a união de `historico`, `media` e `alvo`.
- As origens calculadas podem cair fora do dataset. Isso é intencional: o recorte pela disponibilidade das linhas e pelo corte de treino é uma etapa posterior.

Casos de aceite, sem rodar Spark novamente:

1. Uma correção em 10/07 01h, h24/d2/w6: tamanhos 1, 6, 1 e **7**. Compare o conjunto `todas` com as origens de `impacto_correcao.csv`.
2. Duas correções em 10/07 01h e 02h: tamanhos 2, **7**, 2 e **9**. As janelas de médias se sobrepõem; 12 seria a contagem errada.
3. Repetir o primeiro timestamp na entrada não altera o plano.
4. Com h6/d0/w1 e um timestamp: o histórico e a média apontam para a própria hora; o alvo aponta para seis horas antes; `todas` tem 2 elementos.

Entregue a função e uma explicação curta: quando você usaria a versão 0 para reproduzir um treino, quando a versão atual seria apropriada e por que a hora da medição não é a hora em que uma correção ficou conhecida. Não é preciso redigir novamente todas as explicações de M07.1: a interpretação pendente pode ser consolidada nessa defesa.

A unidade é encerrada pela execução do cenário, leitura correta do impacto e planejador autoral conferido. A próxima unidade já prevista é M07.3: levar a transformação e o contrato de versões para um ambiente Databricks disponível. Não se contabiliza a entrega deste código como execução no seu Windows ou competência já demonstrada.

## 10. Decisões de engenharia e limites

- Para uma única série de 8.760 horas, pandas/DuckDB continuam suficientes. O motivo de usar Delta aqui é aprender revisão, snapshots e contrato de escrita com Spark. Não há benchmark demonstrando vantagem de velocidade.
- O corte temporal e a versão do dataset são duas entradas do experimento. Nenhuma substitui a outra.
- O manifesto do exercício não é um sistema completo de governança: ainda faltam versões históricas reais da fonte e uma política de retenção operacional.
- Em produção, revisão da fonte, ingestão, materialização de features e artefato do modelo precisam ter uma relação rastreável. Uma tabela correta com um modelo ligado à versão errada continua produzindo uma reprodução incorreta.

## Fontes primárias e verificação

Consultadas em 27/10/2026:

- Compatibilidade Delta/Spark: https://docs.delta.io/releases/
- Release Delta 4.0.1 e correções de compatibilidade com Spark 4.0.1: https://delta.io/blog/2026-01-09-delta-lake-4-0-1/
- Leitura por versão, schema e retenção: https://docs.delta.io/delta-batch/
- MERGE e múltiplas correspondências: https://docs.delta.io/delta-update/
- Artefatos oficiais: https://repo.maven.apache.org/maven2/io/delta/

O professor executou o núcleo com Spark 4.0.1/Delta 4.0.1 em Linux nativo, usando a geração reconstruída dos resultados anexados e comparando contra o Parquet de treino recebido. Isso não substitui um teste Docker no Windows; essa execução ainda deve ocorrer no seu computador. O relatório de verificação no pacote delimita o que foi executado.
