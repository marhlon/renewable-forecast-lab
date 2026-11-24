# M09.3 — usar pesos pré-treinados para prever e decidir

Do ferro ao pró — Data Science · Renewcast · 17/11/2026

**Objetivo:** produzir previsões reais de geração com um modelo temporal pré-treinado, preservar o relógio h24/d2 e compará-las às mesmas 168 origens já usadas no M08.3. A pergunta é se a transferência de pesos traz vantagem de erro, viés ou custo neste recorte. O modelo não precisa vencer para que a unidade seja concluída.

As etapas anteriores cumpriram objetivos diferentes: M09.1 calculou atenção; M09.2 compôs um encoder–decoder, conferiu caminhos de dados/gradientes e persistiu a inicialização. Agora usamos uma arquitetura com **pesos já treinados em outras séries**, com saída numérica no tempo futuro. Não converteremos os seis slots sintéticos da prática anterior em seis horizontes reais.

## 1. Um comando para preparar e executar

Baixe `renewcast_m09_3_pre_treinado.zip` para `C:\renewable-forecast-lab`. Execute:

```powershell
Set-Location C:\renewable-forecast-lab
conda activate renewable-forecast
Expand-Archive -LiteralPath .\renewcast_m09_3_pre_treinado.zip -DestinationPath . -Force -ErrorAction Stop
python scripts/executar_m09_3.py
```

Na primeira execução, o controlador cria **`.venvs/m09_3_chronos`**, instala dependências fixadas para CPU e obtém os pesos públicos do modelo, aproximadamente **33 MiB**. O primeiro preparo também baixa PyTorch e suas dependências, portanto o download total é maior. Não há API paga ou necessidade de GPU. Internet é necessária no primeiro preparo; o ambiente `renewable-forecast` chamador não recebe essas instalações.

Não é necessário ativar manualmente o ambiente privado. O controlador encontra seu executável no Windows ou Linux e inicia o laboratório. A instalação é registrada em `reports/setup/m09_3/instalacao.log`; se falhar, a inferência não é iniciada.

As execuções seguintes reutilizam ambiente e snapshot verificados. Depois do primeiro preparo completo, é possível exigir ausência de downloads:

```powershell
python scripts/executar_m09_3.py --offline
```

**Entradas existentes:** o pacote M07.3 em `dist/databricks/CJU_BA5EIGT/m07_3` e sua execução M08.3 apontada por `reports/neural/CJU_BA5EIGT/m08_3_gru/latest_run.json`. Essa execução contém as previsões dos baselines. Ela será lida e verificada, sem ajustar novamente HGB, MLP ou GRU.

Para escolher explicitamente a execução que você já realizou:

```powershell
python scripts/executar_m09_3.py --baseline-run-dir reports/neural/CJU_BA5EIGT/m08_3_gru/20261115T164955Z_5e435b09
```

Cada inferência cria uma pasta em `reports/transformer/CJU_BA5EIGT/m09_3_pre_treinado/<run_id>`. Para abrir o relatório da última execução completa:

```powershell
$p = Get-Content -Raw .\reports\transformer\CJU_BA5EIGT\m09_3_pre_treinado\latest_run.json | ConvertFrom-Json
Invoke-Item (Join-Path $p.directory 'relatorio.html')
```

## 2. O que está sendo carregado

O candidato prescrito é **`amazon/chronos-bolt-tiny`**, da família Chronos-Bolt, revisão:

```text
a0e552de83495b5c28c14c71c374f3e33280b340
```

Ele tem **8.652.672 parâmetros** nesta revisão. O arquivo `model.safetensors` tem 34.622.352 bytes e SHA-256:

```text
75068728d376d2bec670379eeef4bfb4d24c0cfe24d957451f8d19b447030a32
```

Configuração, pesos e model card são obtidos dessa revisão específica, conferidos e preservados localmente. O programa não passa a seguir silenciosamente uma nova versão de `main`. A licença declarada é Apache-2.0. As dependências da interface também estão fixadas, com `chronos-forecasting==1.5.3`, `transformers==4.49.0` e PyTorch `2.7.1+cpu`, combinação executada na preparação desta entrega.

