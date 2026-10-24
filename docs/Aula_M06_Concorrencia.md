# M06.4 — concorrência, vazão e decisão sobre recursos

Marlon Alves Bomfim · 13/10/2026 · E87: migração aceita · E88: experimento e autoria

## 1. O que foi concluído

Seu run `20261013T185650Z_ffc01dd8` demonstrou a execução da mesma API e do mesmo modelo em um contêiner Linux. Os nove anexos foram lidos. O hash do recibo confere com o ponteiro; os sete hashes das saídas conferem com os arquivos enviados. A resposta inteira coincide com a referência Windows, não apenas a probabilidade.

| Evidência | Valor conferido |
| --- | --- |
| Destino | Linux/amd64, Python 3.12.13 |
| Dependências | 26 distribuições; versões iguais às capturadas no Windows |
| Modelo | `7ab0a5cbc45a47df62b3ce44166f090b0ab686481aa37872d25e7c6353a1e17d` |
| Política | `309906646dabc7a998a05071982b56dfad1fda140b45383e7b5e3b02d41decb7` |
| Probabilidade Windows e Linux | `0.20465385372296466` em ambos |
| Diferença absoluta | `0.0`, dentro de `1e-12` |
| Contrato HTTP | 200 no pedido válido; 422 quando falta `lag_1h` |
| Imagem | `sha256:ec1b7b36cf72f6a7610389c6c27cc7b4a1500a0d03d669d9472317f2e45f8c52` |
| Tamanho informado pelo Docker | 228.996.849 bytes = 218,3884 MiB |

O log mostra wheels `manylinux` para NumPy, SciPy, pandas, scikit-learn e pydantic-core, instalação com verificação de hashes e `pip check` sem dependências quebradas. O contêiner usa usuário `10001:10001`, raiz somente para leitura e porta publicada em localhost. Os binários do modelo e a imagem não foram reenviados; a conferência do professor é documental, cruzada com os recibos e logs. Não é uma segunda execução Docker.

O tamanho da imagem não equivale aos 68,68 MiB do wheelhouse Windows. São objetos de medição diferentes: a imagem contém o ambiente de execução e camadas, enquanto o orçamento anterior somava arquivos `.whl` compactados. Comparar os dois números não mede sozinho uma ineficiência.

**Correção na sua interpretação:** transportar os mesmos bytes e fixar versões permite controlar a migração; não garante invariância em qualquer sistema operacional, arquitetura ou entrada. Há bibliotecas nativas, instruções de CPU e operações em ponto flutuante. Uma diferença pequena nas entradas de uma árvore pode até mudar o ramo escolhido. A tolerância é um critério de comparação, não uma prova de portabilidade universal. Modelo, política, esquema e decisão também precisam permanecer coerentes.

Sua conclusão defensável é: **a migração preservou a resposta para o pedido, o artefato e os dois ambientes avaliados**. Reconheço a distinção que você fez entre artefato lógico e wheel específico da plataforma. A execução Docker está aceita; a correção conceitual fica registrada, sem pedir que repita a execução ou copie um novo parecer.

## 2. A pergunta que avança o projeto

Uma resposta correta em baixa carga não informa o que acontece quando várias chamadas chegam juntas. Agora vamos investigar:

> Com a mesma imagem e o mesmo orçamento de recursos, aumentar os clientes de 1 para 4 e 8 aumenta a vazão útil ou apenas a espera?

Isso conecta Pesquisa Operacional, desenho de experimento e MLOps. Sua entrega será uma decisão fundamentada sobre uma configuração, incluindo o caso em que nenhuma atende ao critério. Não há obrigação de encontrar um ganho.

O modelo recebe um único pedido fixo repetido. Logo, o experimento mede o comportamento do serviço para essa carga. Não avalia novas condições meteorológicas, calibração ou generalização estatística. Uma previsão por hora para um conjunto não exige, por si só, alto RPS: a decisão de ampliar infraestrutura depende da demanda real de consumidores e conjuntos.

## 3. Desenho do experimento

