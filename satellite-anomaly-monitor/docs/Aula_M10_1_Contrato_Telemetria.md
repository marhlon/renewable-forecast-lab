# M10.1 — quando três sensores não formam automaticamente uma linha de dados

Do ferro ao pró — Data Science · produto P2: satellite-anomaly-monitor · 17/11/2026

**Problema:** um detector multivariado precisa comparar valores de vários canais no mesmo instante de decisão. Os sensores chegam em horários próprios. Juntar pela observação mais próxima pode usar o futuro; carregar a última medição sem limite pode esconder uma interrupção. Antes de treinar PCA ou Isolation Forest, precisamos produzir uma tabela cujo conteúdo e rótulos tenham significado verificável.

**Entrega desta unidade:** uma grade causal com timestamp e idade da amostra de cada canal, um perfil de qualidade e uma tabela separada de anotações. O laboratório completo funciona; sua atividade é implementar e explicar o sincronizador, não completar infraestrutura.

## 1. Onde salvar e como executar

Baixe `renewcast_m10_1_telemetria.zip` para `C:\renewable-forecast-lab`. O pacote cria uma pasta própria para o P2, preservando os caminhos do Renewcast:

```powershell
Set-Location C:\renewable-forecast-lab
conda activate renewable-forecast
Expand-Archive -LiteralPath .\renewcast_m10_1_telemetria.zip -DestinationPath . -Force -ErrorAction Stop
python satellite-anomaly-monitor/scripts/executar_m10_1.py
```

Usa NumPy, pandas e biblioteca padrão já disponíveis no ambiente. Não instala pacotes, não abre Docker, não carrega Chronos e não treina modelos. Os três CSVs comprimidos e os metadados reais já acompanham a entrega. A execução é offline e funciona a partir de qualquer diretório se o caminho do script for absoluto.

Cada execução cria `satellite-anomaly-monitor/reports/m10_1/<run_id>`. Abra seu relatório:

```powershell
$p = Get-Content -Raw .\satellite-anomaly-monitor\reports\m10_1\latest_run.json | ConvertFrom-Json
Invoke-Item (Join-Path $p.directory 'relatorio.html')
```

Não procure arquivos em `notebooks/` do Renewcast: a implementação desta unidade está em `satellite-anomaly-monitor/src/satmon/temporal.py`; a condução está em `satellite-anomaly-monitor/scripts/executar_m10_1.py`.

## 2. Os dados são reais; seu significado tem limites

Usamos ESA Anomaly Dataset, **Mission1, versão v2 do registro Zenodo 15237121**, DOI `10.5281/zenodo.15237121`. O benchmark reúne telemetria e anotações curadas de missões da ESA. O recorte didático conserva **2007 inteiro, canais 50, 51 e 52**, do grupo 10, marcados como alvos não categóricos nos metadados.

Os canais foram escolhidos por grupo e orçamento de dados, considerando também a existência de anotações no histórico completo, antes de treinar qualquer detector. Portanto este é um recorte de exploração de contratos, não uma seleção cega de dados ou um teste final reservado. Não reproduz o protocolo completo ESA-ADB.

São **348.901 medições por canal**, 1.046.703 no total. Os valores foram preservados. Os identificadores `subsystem_6` e `physical_unit_3` são anonimizados: não podemos convertê-los em temperatura, tensão ou severidade física. Um valor extremo pode ter interesse estatístico sem identificar uma falha do satélite.

O índice original da medição não informa fuso; os intervalos de anotação terminam em `Z`. Nesta transformação, interpretamos ambos no mesmo eixo UTC, explicitamente como hipótese de trabalho. O instante da medição também é a disponibilidade assumida. Não temos um registro de chegada ao solo que comprove essa latência.

O fornecimento inclui `source.json`, com hashes, corte, membros ZIP de origem e a transformação declarada. O preparo obteve apenas membros selecionados do arquivo público e conferiu seus CRCs. Não foi baixado nem validado o MD5 do ZIP completo de 3,8 GB; o campo correspondente registra esse limite. Os CSVs derivados possuem seus próprios SHA-256.

## 3. Cadência, grade e frescor são grandezas diferentes

A mediana do intervalo entre medições é **90 s**, e o percentil 99 é **90,003 s**. O milissegundo adicional já basta para impedir que um `JOIN` por igualdade funcione como sincronização geral. Há 41 intervalos maiores que 180 s por canal; o maior tem **1.170 s**, ou 19,5 minutos.

