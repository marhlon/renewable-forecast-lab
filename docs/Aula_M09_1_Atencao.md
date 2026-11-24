# M09.1 — atenção: quais horas uma representação pode consultar?

Do ferro ao pró — Data Science · Renewcast · 15/11/2026

Você já implementou a atualização de estado de uma GRU. Agora vai implementar outra operação central: **construir uma representação consultando posições de uma sequência por pesos calculados a partir do conteúdo**. A unidade usa uma janela real do projeto e contraprovas pequenas com resultado conhecido. O propósito é entender e programar atenção, condição para avaliar um Transformer depois. Não treinaremos um modelo de previsão nesta unidade.

## 1. Execução, arquivos e entrega

Salve `renewcast_m09_1_atencao.zip` na raiz `C:\renewable-forecast-lab`. Execute no ambiente que acabou de rodar a GRU:

```powershell
Set-Location C:\renewable-forecast-lab
conda activate renewable-forecast
Expand-Archive -LiteralPath .\renewcast_m09_1_atencao.zip -DestinationPath . -Force -ErrorAction Stop
python notebooks/laboratorio_atencao.py
```

Não é necessário repetir M08, instalar bibliotecas, reconstruir Docker ou baixar pesos. A entrada é o pacote M07.3 já usado em M08: `dist/databricks/CJU_BA5EIGT/m07_3`. O contrato de entrada é reutilizado de `notebooks/m08_3_base.py`, que já está no seu projeto; este pacote não o modifica.

| Arquivo | Papel |
| --- | --- |
| `src/renewable_forecast/attention_math.py` | Implementação de referência completa, com validação, máscara e softmax. Leia depois da sua primeira tentativa se quiser testar transferência independente. |
| `notebooks/laboratorio_atencao.py` | Executa contraprovas, extrai a janela real, exporta pesos/representações e relatório. Não contém loop de treinamento. |
| `docs/Aula_M09_1_Atencao.md` | Este guia, incluindo explicação matemática, exemplos e atividade. |

Cada execução cria `reports/transformer/CJU_BA5EIGT/m09_1_atencao/<run_id>`. O caminho aparece no terminal. Para abrir o relatório:

```powershell
$p = Get-Content -Raw .\reports\transformer\CJU_BA5EIGT\m09_1_atencao\latest_run.json | ConvertFrom-Json
Invoke-Item (Join-Path $p.directory 'relatorio.html')
```

A execução normal está completa. Nenhuma função reservada ao aluno bloqueia a exploração. Sua entrega será `notebooks/m09_atencao_autoral.py`, a conferência e uma explicação breve aplicada às máscaras; o contrato está na seção 9.

## 2. Da memória da GRU a uma consulta ponderada

Na GRU, cada passo atualiza um estado que carrega o resultado do processamento anterior. A previsão final usa o último estado. Na atenção, uma posição calcula compatibilidades com várias posições, transforma essas compatibilidades em pesos e combina os valores correspondentes.

Isso permite consultar diretamente outras posições do contexto. Não significa memória infinita nem elimina restrições de disponibilidade. Se uma hora indisponível entra no conjunto de chaves/valores, a arquitetura pode usá-la; o nome Transformer não protege contra vazamento.

Também não significa que a atenção recuperou uma relação causal física. Os pesos resultam de produtos de vetores e normalização. Um peso alto não prova que aquela hora causou a geração futura.

## 3. Q, K e V, sem analogias que escondem a conta

Considere uma sequência de representações `E` e três transformações:

\[
Q=EW_Q,\qquad K=EW_K,\qquad V=EW_V.
\]

Em um modelo treinado, as matrizes são parâmetros aprendidos pela perda. Q descreve as consultas; K fornece vetores contra os quais elas são comparadas; V fornece o conteúdo que será combinado. Q e K precisam ter a mesma dimensão final para o produto interno; V pode ter outra dimensão.

Nesta unidade, para tornar a representação interpretável, Q e K usam projeções fixas e V contém a própria geração histórica. As projeções são **não treinadas**. Assim, a saída será uma média ponderada do histórico, sem reivindicação de qualidade preditiva. O laboratório não a chama de previsão h24.

| Objeto | Shape geral | Significado |
| --- | --- | --- |
| Q | `[B,L,D]` | B exemplos, L consultas, D coordenadas por consulta |
| K | `[B,S,D]` | S chaves por exemplo |
| V | `[B,S,Dv]` | Um vetor de conteúdo por chave |
| `Q @ Kᵀ` | `[B,L,S]` | Compatibilidades consulta–chave |
| A | `[B,L,S]` | Pesos normalizados por consulta |
| `A @ V` | `[B,L,Dv]` | Representações resultantes |

**B não é tempo.** O produto deve acontecer separadamente dentro de cada exemplo. **L e S não precisam ser iguais**: o verificador inclui consultas e chaves de comprimentos diferentes. Na janela histórica desta execução, B=1, L=S=24, D=4 e Dv=1.