A escolha desse modelo compacto responde ao orçamento de CPU e permite ligação direta com encoder–decoder. Não afirma que ele seja o modelo mais recente ou o melhor da família. Variantes maiores ou de outra geração seriam outros experimentos.

**Zero-shot neste laboratório** significa que não ajustamos os pesos com os dados locais. O modelo já foi treinado pelo fornecedor; não significa ausência de treinamento, ausência de conhecimento prévio ou garantia de que todas as fontes do benchmark sejam inéditas para ele. A sobreposição exata com o corpus de pré-treino não foi verificada.

## 3. Do histórico aos quantis

Chronos-Bolt organiza o contexto em patches e usa representações de um encoder–decoder baseado em T5 para gerar diretamente quantis de múltiplos passos. Isso difere da prática com representações aleatórias e também do Chronos original, que usa discretização e amostragem de trajetórias. Nesta variante, `pipeline.predict` devolve nove quantis fixos por passo, não vinte amostras aleatórias.

O código envia geração bruta em MWmed, `[B,24]`. A normalização interna da interface do modelo é aplicada ao contexto disponível. Não aplicamos antes os normalizadores por lag da MLP: isso alteraria a interpretação do pré-treinamento e exigiria uma transformação inversa própria. Todos os métodos recebem as mesmas 24 medições disponíveis; as transformações internas de cada modelo diferem.

| Objeto | Shape | Significado |
| --- | --- | --- |
| Contexto | `[B,24]` | Vinte e quatro medições históricas por origem |
| Saída bruta | `[B,9,26]` | Nove quantis para os próximos 26 passos |
| Níveis | `[9]` | 0,1; 0,2; …; 0,9 |
| P50 alinhado | `[B]` | Previsão pontual do alvo h24/d2 |
| P10/P90 alinhados | `[B]` cada | Limites do intervalo preditivo bruto |

O contexto máximo configurado no modelo é maior que 24, mas esta comparação fixa **24 horas** para preservar a informação oferecida aos baselines. Usar um contexto longo apenas no modelo pré-treinado responderia a outra pergunta. Não estamos medindo o melhor desempenho possível de cada família.

## 4. O erro de duas horas que precisamos impedir

A última medição disponível em uma origem `o` é `history_end=o−2h`. O alvo é `o+24h`. Logo:

\[
\text{passos desde o último dado}=(o+24)-(o-2)=26\text{h}.
\]

Na origem **03/07/2026 04h**:

| Campo | Horário |
| --- | --- |
| Primeira medição do contexto | 02/07 03h |
| Última medição disponível | 03/07 02h |
| Primeiro passo previsto | 03/07 03h |
| Passo 24 | 04/07 02h — ainda não é o alvo |
| **Passo 26** | **04/07 04h — alvo correto** |
| Disponibilidade assumida do alvo | 04/07 06h |

Em índices Python, o passo 26 corresponde ao índice **25**. Solicitar 24 passos e usar o último produziria uma previsão para duas horas antes do alvo. Essa previsão poderia ter um erro numérico atraente e ainda assim ser uma comparação inválida.

A função `alinhar_quantis` calcula a distância temporal por exemplo e escolhe o índice correspondente. Não presume que todas as tarefas tenham o mesmo horizonte, embora a configuração deste experimento resulte em 26 para todas as linhas. A conferência inclui outro exemplo com lead de cinco horas e rejeita trajetória curta, alvo não posterior, diferença não horária e quantis duplicados.

O eixo de tempo permanece o NTZ do pacote M07, com disponibilidade assumida. Não foi resolvida nesta aula a verificação física do fuso ou a semântica original do intervalo de geração.

## 5. Comparação com as referências que você já produziu

O programa lê `predictions.csv`, `resultado.json`, protocolo, partições e normalizadores da execução M08.3. Confere hashes, pacote de entrada, mesmas origens e mesmos alvos. Não busca outro experimento se o caminho fornecido estiver errado.