| Elemento | Regra desta unidade |
| --- | --- |
| Variável alterada | Clientes simultâneos: 1, 4 e 8 |
| Imagem | Exatamente o `image_id` do run aprovado; sem reconstrução ou download |
| Recursos | Limite equivalente a 2 CPUs e 1 GiB de memória; não são CPUs dedicadas |
| Servidor | Um processo Uvicorn da imagem existente; configuração científica preservada |
| Pedido | O mesmo `example_request.json`; a mesma resposta serve de referência |
| Rodadas | Três: ordens 1/4/8, 4/8/1 e 8/1/4 |
| Volume | 120 tentativas por fase; 9 fases = 1.080 tentativas medidas |
| Aquecimento | Oito chamadas anteriores, salvas separadamente e excluídas das métricas |
| Conexões | Uma conexão HTTP por cliente em cada fase, reutilizada quando possível; sem retry oculto |
| Carga | Fechada: cada cliente aguarda a resposta antes da próxima chamada |
| Duração por chamada | Tempo no cliente, do início do envio ao fim da leitura da resposta |
| Timeout | 10 segundos por operação de socket; não é um deadline global rigoroso da transação |

Alternar a ordem distribui cada nível entre as três posições da rodada. Isso reduz o confundimento simples entre nível de concorrência e posição, mas não elimina variação do notebook, do Docker Desktop, de temperatura ou de outros processos. Não há intervalo de confiança de desempenho nesta unidade.

**Carga fechada não equivale a taxa fixa de chegada.** Se as respostas demorarem, os próprios clientes diminuem a taxa de novos pedidos. Portanto, não afirme que o teste provou suporte a uma demanda externa constante de X requisições por segundo. Ao fim de cada fase pode haver menos clientes ativos, pois alguns terminam sua cota antes dos demais.

O script usa `ThreadPoolExecutor` para os clientes HTTP. Não enfileira 120 futures e chama isso de 120 requisições simultâneas: cria exatamente C trabalhadores, cada um com uma requisição em voo. Ele também registra as falhas; HTTP 200 com probabilidade, identidade ou decisão divergente é falha de contrato.

## 4. Medidas: o denominador faz parte da conclusão

Considere N tentativas, K respostas 200 corretas e T segundos da fase:

- **Vazão útil:** K/T, em respostas corretas por segundo. Uma resposta rápida e errada não aumenta a vazão útil.
- **Taxa de falhas:** (N−K)/N. Os tipos de falha continuam separados: 4xx, 5xx, transporte e resposta incorreta.
- **P50/P95:** quantis das durações das respostas 200 corretas. O código usa interpolação linear no índice `(n−1)*p`.
- **Tempo observado das tentativas:** inclui duração até falhas. Timeout não informa quando o servidor teria terminado; não trate essa duração como uma resposta concluída.
- **Concorrência média observada:** soma das durações das tentativas dividida pela duração da fase, na mesma unidade. Não é o número de processos Uvicorn nem o número de threads científicas.

**Exemplo didático:** se uma fase tem 120 respostas corretas em 6 s, sua vazão é 20/s. Se quatro clientes estiverem ocupados quase todo o tempo, uma latência média perto de 200 ms é coerente com aproximadamente `4 / 0,2 = 20/s`. Essa relação usa média e condições de regime, não o P95. O campo `mean_in_flight` fornece uma contabilidade do tempo observado; sozinho não demonstra que o sistema está estacionário.

Não faça média dos P95 e a chame de P95 agregado. Para o agregado, seria necessário juntar as durações individuais e recalcular o quantil. Nesta unidade, usamos cada rodada separadamente e o pior P95 entre as três para a decisão conservadora.

## 5. Executar no seu computador

Salve `renewcast_m06_concorrencia_20261013.zip` na raiz `C:\renewable-forecast-lab`. Mantenha Docker Desktop iniciado. O pacote acrescenta arquivos; não altera a API nem o modelo.

```powershell
Set-Location C:\renewable-forecast-lab
conda activate renewable-forecast
Expand-Archive -LiteralPath .\renewcast_m06_concorrencia_20261013.zip -DestinationPath . -Force
python scripts/medir_concorrencia.py --run-dir reports/containers/CJU_BA5EIGT/h24_event_v1/20261013T185650Z_ffc01dd8
```