## 4. Produto, escala, máscara e softmax

A atenção escalada de uma cabeça é:

\[
Z=\frac{QK^\top}{\sqrt D},\qquad
A_{ij}=\frac{\exp(Z_{ij})}{\sum_j\exp(Z_{ij})},\qquad O=AV.
\]

Cada **linha** de A corresponde a uma consulta; suas colunas são as chaves. A soma sobre as chaves deve ser um. Aplicar softmax sobre a dimensão de consultas responderia a outro problema.

A divisão por `sqrt(D)` controla a escala dos produtos quando a dimensão cresce. Sob coordenadas aproximadamente independentes, centradas e de variância unitária, a variância da soma de D produtos cresce com D. A raiz reduz esse crescimento. Isso é motivação da escala, não garantia de que toda distribuição real siga essas hipóteses.

Para calcular softmax com estabilidade, subtraia de cada linha seu maior valor antes da exponencial. Isso não muda a razão final, pois o mesmo fator cancela no numerador e denominador. Evita tentar calcular, por exemplo, `exp(1.000.000)`. O teste usa esse tipo de score grande.

A máscara booleana do contrato desta aula usa **True = permitido**. Transforme scores proibidos em `−inf` **antes** da normalização. Assim, a exponencial correspondente é zero e a chave não participa do denominador. Zerar pesos depois do softmax, sem renormalizar, geralmente deixa a soma menor que um.

Uma linha com todas as chaves bloqueadas não define uma distribuição neste contrato. Sua função deve rejeitá-la com `ValueError`; não criar silenciosamente uma média com zeros. A convenção de máscara é específica da função/API: leia a documentação ao migrar para outro módulo.

## 5. Uma conta que você consegue verificar sem framework

Uma consulta tem scores já escalados `[ln(3),0]`; os valores são `[10,30]`:

\[
A=[3/(3+1),1/(3+1)]=[0{,}75,0{,}25],\qquad
O=0{,}75\times10+0{,}25\times30=15.
\]

Se apenas a segunda chave for permitida, os pesos tornam-se `[0,1]` e a saída é 30. Os conteúdos V não foram mudados; mudou quais deles a consulta pode usar.

Outro caso do verificador usa três valores `[0,6,12]`, Q/K nulos e portanto compatibilidades iguais:

| Consulta | Atenção livre | Atenção causal incluindo a diagonal |
| --- | ---: | ---: |
| Posição 0 | média de 0,6,12 = 6 | apenas 0 = 0 |
| Posição 1 | média de 0,6,12 = 6 | média de 0,6 = 3 |
| Posição 2 | média de 0,6,12 = 6 | média de 0,6,12 = 6 |

O caso mostra o efeito da máscara na conta inteira. Não é um experimento de previsão de geração.

## 6. Há dois sentidos de “futuro” nesta janela

Na origem `03/07/2026 04h`, a janela conhecida vai de `02/07 03h` a `03/07 02h`, sob atraso assumido de duas horas. **Todas as 24 posições estão no passado da origem de previsão.**

Uma atenção livre entre essas 24 medições não usa, por si só, futuro indisponível na origem. Um encoder pode combinar livremente esse contexto se a coleta e o corte forem corretos.

Já uma representação da posição interna 5, quando interpretada como processamento de um prefixo até essa posição, não deveria consultar as posições 6–23. Para esse objetivo, a máscara triangular inferior impede consultas posteriores dentro da sequência. Esse é o sentido de causalidade autorregressiva da máscara; não prova causalidade meteorológica.

O laboratório altera o último V do caso de três posições. Com máscara causal, as duas primeiras saídas permanecem iguais; a última pode mudar. Sem máscara, as anteriores podem mudar. É uma contraprova de acesso à informação, sem treinar nada.

**Sutileza que você deve explicar:** na atenção de uma única camada, sem dropout e sobre os mesmos Q/K/V, a última consulta permite todas as chaves tanto na máscara causal quanto na livre. Por isso suas saídas são iguais. Isso não garante igualdade em uma pilha de camadas: as representações anteriores podem ter sido produzidas com conjuntos de acesso diferentes e alimentar as próximas camadas.

Não atribua qualquer diferença observada a “vazamento” sem antes dizer qual posição está sendo prevista, qual relógio define disponibilidade e quais entradas estavam permitidas nesse instante.

## 7. Por que precisamos representar posição?

Sem informação posicional, a atenção livre sobre conteúdo tem uma propriedade de permutação. Se você reordenar Q/K/V da mesma sequência, as saídas se reordenam da mesma forma. Se depois fizer uma média das saídas, essa média será invariante à permutação.

Isso é adequado para um conjunto sem ordem, mas pode ser insuficiente para distinguir “vento subiu” de “vento caiu” em uma série. O problema não é que o produto matricial deixe de funcionar: falta representar o significado da posição.