O protocolo prescreve uma grade de 90 s, de 01/01/2007 00h até 01/01/2008 00h, com fim exclusivo: **350.400 instantes**. A tolerância de idade é **180 s**, exploratória, igual para os três canais. Ela não foi otimizada contra os rótulos e não representa um SLA de operação.

Em um instante de grade `g`, procuramos a última amostra `t` que satisfaça:

\[
t\le g,\qquad 0\le g-t\le180\text{ s}.
\]

Se não houver amostra anterior ou ela estiver velha demais, o valor utilizável fica desconhecido. Preservamos `sample_time` e `age_seconds` para revelar a causa. Um valor `NaN` presente na última medição também não autoriza buscar um valor antigo conveniente.

Isso é retenção limitada da última amostra, não geração de novas medições. A quantidade de linhas utilizáveis na grade pode superar a quantidade de medições brutas: uma amostra pode atender dois instantes. Nunca interprete esse percentual como taxa de chegada original ou prova de funcionamento normal.

Os relógios desses três canais coincidem no recorte recebido. A função ainda precisa funcionar com relógios diferentes; as contraprovas fazem essa alteração de propósito. Não apresentamos essa contraprova como dado real do satélite.

## 4. A operação central, explicada

O núcleo faz uma busca temporal com as tabelas ordenadas:

```python
pd.merge_asof(
    grade, canal,
    left_on="timestamp", right_on="sample_time",
    direction="backward", allow_exact_matches=True,
)
```

`backward` seleciona uma amostra anterior ou simultânea. `nearest` escolhe a menor distância absoluta e pode atravessar a fronteira do presente. Não usar `tolerance` na busca é deliberado nesta implementação: primeiro guardamos qual era a última amostra; depois calculamos sua idade e invalidamos o valor quando passa de 180 s. Assim a evidência de expiração continua na saída.

`usable` exige timestamp conhecido, idade dentro do limite e valor preenchido. Só depois dessa condição substituímos `value` por `NaN` nas linhas inválidas. Não zeramos medições desconhecidas. As colunas finais são `timestamp` e, para cada canal, `value`, `sample_time`, `age_seconds` e `usable`. `all_channels_usable` é calculada pelo laboratório após a sincronização.

Exemplo com tolerância de 5 s, fonte `(00s, 0)` e `(10s, 10)`:

| Decisão | Amostra anterior | Idade | Valor utilizável |
| --- | --- | ---: | ---: |
| 02s | 00s | 2s | 0 |
| 07s | 00s | 7s | desconhecido |
| 12s | 10s | 2s | 10 |

Em 07s, `nearest` escolheria 10s: o valor ainda não existe no instante da decisão. Já a retenção sem limite devolveria 0, escondendo a expiração. Alterar a medição dos 10s deve mudar a linha dos 12s, mas não as linhas dos 02s e 07s. Essa invariância é uma prova mais forte que apenas conferir se o programa terminou.

## 5. Eventos não são pontos independentes

`labels.csv` contém **ID, canal, início e fim**. `anomaly_types.csv` acrescenta a categoria e outras propriedades. O mesmo ID pode afetar vários canais e aparecer em mais de um intervalo. Contar linhas desse CSV como eventos independentes inflaria o número de exemplos.

O recorte contém **33 linhas de anotação**, com dez IDs distintos: três da categoria `Anomaly` e sete `Rare Event`. Há sete linhas canal/intervalo de anomalia e 26 de evento raro. Não há anotação `Communication Gap` nesse recorte, embora existam lacunas de amostragem medidas nos próprios canais. São informações de naturezas diferentes.

O laboratório conserva as três categorias. Não transforma automaticamente evento raro em anomalia. Um instante sem anotação recebe `unannotated`, e não a declaração de que está fisicamente normal. A ausência de rótulo não resolve a cobertura ou a exaustividade da anotação.

Para a grade, adotamos intervalo fechado `[StartTime, EndTime]`, regra explícita desta unidade. Um intervalo pontual pode não coincidir com a grade; ele continua na tabela de eventos. `cobertura_eventos.csv` informa quantos instantes da grade e quantas amostras utilizáveis caíram em cada anotação. Não prolongamos um rótulo para forçar acerto.

As anotações ficam em `rotulos_grade.csv.gz`, separadas de `grade_features.csv.gz`. São retrospectivas e destinam-se à avaliação posterior. Nunca fornecer ID, categoria ou marcador de anomalia como entrada de um detector que deveria descobrir essas condições.

Três IDs de anomalia são suficientes para estudar esse contrato, mas são evidência pequena para estimar generalização, escolher dezenas de limiares ou medir atraso com estabilidade. M10.2 deverá ampliar e fixar o recorte temporal antes da comparação de detectores; M10.3 fará a avaliação por evento. Não existe promessa de desempenho baseada nesta unidade de preparação.