O comando confere a origem, inicia a imagem já existente, mede as fases e remove somente o contêiner que criou. A imagem permanece disponível. Não é necessário abrir a API anterior em outra janela. A porta é escolhida automaticamente e publicada somente em `127.0.0.1`.

Resultados em `reports/performance/CJU_BA5EIGT/h24_event_concurrency_v1/<run_id>/`:

| Arquivo | Uso |
| --- | --- |
| `protocol.json` | Regras, recursos, ordem das fases e origem, gravados antes da carga |
| `requests.csv` | Uma linha por tentativa, inclusive falhas |
| `summary.csv` | Nove linhas, uma por rodada/concorrência |
| `verification.json` | Medição completa, identidades, hashes e correção das respostas |
| `api_source.txt` | Função `create_app` extraída da imagem realmente executada |
| `container.json` e `container_final.json` | Configuração efetiva e estado final |
| `warmup.csv`, `server.log`, `pipeline.log` | Aquecimento e diagnóstico |

Se houver falha de transporte, o script encerra depois daquela fase para não contaminar a próxima com chamadas de estado desconhecido. Preserva os CSVs já medidos e `failure.json`; não publica um novo ponteiro de execução completa. Nesse caso, envie o caminho da tentativa que falhou, não use um `latest_run` antigo como se fosse o resultado novo.

Se a imagem tiver sido apagada, a inspeção falha. Não há download ou reconstrução silenciosa. Se a medição terminar com respostas incorretas, o recibo informa isso e o comando retorna código 2. Ultrapassar o P95 didático não apaga a medição nem significa falha do código: é um resultado a interpretar.

Com medição concluída:

```powershell
python notebooks/analise_concorrencia.py
```

Esse comando confere hashes e apresenta as nove fases. Nenhuma biblioteca adicional precisa ser instalada.

## 6. Sua autoria: escolher sem premiar fila desnecessária

Arquivo: **`notebooks/analise_concorrencia.py`**. Função a implementar: **`escolher_concorrencia`**. As demais funções já fazem leitura e validação. O modo normal funciona; `--autoria` deve ser usado depois da implementação.

Regras fixadas antes do seu resultado:

1. Um nível é elegível somente se, nas três rodadas, não houver falhas e o P95 das respostas corretas for finito e no máximo 250 ms.
2. Para cada nível elegível, calcule a mediana da vazão útil das três rodadas.
3. Encontre a melhor dessas medianas. Escolha a **menor concorrência** que alcance pelo menos 95% dela.
4. Se nenhum nível for elegível, retorne `concurrency=None` com justificativa. Não substitua ausência por zero nem flexibilize o teto depois de ver os dados.

O teto 250 ms é uma regra didática desta unidade; não foi negociado com um usuário real e não constitui SLA. A escolha é uma recomendação experimental de concorrência de clientes; o script não configura um limitador de admissão na API.

Ferramentas a aplicar: agrupamento em Python, `statistics.median`, tratamento explícito de ausentes e minimização sob restrições. O contrato e o formato do retorno estão na docstring. Não há solução pronta para essa função no pacote.

Após implementar:

```powershell
python notebooks/analise_concorrencia.py --autoria
```

Ele grava `autoria/decisao.json`. A validação automática confere o formato; a revisão do professor avaliará a lógica e a interpretação. Envie o código alterado, `summary.csv`, `verification.json`, `protocol.json` e `decisao.json`.

Escreva também **`parecer_concorrencia.md`**, na pasta `autoria` do run, com até 25 linhas:

- Decida a concorrência segundo a regra e cite medianas de vazão e o pior P95 relevante.
- Descreva o que mudou de 1 para 4 e para 8. Se a vazão estabilizar e a latência crescer, formule uma hipótese de saturação/fila; não declare CPU saturada sem medição de uso de CPU.
- Abra `api_source.txt`, localize `predict_decision` e explique a diferença entre clientes concorrentes, `async def`, threads de cálculo e processos Uvicorn.
- Diga qual evidência faltaria para transformar esta medição em dimensionamento operacional. Considere diversidade dos pedidos, taxa externa de chegada, duração da carga e interferência do cliente no mesmo computador.

## 7. Aula de arquitetura: `async` não multiplica processos