O P50 é escolhido **antes de calcular o desempenho**, como previsão pontual principal. Todas as sementes MLP/GRU permanecem na tabela. Não escolhemos retrospectivamente uma semente para favorecer ou prejudicar o candidato.

As métricas continuam sendo MAE, RMSE e viés observado−previsto. Viés positivo indica subestimação. O ganho relativo ao HGB é `(MAE_HGB−MAE_candidato)/MAE_HGB`; valor positivo significa redução de MAE.

As 168 origens já foram examinadas em unidades anteriores. Este é um benchmark de desenvolvimento, não um teste final intocado. Mesmo um ganho observado não demonstra superioridade estatística geral nem autoriza substituir o serviço HTTP do projeto.

## 6. O resultado que já executei

Referência Linux/CPU, com o pacote M07.3 do professor e baselines Linux M08.3. O controlador foi executado em ambiente privado criado do zero, sem herdar os pacotes globais:

| Método | MAE | RMSE | Viés observado−previsto |
| --- | ---: | ---: | ---: |
| Persistência d2 | 37,991646 | 55,434342 | −3,016872 |
| Linear 24h | 33,678664 | 44,938111 | +15,148681 |
| HGB 24h | 31,846768 | **44,051119** | +11,662000 |
| Chronos-Bolt Tiny P50 | **31,340739** | 45,380137 | +2,962412 |

O candidato reduz MAE em **1,59%** frente ao HGB dessa referência e reduz a subestimação média, mas tem RMSE maior. Isso é um resultado favorável em dois critérios e desfavorável em outro, não uma aprovação automática.

No seu Windows, o HGB M08.3 teve MAE 32,323956. O laboratório vai reutilizar **esse resultado local**, com sua proveniência, em vez de substituir a referência por 31,846768. Também não promete que as previsões pré-treinadas sejam idênticas entre plataformas; a primeira comparação válida é a produzida pela sua execução e seus hashes.

O arquivo `comparacao_pareada.csv` permite localizar onde o ganho ocorre e onde ele falha. Não atribua uma causa meteorológica a esses resíduos sem dados que a sustentem. Todos os modelos desta comparação usam apenas geração histórica.

## 7. Intervalos e custo: duas perguntas adicionais

O modelo produz P10/P50/P90. Medimos pinball, cobertura, taxas abaixo/acima, largura e interval score; não corrigimos, ordenamos ou recortamos as previsões silenciosamente. Cruzamentos e medianas negativas são contados. P10 e P90 são quantis preditivos, não limites de confiança da média.

Na referência executada, a cobertura bruta foi **80,36%**, a largura média **83,60 MWmed** e não houve cruzamento entre P10/P50/P90 nos alvos. Uma frequência agregada próxima de 80% em uma semana não prova calibração condicional, estabilidade temporal ou a mesma cobertura em produção. O intervalo não foi recalibrado.

Separadamente, registramos carga do modelo, aquecimento, tempo por lote e pico de memória do processo. Não comparamos tempo de inferência do Chronos com tempo de treinamento da GRU como se fossem a mesma operação. Instalação e download são custos do primeiro preparo, distintos da inferência com cache. O pico de memória inclui bibliotecas e dados, não apenas pesos.

O programa não faz `fit`, fine-tuning ou `optimizer.step()`. O teste de repetição compara a mesma entrada com os mesmos pesos congelados; isso confere reprodutibilidade dentro daquela execução, não acurácia.

## 8. Arquivos de trabalho

| Arquivo | Pergunta respondida |
| --- | --- |
| `scripts/executar_m09_3.py` | Qual ambiente será usado? Como instalar/reutilizar com segurança e interromper no erro? |
| `notebooks/laboratorio_pre_treinado.py` | Como os dados, baselines, inferência e métricas se conectam? |
| `notebooks/m09_pre_treinado_core.py` | Como fixar os arquivos e alinhar o alvo por timestamp? |
| `docs/model_source_m09_3.json` | Qual revisão e quais bytes do modelo foram prescritos? |
| `docs/requirements_m09_3.lock.txt` | Quais dependências foram fixadas? |
| `alinhamento_alvos.csv` | Qual passo foi usado para cada origem e cada alvo? |
| `trajetorias_26_passos.csv` | O que foi previsto em cada um dos 26 passos? |
| `quantis_26_passos.npz` | Saída numérica completa `[168,9,26]`, antes de selecionar o alvo |
| `summary.csv`, `predictions.csv`, `comparacao_pareada.csv` | Métricas e erros pareados com todas as referências |
| `quantile_metrics.json` | Qualidade dos quantis e do intervalo bruto |
| `protocol.json`, `resultado.json` | Configuração, proveniência, versões, verificações e hashes |

