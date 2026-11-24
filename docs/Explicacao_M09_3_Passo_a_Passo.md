# M09.3: do contexto histórico à previsão alinhada

Esta unidade usou Chronos-Bolt Tiny com pesos pré-treinados congelados para
prever geração. O laboratório reuniu essas previsões às referências Windows
já produzidas, sem ajustá-las novamente. A execução autoral examinada é
`20261117T213329Z_3b201a01`; a decisão integrada fica no
[parecer](../reports/parecer_m09_pre_treinado.md).

## 1. O que mudou em relação ao bloco anterior

Na M09.2, o encoder–decoder tinha parâmetros aleatórios e devolvia
representações de 16 coordenadas. Suas seis consultas eram zeros projetados
com posição: slots para estudar a composição, sem significado automático
de seis horas futuras.

Agora há pesos treinados anteriormente em outras séries e uma cabeça que
produz quantis de geração para passos futuros. Chronos-Bolt organiza o
contexto em patches e usa um encoder–decoder baseado em T5. Seu decoder
parte de um token de início e a cabeça produz quantis diretamente. Não
reaproveitamos os seis slots da prática anterior. Essa estrutura consta do
[código oficial da versão 1.5.3](https://github.com/amazon-science/chronos-forecasting/blob/v1.5.3/src/chronos/chronos_bolt.py).

Zero-shot significa que os pesos não foram ajustados com estes dados locais.
Não significa que o modelo nunca foi treinado ou que a série está comprovadamente
ausente de seu pré-treino. Essa sobreposição não foi verificada.

## 2. Qual modelo e qual ambiente foram usados

O snapshot é `amazon/chronos-bolt-tiny`, revisão
`a0e552de83495b5c28c14c71c374f3e33280b340`, com **8.652.672 parâmetros**.
O arquivo `model.safetensors` tem 34.622.352 bytes e SHA-256:

```text
75068728d376d2bec670379eeef4bfb4d24c0cfe24d957451f8d19b447030a32
```

Configuração, model card e pesos foram preservados e verificados por tamanho
e hash. A revisão fixa evita seguir alterações posteriores de `main`.
A [configuração publicada](https://huggingface.co/amazon/chronos-bolt-tiny/blob/a0e552de83495b5c28c14c71c374f3e33280b340/config.json)
registra os nove quantis e o horizonte interno de 64 passos.

O controlador usa `.venvs/m09_3_chronos`, separado do Conda chamador.
Nesta execução: Python 3.12.13, PyTorch 2.7.1+cpu, Chronos 1.5.3,
Transformers 4.49.0, NumPy 2.3.5 e pandas 2.2.3. O preparo anterior deixou
ambiente e snapshot prontos; a execução autoral os reutilizou offline.
A inferência usa CPU/float32; o alinhamento NumPy trabalha em float64.
Se o ambiente ou um arquivo exigido estiver ausente ou divergente, o modo
offline interrompe o processo, sem tentar substituir o snapshot por download.

## 3. O contexto enviado ao modelo

Cada origem recebe as mesmas 24 medições disponíveis oferecidas aos baselines.
A entrada é geração bruta em MWmed, `[B,24]`. Não aplicamos os normalizadores
por lag da MLP. Chronos-Bolt calcula sua normalização interna sobre o contexto
disponível e transforma a saída de volta à escala original.

As referências vêm da execução Windows `20261115T170309Z_90a6625f`.
O programa verifica seus arquivos, o mesmo pacote de entrada e o pareamento
das 168 origens e alvos. Todas as sementes MLP/GRU permanecem na comparação.
Não existe novo `fit`, fine-tuning ou passo de otimizador.

## 4. Por que o alvo exige 26 passos

O horizonte h24 começa na origem. O primeiro passo do modelo começa depois
da última medição disponível, que está duas horas antes da origem:

```text
history_end = origem - 2h
alvo        = origem + 24h
distância   = 26h
```

| Campo na primeira origem | Timestamp no eixo da entrada |
|---|---|
| Origem | 03/07/2026 04h |
| Início do contexto | 02/07/2026 03h |
| Fim do contexto | 03/07/2026 02h |
| Primeiro passo previsto | 03/07/2026 03h |
| Passo 24 | 04/07/2026 02h |
| Alvo correto, passo 26 | 04/07/2026 04h |

O índice Python do passo 26 é **25**, pois o índice zero representa
`history_end + 1h`. Usar o passo 24 compararia uma previsão de duas horas
antes com o alvo errado, mesmo que seu erro parecesse pequeno.

## 5. Como `alinhar_quantis` faz a seleção

A [função implementada](../notebooks/m09_alinhamento_autoral.py) recebe:

| Entrada | Shape |
|---|---|
| `forecast` | `[B,Q,P]` |
| `quantile_levels` | `[Q]` |
| `history_end` | `[B]` |
| `target_times` | `[B]` |

No run completo, a saída bruta é `[168,9,26]`. **Q é o eixo dos quantis**,
de 0,1 a 0,9; P é o eixo dos passos. Não são nove amostras aleatórias.
P50 é a mediana prevista, escolhida previamente como previsão pontual.

A função converte previsões e níveis para float64. Exige três dimensões
positivas, um nível por coluna Q, valores finitos, níveis distintos,
crescentes e dentro de `(0,1)`. Cada vetor temporal precisa identificar
exatamente os B exemplos, sem `NaT`.

Timestamps com fuso explícito são recusados, preservando o eixo sem fuso
do projeto. Isso impede uma conversão implícita; não comprova qual fuso
físico o arquivo deveria ter. Diferenças temporais precisam ser positivas
e múltiplas exatas de uma hora.

As subtrações usam inteiros Python para evitar overflow entre timestamps
em nanossegundos. Para cada linha, calculam-se `lead_hours` e
`index_zero_based = lead_hours - 1`. A trajetória precisa alcançar esse índice.
Os quantis 0,1/0,5/0,9 são localizados com tolerância absoluta `1e-12`,
exigindo uma ocorrência única.

A extração combina três índices: linha, coluna do quantil e passo daquela
linha. O retorno contém exatamente `lead_hours`, `index_zero_based`,
`p10`, `p50` e `p90`, todos vetores `[B]`. Não se modifica nenhuma entrada,
inclusive quando os arrays estão somente para leitura.

A conferência inclui um segundo exemplo com cinco horas de distância:
ele usa índice 4. A regra não fixa 26 dentro da função. Minutos iguais
também são permitidos: de 02h30 a 07h30 há cinco horas inteiras. De 02h30
a 07h há quatro horas e meia e o caso é rejeitado. O que importa é a
distância, não obrigar cada timestamp a terminar em `:00`.

## 6. Por que os quantis são preservados como saíram

P10/P50/P90 são selecionados sem ordenar previsões, recortar negativos ou
corrigir cruzamentos. Ordenar valores esconderia uma falha do modelo e
mudaria o resultado medido. Níveis crescentes identificam as colunas;
não garantem que seus valores previstos estejam sempre ordenados.

Neste run não houve cruzamento entre os três quantis selecionados nem
P50 negativo. Isso foi observado, não obtido por clipping. O intervalo
P10–P90 permaneceu bruto, sem recalibração.

## 7. O que os erros Windows mostraram

Nas mesmas 168 origens, em MWmed:

| Medida | Chronos-Bolt Tiny P50 | HGB histórico |
|---|---:|---:|
| MAE | 31,340738 | 32,323956 |
| RMSE | 45,380136 | 44,221683 |
| Viés observado − previsto | +2,962412 | +13,119039 |

O ganho de MAE foi **3,041763%**, calculado como
`100 × (MAE_HGB - MAE_Chronos) / MAE_HGB`. A redução média de erro absoluto
foi 0,983218 MWmed. Chronos teve erro absoluto menor em 95 das 168 origens.

O viés positivo significa subestimação média; ela diminuiu, mas não zerou.
O RMSE piorou, pois dá maior peso aos erros grandes. Esse conjunto de
medidas sustenta uma decisão com critérios explícitos, sem declarar um
vencedor universal. São os resultados Windows, não os números Linux da aula.

## 8. Como ler a cobertura e o custo

O intervalo bruto P10–P90 incluiu **135 de 168 alvos**, cobertura de
**80,357143%**. Vinte alvos ficaram abaixo de P10 e treze acima de P90.
A largura média foi **83,595237 MWmed**. P10 e P90 são quantis preditivos,
não um intervalo de confiança da média.

Cobertura agregada próxima de 80% numa semana não demonstra calibração em
todos os regimes ou períodos. Um intervalo muito largo pode cobrir bastante
e ser pouco útil; por isso o laboratório também registra largura, pinball
e interval score. A dependência temporal entre as origens permanece.

Os custos foram separados:

| Operação nesta execução | Tempo |
|---|---:|
| Carregar o modelo | 0,174339 s |
| Aquecer com uma origem | 0,024015 s |
| Inferir os lotes das 168 origens | 0,198840 s |

Foram usados lotes de até 16 e dois threads de CPU. Esses tempos não
incluem instalação ou download. Comparar essa inferência com o tempo de
treinamento da GRU misturaria operações distintas. O pico de **397,292969 MiB**
pertence ao processo inteiro, incluindo bibliotecas e dados, sem isolar
a memória dos pesos. A repetição da mesma entrada teve diferença zero
dentro desta execução; isso verifica repetibilidade, não acurácia.

## 9. Como repetir a conferência ou a inferência

Para conferir somente o alinhamento no Conda existente, sem carregar o modelo:

```powershell
python notebooks/laboratorio_pre_treinado.py --autoria --verificar
```

Com ambiente privado e snapshot já preparados, a inferência autoral offline é:

```powershell
python scripts/executar_m09_3.py --autoria --offline --baseline-run-dir reports/neural/CJU_BA5EIGT/m08_3_gru/20261115T170309Z_90a6625f
```

`--autoria` sem caminho usa `notebooks/m09_alinhamento_autoral.py`.
No run completo, `protocol.json` registra o hash dessa função e a referência
utilizada. O relatório, alinhamentos, trajetórias e quantis completos ficam
na pasta identificada da execução.

Esta é uma semana de desenvolvimento já examinada. A inferência com pesos
congelados não a transforma em teste final intocado. A sobreposição com o
pré-treino continua desconhecida, e os resultados não autorizam promoção
operacional. O parecer liga a implementação, os arquivos e a decisão
provisória sem exigir outro treinamento.

## 10. Como conferir a entrega sem repetir o modelo

Passaram os cinco grupos da conferência integrada e os dez testes de unidade
do alinhamento. Os testes adicionais cobrem o último passo disponível,
distâncias diferentes no mesmo batch, quantis extras ou ambíguos,
arrays somente para leitura, instantes inválidos e preservação de valores
negativos ou cruzados. Para repeti-los no ambiente Conda:

```powershell
python -m unittest discover -s tests -p test_m09_alinhamento_autoral.py -v
```

O [script de auditoria](evidencias_m09_3_local/auditar_resultados.py)
recalcula as métricas a partir dos arquivos e verifica as identidades,
sem chamar a função autoral ou executar Chronos novamente:

```powershell
python docs/evidencias_m09_3_local/auditar_resultados.py
```

Seu [resultado](evidencias_m09_3_local/auditoria_resultados.json) complementa
o [registro de execução](evidencias_m09_3_local/registro_execucao.json).
O registro distingue os comandos observados dos números recalculados;
não substitui um log bruto do terminal. Os gráficos do parecer também
partem dos CSVs preservados da execução.