Na implementação anteriormente entregue, `predict_decision` é `async def` e chama `runtime.predict(request)` diretamente. Confirme o trecho na fonte extraída da imagem. Essa chamada síncrona não entrega o controle de volta ao event loop enquanto calcula. O runtime pode usar threads de bibliotecas nativas, mas isso é outro nível de paralelismo. Ter oito clientes não significa que oito inferências estejam sendo calculadas em paralelo.

Isso é uma hipótese de mecanismo para interpretar o resultado, não um benchmark já conhecido do seu computador. O experimento preserva a implementação atual para formar uma referência. Alterar endpoint, número de processos, threads científicas e quota de CPU de uma vez impediria atribuir o efeito a uma mudança específica.

Se os números justificarem uma alteração, a próxima comparação deverá mudar um desses fatores e preservar o protocolo. Nem toda melhoria de latência exige mais recursos; nem toda arquitetura que alcança mais RPS compensa para uma previsão horária.

## 8. Fixação lexical por aplicação

| Termo | Evidência neste experimento | Explique sem consultar |
| --- | --- | --- |
| Concorrência | `concurrency` | Quantas chamadas podem estar em voo? |
| Paralelismo | Implementação, processos e recursos | Quantos cálculos realmente progridem ao mesmo tempo? |
| Vazão / throughput | `correct_per_second` | Por que usar respostas corretas no numerador? |
| Latência de cauda | `p95_correct_ms` | Por que mediana baixa pode esconder espera? |
| Carga fechada | Laço de cada worker | Como uma resposta lenta muda as próximas chegadas? |
| Restrição | P95 e falhas em três rodadas | Uma boa média pode compensar uma rodada que falhou? |
| SLI e SLO | Métrica observada e teto didático | Qual é a medida e qual é a meta? |

Depois do código, feche a aula e explique esses termos usando uma linha real do seu relatório. Reabra e corrija imprecisões. Na sessão seguinte, aplique-os a um caso de API de BI que recebe consultas concorrentes, sem reutilizar os números do Renewcast.

## 9. Critério de conclusão e continuidade

Esta unidade se encerra com medição rastreável, função autoral que obedeça às regras e interpretação que distinga observação, hipótese e limite. Um resultado desfavorável pode concluir a unidade. Contagem de testes, linhas de código ou RPS elevado não substituem esses critérios.

**Situação do roteiro:** E87 aceita a migração Docker. E88 entrega concorrência, dentro de M06.4. CI remoto continua pendente: o YAML entregue anteriormente não foi executado por um runner. A escolha de fazer a análise local agora usa os recursos disponíveis e não fecha CI, shadow ao vivo ou o utilitário Windows. M07–M14 mantêm seu estado; não há novo percentual global de formação.

## 10. Verificação do material pelo professor

O cliente foi executado em HTTP real com a réplica HGB já existente: nove fases, 216 respostas corretas, ajuste proibido. Essa réplica possui outra identidade e probabilidade, explicitadas em `Verificacao_E88_Professor.json`; não são novos números do seu modelo. Um servidor de teste, explicitamente sintético, conferiu sobreposição das chamadas e separação de 200 incorreto, 422 e 500. O quantil e o tratamento de resposta não finita foram verificados.

Docker e PowerShell não estão disponíveis no ambiente do professor. O ciclo Docker desta unidade reutiliza o mecanismo já executado por você e acrescenta limites de recursos; sua execução no Windows ainda precisa ser observada. Não se atribui latência ou capacidade ao seu computador a partir da réplica.

## Referências primárias

- [scikit-learn — persistência e ambiente](https://scikit-learn.org/stable/model_persistence.html)
- [PyPA — compatibilidade dos wheels](https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/)
- [Docker — limites de recursos](https://docs.docker.com/engine/containers/resource_constraints/)
- [FastAPI — concorrência, async e funções síncronas](https://fastapi.tiangolo.com/async/)
- [Grafana k6 — modelos de carga abertos e fechados](https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/open-vs-closed/)
- [Python — concurrent.futures](https://docs.python.org/3.12/library/concurrent.futures.html)
- [Python — http.client](https://docs.python.org/3.12/library/http.client.html)