As evidências do professor ficam em `docs/evidencias_m09_3_professor/`, separadas das suas execuções. O pacote não inclui o ambiente nem os 33 MiB de pesos; eles serão preparados e preservados no seu projeto.

## 9. Seu trabalho e o encerramento do M09

O experimento normal já funciona. Para praticar a adaptação de uma API pré-treinada, crie **`notebooks/m09_alinhamento_autoral.py`** com:

```python
def alinhar_quantis(forecast, quantile_levels, history_end, target_times):
    # forecast[B,Q,P]; niveis[Q]; dois vetores de timestamps[B]
    # Devolver: lead_hours, index_zero_based, p10, p50, p90
    ...
```

Calcule o passo a partir dos timestamps no mesmo eixo sem fuso, valide se ele existe na trajetória, localize os níveis 0,1/0,5/0,9 e extraia cada exemplo nos eixos corretos. Preserve entradas. Não fixe 26/25 no corpo da função: esses são resultados deste protocolo, não definições universais do alinhamento. A função de referência está disponível para consulta depois da sua tentativa.

Confira sua função no ambiente Conda existente, sem carregar o Chronos nem treinar:

```powershell
python notebooks/laboratorio_pre_treinado.py --autoria notebooks/m09_alinhamento_autoral.py --verificar
```

Neste novo laboratório, `--autoria` sem caminho também usa o nome acima. No laboratório antigo de atenção, que você já executou, a opção ainda exige o caminho completo: `--autoria notebooks/m09_atencao_autoral.py`. São interfaces registradas; o erro de argumento não significa falha no algoritmo.

Escreva **`reports/parecer_m09_pre_treinado.md`** com uma decisão integrada, sem outro treinamento:

1. Mostre em uma origem real por que o passo correto é 26, com fim do histórico, alvo e índice.
2. Explique como o bloco não treinado M09.2 difere do modelo pré-treinado usado agora. Inclua o papel das consultas do decoder e por que seis slots não definiam seis horas.
3. Compare erro, viés e custo da sua execução, mantendo todas as sementes de referência. Diga qual candidato você mantém em desenvolvimento e por qual critério.
4. Interprete cobertura/largura sem prometer calibração futura e registre a limitação de pré-treino e de semana já examinada.

Entrega: saída do controlador, `summary.csv`, `resultado.json`, sua função e o parecer. Isso pode consolidar as interpretações M08.3/M09.1/M09.2 que ainda não foram recebidas como defesa própria. Não é necessário refazer os laboratórios já aceitos.

O encerramento exige alinhamento válido, comparação pareada identificável e defesa coerente. Depois segue M10, o produto de anomalias em telemetria. Operação contínua/CI do P1 permanecem entregas próprias; não serão declaradas realizadas por este benchmark.

## Fontes primárias

- [Model card oficial Chronos-Bolt Tiny](https://huggingface.co/amazon/chronos-bolt-tiny), preservado no snapshot: arquitetura, quantis diretos, tamanhos e licença.
- [Código da interface oficial](https://github.com/amazon-science/chronos-forecasting): esta execução fixa a versão1.5.3 e usa `ChronosBoltPipeline.predict`.
- [Chronos — artigo](https://arxiv.org/abs/2403.07815): contexto de pré-treinamento e limites das comparações. Não atribuímos ao Chronos-Bolt todas as escolhas de tokenização do Chronos original.

As métricas desta aula foram medidas nos arquivos de referência incluídos; não são resultados promocionais extraídos do model card.