O laboratório acrescenta quatro coordenadas senoidais/cossenoidais dos índices 0–23 às representações antes de calcular Q/K. Então reordena o conteúdo mantendo os índices de posição fixos. A equivalência anterior deixa de valer. Isso demonstra a função de posição nesse cálculo; não demonstra qual codificação seria melhor em previsão.

Reordenar **conteúdo e posição juntos** é diferente de mudar qual conteúdo ocupa cada posição. Na contraprova, mantemos o calendário de posições fixo e trocamos o conteúdo; o objetivo é testar a segunda operação.

## 8. Ler sua saída

`relatorio.html` mostra dois mapas de pesos 24×24. Passe o mouse sobre uma célula para ler consulta, chave e peso. A cor é relativa ao máximo de cada painel; use os CSVs para comparar valores exatos. O eixo 0 corresponde à hora mais antiga e o 23 à mais recente.

| Saída | Leitura |
| --- | --- |
| `pesos_livres.csv` | Distribuição sobre as 24 chaves em cada consulta |
| `pesos_causais.csv` | Zeros nas posições proibidas e soma um nas permitidas |
| `janela_e_representacoes.csv` | As 24 medições reais e suas representações ponderadas |
| `projecoes.json` | Matrizes fixas e codificação posicional, explicitamente não treinadas |
| `conferencia.json` | Casos manuais, máscaras, estabilidade, permutação e comparação PyTorch |
| `resultado.json` | Origem, shapes, versões, hashes de entrada e saídas, limites do ensaio |

Como V contém geração e os pesos são não negativos com soma um, cada saída escalar fica entre o mínimo e o máximo de V permitido para aquela consulta. Isso é propriedade dessa combinação convexa. A cabeça de um Transformer completo pode produzir valores fora desse intervalo após projeções e outras operações.

M09.1 calcula uma atenção de uma cabeça. Um bloco Transformer completo acrescenta, entre outros componentes, projeções aprendidas, atenção de múltiplas cabeças, conexões residuais, normalização e rede feed-forward. Pesos pré-treinados, contextos/horizontes maiores, custo e comparação preditiva pertencem às próximas unidades; o programa não os declara executados.

## 9. Sua implementação e explicação

Crie **`notebooks/m09_atencao_autoral.py`**:

```python
def atencao_escalada(q, k, v, mascara=None):
    # Calcular e devolver:
    # {"pesos": pesos, "saida": saida}
    ...
```

Contrato: arrays float64 finitos, Q `[B,L,D]`, K `[B,S,D]`, V `[B,S,Dv]`; máscara opcional booleana `[L,S]`, True permite. Preserve entradas, inclusive somente para leitura. Não importe a referência do professor nem chame PyTorch dentro da sua implementação. B/L/S/D/Dv são variáveis; não fixe 24 ou 4. Rejeite uma consulta sem nenhuma chave permitida e dimensões incompatíveis.

Trabalhe em cinco operações, justificando cada eixo: produto Q/K; divisão por raiz de D; bloqueio; softmax estável sobre S; produto A/V. A implementação não precisa treinar ou carregar um modelo.

Depois confira:

```powershell
python notebooks/laboratorio_atencao.py --autoria notebooks/m09_atencao_autoral.py --verificar
```

Esse comando não lê os Parquets nem treina. Para aplicar sua função também à janela real, execute o mesmo comando **sem** `--verificar`.

Em **`reports/parecer_m09_atencao.md`**, faça uma defesa curta de três decisões: por que atenção livre é permitida no contexto histórico disponível, por que a última consulta coincide no ensaio de uma camada e por que um mapa de atenção de projeções não treinadas não aprova uma previsão. Inclua a conta de `[ln(3),0]` e os shapes da sua execução.

Você pode acrescentar no mesmo parecer um parágrafo de fechamento do M08: escolha provisória HGB/MLP/GRU diante de MAE, RMSE, viés e custo, com os números Windows auditados. Isso consolida a interpretação que faltava, sem novo experimento nem repetição dos testes aceitos.

**Critério de conclusão da unidade:** função correta, contraprovas aprovadas, janela real identificada e defesa dos acessos permitidos. Envie código, `conferencia.json`, `resultado.json` e parecer. O próximo conteúdo é a composição de um Transformer e depois o modelo temporal pré-treinado, com protocolo próprio; não serão contados como feitos por executar esta atenção.

## Referência primária

[PyTorch 2.7 — scaled_dot_product_attention](https://docs.pytorch.org/docs/2.7/generated/torch.nn.functional.scaled_dot_product_attention.html): produto escalado, shapes, máscara booleana e dropout. No comparador usamos CPU/float64 e `dropout_p=0.0`. A execução deste pacote registra as versões efetivamente usadas. A função do aluno é comparada numericamente com essa operação, não avaliada pela semelhança textual do código.