## 6. Resultado de referência já executado

| Medida | Resultado Linux desta entrega |
| --- | ---: |
| Medições brutas | 1.046.703 |
| Instantes na grade | 350.400 |
| Linhas utilizáveis por canal | 350.346 |
| Linhas não utilizáveis por canal | 54 |
| Cobertura de frescor por canal | 99,9846% |
| Linhas de grade anotadas como anomalia, união dos canais | 5.732 |
| Linhas anotadas como evento raro, união dos canais | 3.303 |
| Treinos executados | 0 |

A frequência de linhas anômalas não é a frequência de eventos, e a grade não cria 350 mil casos independentes. Persistência temporal, sobreposição e identidade dos IDs precisarão ser respeitadas na divisão posterior.

As cinco conferências cobrem cálculo manual, expiração, igualdade na fronteira, canais com relógios diferentes, preservação das entradas, perturbação do futuro e rejeição de entradas inválidas. Uma auditoria adicional por `searchsorted`, independente do `merge_asof`, confronta a grade real inteira na preparação da entrega. A execução Windows do aluno ainda será registrada; os números acima são da referência Linux.

## 7. Sua demanda de programação

Crie **`satellite-anomaly-monitor/notebooks/m10_sincronizacao_autoral.py`**, com a função:

```python
def sincronizar_causal(tabelas, grade, tolerancia):
    # tabelas: {nome: DataFrame com timestamp e value}
    # grade: DatetimeIndex crescente, com fuso
    # tolerancia: pandas.Timedelta não negativo
    ...
```

Implemente a busca anterior, a idade e a invalidação seletiva, preservando o timestamp da amostra expirada e as entradas. Rejeite instantes duplicados por canal e uma grade fora de ordem. O resultado tem as mesmas colunas e ordem descritas na seção 4. Não consulte os rótulos, não use `nearest`, interpolação entre passado e futuro ou preenchimento sem limite.

Leia primeiro a conta da seção 4; depois escreva a implementação. A referência completa está em `src/satmon/temporal.py` para consulta e revisão. Não há necessidade de criar novos ambientes ou refazer a aquisição de dados.

Confira as contraprovas, sem ler o ano de dados:

```powershell
python satellite-anomaly-monitor/scripts/executar_m10_1.py --autoria satellite-anomaly-monitor/notebooks/m10_sincronizacao_autoral.py --verificar
```

Depois use a mesma função no recorte real:

```powershell
python satellite-anomaly-monitor/scripts/executar_m10_1.py --autoria satellite-anomaly-monitor/notebooks/m10_sincronizacao_autoral.py
```

O modo autoral confronta a tabela real inteira com a referência, não apenas o formato. Entregue a função, `resultado.json`, `perfil_canais.csv` e uma nota em `satellite-anomaly-monitor/reports/parecer_m10_1.md` respondendo:

1. Por que há mais instantes utilizáveis que medições brutas por canal? Use `sample_time` para sustentar sua resposta.
2. O que aconteceria com a detecção de uma mudança se `nearest` consultasse uma amostra posterior? Mostre o caso de 07s.
3. Por que zero rótulos de `Communication Gap` não elimina as 41 lacunas medidas? Por que dez IDs não equivalem a 33 falhas independentes?
4. Quais hipóteses de disponibilidade, unidade e fuso ainda impedem uma afirmação operacional?

**Aceite:** função passa nas cinco conferências e na comparação real; explicação distingue medições, grade, anotações e eventos. Depois seguem escore robusto, PCA e Isolation Forest em M10.2, com protocolo temporal ampliado e declarado antes de medir desempenho.

## Fontes e atribuição

- [ESA Anomaly Dataset v2](https://zenodo.org/records/15237121), European Space Agency, De Canio, Kotowski, Haskamp e colaboradores: origem da telemetria e anotações.
- [Repositório do benchmark ESA-ADB](https://github.com/kplabs-pl/ESA-ADB) e [metadados Croissant](https://github.com/kplabs-pl/ESA-ADB/blob/main/data/preprocessed/esa-anomaly-dataset-metadata.json). A declaração de licença preservada nesses metadados é CC BY 3.0 IGO; este recorte e sua sincronização são adaptações didáticas, sem endosso da ESA.
- [Documentação pandas.merge_asof](https://pandas.pydata.org/docs/reference/api/pandas.merge_asof.html): semântica de backward, forward, nearest e ordenação. Os limites de frescor e os resultados desta aula são decisões e medições locais, não resultados do benchmark oficial.
