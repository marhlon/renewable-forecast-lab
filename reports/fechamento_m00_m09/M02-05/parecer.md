# M02-05 — reconstrução do bootstrap pareado

25/11/2026 · Responsável pela implementação, contraprovas e interpretação: Codex, com assistência declarada. A revisão do código e o cadastro do item cabem à revisão seguinte. Esta entrega não certifica autonomia do aluno nem novo aceite do professor.

Completei `summarize` e a CLI de `src/renewable_forecast/weather_gain_uncertainty.py`. O arquivo local e a única revisão Git localizada terminavam em `rows = []`: não retornavam o resumo nem ofereciam a execução completa pela linha de comando. A busca focada não recuperou outra fonte completa. Os hashes das duas versões incompletas e o commit consultado estão no protocolo. Isso não significa que a implementação histórica nunca tenha existido.

O protocolo foi registrado antes da primeira execução. As emendas também antecederam suas respectivas conferências: acrescentaram rejeição de overflow e corrigiram um rótulo sobre retenção de arquivos temporários, sem mudar o estimando ou selecionar um resultado favorável.

## O cálculo que foi implementado

Para cada emissão, a função calcula:

```text
ganho = abs(alvo - previsão_história)
      - abs(alvo - previsão_história_meteorologia)
```

Ganho positivo significa menor erro absoluto para história+meteorologia. A unidade é MWmed. O pareamento importa: alvo e duas previsões precisam se referir à mesma emissão. Reamostrar o delta mantém esse vínculo; sortear as duas séries de erros separadamente mudaria a pergunta.

A função ordena as emissões, valida os dados e separa os folds. Dentro de cada fold, sorteia inícios de blocos consecutivos. Se o bloco chega ao fim daquele fold, retorna ao começo dele. Depois corta a sequência para manter exatamente o número original de observações. Nenhum bloco consulta o fold vizinho.

Um exemplo de índices, com cinco observações, bloco de duas e inícios `[4, 1, 3]`, é `[4, 0, 1, 2, 3]`. O sexto índice é descartado. Esse retorno circular é uma regra da reamostragem, não uma reconstrução de medições nem uma garantia de dependência temporal bem representada.

Cada réplica mantém os tamanhos dos folds. O agregado combina as médias das réplicas com peso `n_do_fold / n_total`. O ganho observado usa a mesma média por emissão. Os limites do agregado são os percentis das **réplicas agregadas**; não são médias dos limites dos folds.

O retorno contém uma linha por fold e outra agregada para cada comprimento de bloco. Informa contagens, MAEs observados, ganho médio, média bootstrap, limites percentis nominais de 95%, fração de réplicas não positivas, seed e número de réplicas. Essa fração é descritiva e não foi chamada de p-valor.

## Controles de entrada e reprodução

Chamadas diretas e leitura CSV passam pela mesma validação: colunas obrigatórias, timestamps válidos e únicos, folds inteiros positivos em ordem temporal, pelo menos duas emissões horárias sem lacunas por fold e valores reais finitos. Um delta já gravado precisa coincidir com as previsões. Booleanos usados como números, colunas duplicadas, parâmetros inválidos e overflow aritmético são rejeitados explicitamente.

Os blocos devem ser inteiros distintos, positivos e menores que o menor fold; `summarize` exige pelo menos mil réplicas. Cada combinação de seed, tamanho do bloco e fold usa um gerador NumPy local. Reordenar os blocos pedidos não muda a corrente de sorteios de cada combinação. As entradas e o RNG global são preservados.

A CLI recebe `--predictions`, `--output-dir`, `--block-hours`, `--repetitions` e `--seed`. Produz `summary.csv` e `receipt.json`, sem sobrescrever esses arquivos se já existirem. O recibo registra comando, datas UTC, versões, parâmetros, contagens, código, hashes da entrada e da saída, além dos limites do cálculo. A entrada é conferida novamente antes de publicar o resultado.

Os padrões são blocos de 6/24/48 horas, 5.000 réplicas e seed 42. A implementação completa original não foi recuperada; portanto, não se promete identidade bit a bit dos intervalos históricos E42/E47. Preservar método, dados e seed não basta para presumir a mesma sequência quando a organização dos sorteios mudou.

## Evidências obtidas com casos pequenos

As conferências foram executadas no Windows, com Python 3.12.13, NumPy 2.5.3, pandas 3.0.5 e pytest 9.1.1. O resultado é **59 contraprovas aprovadas, nenhuma falha e nenhuma ignorada**, com saída zero. O comando integral, datas, stdout, propriedades dos casos e hashes reais estão em `resultado.json` e `contraprovas.json`. O histórico das primeiras conferências foi preservado.

Todos os números abaixo pertencem a exemplos fabricados:

| Contraprova | Resultado observado | Erro que detecta |
| --- | --- | --- |
| Fold com 3 ganhos iguais a 1 e fold com 5 ganhos iguais a 3 | Agregado 2,25; limites 2,25/2,25 | Média de folds sem peso daria 2; misturar folds na reamostragem acrescentaria variação artificial |
| Erros `[2, 6, 10]` contra `[1, 5, 9]` | Ganho 1; limites 1/1 | Perder o pareamento entre as duas previsões |
| Cinco valores, bloco 2, 1.031 réplicas, seed 17 | Primeiros inícios `[3, 4, 0]`; média manual e da função 14,6; diferença máxima zero | Não circular, não cortar para n ou alterar a ordem dos blocos |
| Dois folds variáveis de tamanhos 3 e 5 | Ganho 3,125; IC manual e da função `[0,49375; 5,625]` | Combinar limites por fold em vez das réplicas ponderadas |
| CLI sobre fixture de oito linhas | CSV com seis linhas, recibo e hashes conferidos; segunda chamada recusada com saída 2 | Publicar sem identidade da entrada/saída ou sobrescrever evidência |

Também passaram as verificações de determinismo, ordem dos blocos/linhas, preservação das entradas e do RNG global, delta inconsistente, timestamps/folds inválidos, lacunas, não finitos e overflow. O primeiro run emitiu apenas um aviso de acesso ao cache opcional do pytest; os seguintes desabilitaram esse cache. Não houve solicitação de elevação nem alteração de permissões.

Um metadado inicial dizia que os temporários seriam descartados, mas isso não foi comprovado: o pytest pode retê-los. O rótulo foi corrigido e a história registra a correção. Não se declara limpeza desses arquivos. A evidência da CLI registra comandos, recibos e hashes reais dos arquivos que foram produzidos.

## Alcance e decisão

C1 e C2 têm evidência técnica de construção e contraprovas pequenas. O item fica preparado para revisão, sem mudança do cadastro por esta implementação.

**M02-08 não foi executado.** Não houve bootstrap dos CSVs reais E41/E46, treino, inferência, novo benchmark, rede, GUI, CI ou implantação. Nenhum ganho real ou intervalo histórico foi recalculado nesta entrega.

O bootstrap é condicional às previsões, folds e blocos fornecidos. Não corrige seleção prévia, não estabelece causalidade, não comprova desempenho futuro e não transforma um período já explorado em teste intocado. Interpretar timestamps como UTC também não comprova seu significado físico nem a disponibilidade histórica das fontes.
