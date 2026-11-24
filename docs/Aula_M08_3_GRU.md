# M08.3 — uma rede com memória precisa vencer uma referência simples?

Renewcast · Do ferro ao pró — Data Science · 15/11/2026

**Problema desta unidade:** prever a geração em `origem + 24h`, usando as 24 medições que já poderiam estar disponíveis na origem, sob atraso assumido de duas horas. A MLP tratou essas medições como 24 posições de um vetor. Agora uma GRU percorrerá a sequência, atualizando um estado. A pergunta experimental é se essa representação melhora o resultado diante de persistência, regressão linear, MLP e HGB, mantendo as mesmas origens e a mesma informação disponível.

O laboratório está completo. Nenhuma função vazia impede a execução normal. Sua programação autoral vem depois de um experimento que funciona e tem saída identificável. M08.2 está aceito no escopo assistido; sua avaliação em lotes foi incorporada ao módulo desta unidade.

## 1. Onde salvar, como executar e o que abrir

Baixe `renewcast_m08_3_gru.zip` para `C:\renewable-forecast-lab`. No PowerShell:

```powershell
Set-Location C:\renewable-forecast-lab
conda activate renewable-forecast
Expand-Archive -LiteralPath .\renewcast_m08_3_gru.zip -DestinationPath . -Force
python notebooks/laboratorio_gru.py
```

O comando usa o ambiente existente, CPU e dois threads. Não baixa dados, não usa Docker ou Databricks e não reinstala dependências. O projeto já deve estar importável nesse ambiente, como nas unidades anteriores. A entrada continua exatamente:

```text
dist/databricks/CJU_BA5EIGT/m07_3/
    manifesto_entrada.json
    geracao.parquet
    treino_referencia.parquet
```

O manifesto, os tamanhos e os hashes são conferidos antes do ajuste. Uma entrada ausente ou divergente interrompe a execução com mensagem, sem procurar outro experimento e sem gerar dados de substituição.

Cada execução cria uma pasta própria em `reports/neural/CJU_BA5EIGT/m08_3_gru/<run_id>`. A saída informa esse caminho. Para abrir o relatório da última execução completa:

```powershell
$p = Get-Content -Raw .\reports\neural\CJU_BA5EIGT\m08_3_gru\latest_run.json | ConvertFrom-Json
Invoke-Item (Join-Path $p.directory 'relatorio.html')
```

Durante o treinamento aparecem arquitetura, semente, época, perdas e melhor época. Há seis ajustes neurais; pode levar vários minutos no seu computador. O tempo desta máquina de referência não estima o tempo do seu Windows. Se houver erro, `failure.json` identifica a interrupção; o ponteiro da última execução completa não é atualizado.

| Arquivo do código | Para que serve; o que ler |
| --- | --- |
| `src/renewable_forecast/neural_gru.py` | Modelo reutilizável e avaliador. Comece por `GRU24h.forward`: são as linhas que dão significado à recorrência. |
| `notebooks/laboratorio_gru.py` | Orquestra dados, treino, checkpoints e comparação. Leia `treinar`, depois `executar`. |
| `notebooks/m08_3_base.py` | Contratos de entrada, divisão e MLP preservados do M08.2. Não precisa reimplementar. |
| `notebooks/m08_3_verificacao.py` | Contraprovas de portas, estado, lotes e recarregamento sem treinar. Contém referência NumPy para consulta posterior à sua tentativa. |
| `scripts/executar_m08_3.ps1` | Alternativa ao comando direto, com conferência do ambiente e interrupção no primeiro erro. |

Os arquivos anteriores do M08.2 não são substituídos. Este pacote acrescenta a unidade M08.3; não cria cópias de segurança dentro de `notebooks`.

## 2. O contrato temporal vem antes da arquitetura

Para uma origem `o`, horizonte `h=24`, atraso `d=2` e contexto `L=24`:

\[
X_o=[g_{o-25},g_{o-24},\ldots,g_{o-2}],\qquad y_o=g_{o+24}.
\]

O contexto tem **24 valores**, não 24 horas de distância entre suas pontas: as pontas estão separadas por 23 horas. O último valor conhecido e o alvo estão separados por 26 horas. Portanto, `h24` não significa que o modelo vê a geração na origem.

No primeiro exemplo de avaliação, origem `03/07/2026 04h`, a janela começa em `02/07 03h` e termina em `03/07 02h`. O alvo é `04/07 04h`, disponível às `06h` sob a hipótese de atraso. O eixo permanece sem fuso físico validado: estes horários não foram convertidos silenciosamente em UTC.

| Papel | Linhas | Uso permitido |
| --- | ---: | --- |
| Ajuste | 7.079 | Estimar normalização e parâmetros dos modelos |
| Seleção | 168 | Escolher a época de cada rede |
| Avaliação | 168 | Descrever os checkpoints já fixados |
| Exclusão por disponibilidade | 52 | Impedir que um alvo ainda indisponível atravesse a fronteira |
| Exclusão por contexto incompleto | 18 | Não inventar as primeiras 24 medições |

As 52 exclusões correspondem a duas fronteiras de 26 origens. O critério exige que o alvo do conjunto anterior esteja disponível **estritamente antes** da primeira origem do conjunto seguinte. `particoes.csv` torna essa regra inspecionável. O treinamento não recebe a semana de avaliação como argumento.

A divisão evita esse vazamento específico; ela não elimina sobreposição de janelas, dependência temporal, alterações históricas da fonte ou o fato de a semana final já ter sido examinada no desenvolvimento.

## 3. O que muda de MLP para GRU

A regressão linear aprende um coeficiente por posição. A MLP mistura as 24 posições em uma camada de 32 unidades. Na GRU, cada medição entra sucessivamente, junto de um vetor de estado que resume o processamento anterior. Os mesmos pesos da célula são reutilizados nos 24 passos.

Esse compartilhamento é uma hipótese de modelagem: uma transformação recorrente pode representar padrões úteis em posições distintas. Não é prova de que ela aproveita melhor a informação. A regressão e o HGB também recebem a ordem temporal por meio das posições dos lags.

| Etapa | Shape | Interpretação |
| --- | --- | --- |
| Lote de entrada | `[B,24,1]` | B origens, 24 horas por origem, uma variável |
| Entrada de um passo | `[B,1]` | A mesma posição temporal de todas as origens do lote |
| Estado de um passo | `[B,16]` | Dezesseis coordenadas aprendidas por origem |
| Todos os estados da GRU | `[B,24,16]` | Um estado após cada medição |
| `hidden` final | `[1,B,16]` | Uma camada e uma direção; `batch_first` não muda este shape |
| `hidden[-1]` | `[B,16]` | Estado final da única camada |
| Saída da cabeça linear | `[B,1]` | Geração prevista, na escala padronizada |

O código central é:

```python
_, hidden = self.gru(x)
return self.head(self.dropout(hidden[-1]))
```

`self.gru(x)` processa os 24 passos; o `_` dispensa a sequência completa de estados para a previsão. `hidden[-1]` seleciona a camada final, não o último exemplo do lote. A cabeça linear transforma suas 16 coordenadas em um número. `Dropout(0.1)` está explicitamente nessa cabeça. Em uma GRU de apenas uma camada, o parâmetro de dropout **entre camadas recorrentes** não produz o mesmo efeito.

O estado final não tem unidade MWmed e não é uma média física. Sua interpretação depende dos pesos aprendidos. É a cabeça, seguida da transformação inversa do alvo, que produz a previsão em MWmed.

## 4. Portas: como a memória é atualizada

Chamemos `x_t` a entrada de um passo e `h_{t-1}` o estado anterior. A implementação do PyTorch usa:

\[
\begin{aligned}
r_t&=\sigma(W_{ir}x_t+b_{ir}+W_{hr}h_{t-1}+b_{hr}),\\
z_t&=\sigma(W_{iz}x_t+b_{iz}+W_{hz}h_{t-1}+b_{hz}),\\
n_t&=\tanh(W_{in}x_t+b_{in}+r_t\odot(W_{hn}h_{t-1}+b_{hn})),\\
h_t&=(1-z_t)\odot n_t+z_t\odot h_{t-1}.
\end{aligned}
\]

`σ` transforma cada coordenada em um valor entre zero e um. `⊙` multiplica coordenadas correspondentes; não é multiplicação de matrizes. Os vetores `r` e `z` têm 16 coordenadas por exemplo. Seus valores são calculados pelo modelo, não definidos como regras manuais de vento.

- **`z` controla a combinação:** próximo de um, preserva mais do estado anterior; próximo de zero, incorpora mais do candidato `n`. Com `h_anterior=0,8`, `n=−0,2` e `z=0,75`, o novo estado é `0,25×(−0,2)+0,75×0,8=0,55`.
- **`r` controla a contribuição recorrente para o candidato:** atenua ou preserva coordenadas do termo afim calculado a partir do estado anterior. Não zera diretamente todo o estado final.
- **`n` é uma proposta de estado:** combina a entrada atual com a contribuição do passado e aplica `tanh`.

Uma sutileza importante de implementação: no PyTorch, a porta `r` multiplica o termo `W_hn h + b_hn` **depois** dessa transformação. Em geral, `r ⊙ (W h + b)` não é igual a `W(r ⊙ h)+b`. A matriz mistura coordenadas; mover a porta altera a função. É por isso que a conferência autoral usa estado inicial não nulo e matrizes com várias coordenadas.

As matrizes são armazenadas empilhando três blocos, na ordem **r, z, n**:

| Parâmetro | Shape na nossa GRU | Elementos |
| --- | --- | ---: |
| `weight_ih_l0` | `[48,1]` | 48 |
| `weight_hh_l0` | `[48,16]` | 768 |
| `bias_ih_l0` e `bias_hh_l0` | `[48]` cada | 96 |
| Cabeça: peso e intercepto | `[1,16]` e `[1]` | 17 |
| Total | | **929** |

A MLP tem 833 parâmetros; o linear, 25. Contar parâmetros ajuda a descrever a complexidade, mas não iguala custo computacional, regularização nem capacidade preditiva.

## 5. Estado dentro da janela; independência entre chamadas

Ao omitir `h_0`, a GRU começa cada janela com estado zero. As 24 medições daquela janela constroem seu estado. A chamada seguinte começa novamente em zero.

Guardar `hidden` no objeto e usá-lo no lote seguinte misturaria histórias de origens diferentes. Com `shuffle=True`, a primeira linha do próximo lote não é a continuação temporal da primeira linha do anterior. Além de depender da ordem de execução, esse estado poderia trazer informação posterior à origem que se pretende prever.

As conferências fazem três verificações concretas: prever um lote A, processar outro B e prever A novamente; permutar as origens dentro de A e desfazer a permutação; dividir o mesmo lote em 4+1 exemplos. As previsões devem permanecer iguais dentro da tolerância numérica. Isso verifica o comportamento deste modelo em `eval()`, não uma garantia sobre qualquer módulo com estado mutável.

Usamos uma GRU unidirecional para estudar esse fluxo. Uma rede bidirecional aplicada exclusivamente a uma janela passada não seria automaticamente vazamento: o ponto decisivo continua sendo quais observações estavam disponíveis na origem. Ela seria outra arquitetura e outro experimento.

## 6. Como o gradiente atravessa o tempo

A perda compara a saída final `[B,1]` com o alvo `[B,1]`. O estado final depende do anterior, que depende do anterior, até o início. `backward()` aplica a regra da cadeia por esse grafo de 24 passos. Como os pesos são compartilhados, contribuições dos diferentes passos se acumulam nos mesmos parâmetros.

Não se faz `detach()` entre as 24 posições: isso cortaria caminhos pelos quais a perda final ensina o processamento das posições anteriores. Também não se mantém o grafo entre janelas. O laboratório usa a GRU implementada pelo PyTorch e autograd; a atividade NumPy abaixo demonstra o forward de uma célula, sem substituir o treinamento.

O otimizador continua AdamW, taxa 0,001, weight decay 0,0001, lote 128, até 60 épocas, paciência oito e sementes 17/29/41. Não há busca de hiperparâmetros nem clipping de gradiente introduzido silenciosamente. A época de menor MSE de seleção é recarregada; a primeira vence empates. Todas as sementes são reportadas.

As escalas também são preservadas do M08.2: uma média e um desvio por lag, estimados apenas no ajuste, e uma escala para o alvo. Isso mantém comparabilidade, mas significa que o valor padronizado de uma mesma medição pode depender da posição em que entra na janela. Normalização global compartilhada entre passos é uma alternativa válida a estudar depois; mudar isso agora junto da arquitetura confundiria duas alterações.

## 7. O experimento e o resultado já verificado

O HGB recebe **os mesmos 24 lags de geração**, sem vento. Não é o HGB+vento dos folds de julho de unidades anteriores. Seus parâmetros foram fixados antes desta execução: 200 iterações, 15 folhas máximas, taxa 0,05, mínimo 20 exemplos por folha, L2=1, semente 17 e `early_stopping=False`. Não há divisão aleatória interna de validação. A MLP é ajustada novamente dentro desta comparação para registrar entradas, escalas, épocas e versões no mesmo protocolo.

Referência Linux/CPU, PyTorch 2.7.1, scikit-learn 1.8.0, execução `20261115T163556Z_bd3adefd`:

| Método | Semente | MAE | RMSE | Viés observado − previsto |
| --- | ---: | ---: | ---: | ---: |
| Persistência d2 | — | 37,991646 | 55,434342 | −3,016872 |
| Linear 24h | — | 33,678664 | 44,938111 | +15,148681 |
| HGB 24h | 17 | **31,846768** | 44,051119 | +11,662000 |
| MLP | 17 | 32,724828 | 44,019866 | +10,655947 |
| MLP | 29 | 33,700811 | 44,892316 | +12,652756 |
| MLP | 41 | 33,159788 | 44,069511 | +13,724279 |
| GRU | 17 | 35,675970 | 45,200733 | +18,525119 |
| GRU | 29 | 34,911227 | 43,816199 | +17,993098 |
| GRU | 41 | 34,573203 | **43,066021** | +14,777713 |

Todas as métricas estão em MWmed, nas mesmas 168 origens. A mediana do MAE das GRUs é 34,911227, contra 33,159788 das MLPs. O HGB apresenta o menor MAE desse conjunto de variantes. As GRUs 29 e 41 têm RMSE menor que o HGB, mas MAE maior; a 17 perde nos dois. Esses resultados se referem aos checkpoints selecionados por MSE da janela anterior.

**Interpretação:** uma redução de erros quadráticos pode coexistir com maior erro absoluto médio. Alguns erros grandes pesam mais no RMSE, enquanto o MAE soma distâncias linearmente. Para atribuir a diferença a eventos específicos é preciso examinar `predictions.csv`; a tabela agregada não identifica a causa. Tampouco demonstra que memória recorrente seja prejudicial em geral.

No orçamento fixado, não há evidência para substituir as referências pela GRU com base em MAE. Ela permanece uma arquitetura implementada e compreendida. Ajustar muitas configurações até ganhar nesta mesma semana a transformaria ainda mais em seleção; isso não produziria um teste independente.

O pacote de entrada usado aqui é o M07.3 do professor Linux, reconstruído e conferido nas etapas anteriores. Seus hashes estão no protocolo. Ele não é declarado binariamente idêntico ao pacote Windows. Pequenas diferenças de bibliotecas, entradas ou plataforma devem ser examinadas antes de exigir igualdade byte a byte. O recarregamento dentro desta execução teve diferença zero nas seis redes; não se promete igualdade universal entre plataformas.

## 8. Ler evidências sem confundir execução com decisão

| Saída | Pergunta que responde |
| --- | --- |
| `protocol.json` | Quais entradas, versões, regras e códigos foram usados? |
| `particoes.csv` e `origens_sem_janela.csv` | Quem entrou em cada papel e quem foi excluído? |
| `janelas_avaliacao.csv` | Quais horários e valores delimitam cada previsão? |
| `curvas.csv` / `curvas.png` | Como ajuste e seleção evoluíram e onde ficou o checkpoint? |
| `summary.csv` / `predictions.csv` | Qual o desempenho agregado e por origem? |
| `preprocessing.json` | Quais escalas foram aprendidas no ajuste? |
| `*.pt`, `linear_24h.json`, `hgb_24h.joblib` | Quais estados/modelos foram persistidos? |
| `resultado.json` | Conferências, recarregamentos, tempos, memória e hashes das saídas |

`completed=True` significa que o protocolo terminou. Não é aprovação da qualidade do modelo. `operational_policy_approved=False` mantém esse limite explícito.

A memória registrada é o pico residente **do processo inteiro**, incluindo bibliotecas, dados e modelos treinados anteriormente no mesmo processo. Os bytes dos parâmetros e checkpoints são registrados separadamente. Não interprete o pico total como consumo isolado da GRU. Os tempos incluem as avaliações por época; uma execução sequencial não é um benchmark causal de hardware ou arquitetura.

## 9. Sua programação autoral: uma célula GRU em NumPy

Crie **`notebooks/m08_gru_autoral.py`** com a função abaixo, usando somente NumPy no cálculo. Não importe a referência do professor e não use `torch` para obter a resposta. O objetivo é transformar as equações da seção 4 em operações matriciais com as dimensões da seção 3.

```python
def passo_gru(x, h, weight_ih, weight_hh, bias_ih, bias_hh):
    # Implementar e devolver:
    # {"r": r, "z": z, "n": n, "h": novo_estado}
    ...
```

Contrato: `x [B,I]`, `h [B,H]`, `weight_ih [3H,I]`, `weight_hh [3H,H]`, dois vieses `[3H]`. As entradas são finitas, float64 e podem estar somente para leitura. Devolva quatro arrays `[B,H]`, sem modificar entradas. O verificador usa diferentes B/I/H; não fixe 16 ou 24 dentro dessa função.

Sequência de raciocínio: calcule as duas transformações afins; separe cada resultado em três blocos de colunas; forme as duas sigmoides; forme o candidato com a porta no lugar correto; combine candidato e estado anterior. Como os exemplos estão nas linhas, as matrizes de pesos entram transpostas. Faça primeiro o exemplo escalar `h=0,8`, `n=−0,2`, `z=0,75` no papel para conferir o sentido da atualização.

Confira sua função **sem treinar novamente**:

```powershell
python notebooks/laboratorio_gru.py --autoria notebooks/m08_gru_autoral.py --verificar
```

O verificador compara portas, estado final e uma sequência de 24 passos com a implementação de referência e `torch.nn.GRUCell/GRU`, além de verificar preservação de entradas. A tolerância é `1e-12` em float64. O arquivo `conferencia_sem_treino.json` registra seu hash. O modo autoral confere o forward NumPy; os modelos do experimento continuam treinados por autograd.

## 10. Parecer e critério de conclusão

Escreva **`reports/parecer_m08_gru.md`** com quatro argumentos sustentados por sua execução:

1. **Arquitetura:** explique `[B,24,1]`, `hidden[-1]`, as duas portas e o total 929. Mostre por que carregar estado entre lotes embaralhados muda o problema.
2. **Treinamento:** apresente melhor época e parada por semente; contraste curvas de ajuste e seleção. Explique por que a seleção por MSE não garante menor MAE na semana seguinte.
3. **Comparação:** compare GRU, MLP, linear e HGB nas mesmas origens; reporte todas as sementes e a mediana, sem chamar a faixa de intervalo de confiança. Separe o HGB histórico atual do antigo HGB com vento.
4. **Decisão e limite:** escolha uma referência provisória conforme a métrica que você defende. Use erro, viés, custo e complexidade; indique o que seria necessário para uma decisão em outros períodos sem reutilizar esta semana como teste intocado.

Entrega para revisão: sua função NumPy, saída da conferência, `summary.csv`, `resultado.json` e o parecer. Não é necessário enviar todos os pesos nem reconstruir Docker. A unidade termina quando a implementação, a interpretação e a execução forem conferidas; não será prolongada com novos exercícios de calendário ou instalação. Depois segue M09, atenção e comparação fundacional, conforme o roteiro.

## Referências primárias

- [PyTorch 2.7 — GRUCell: equações e pesos](https://docs.pytorch.org/docs/2.7/generated/torch.nn.GRUCell.html).
- [PyTorch — GRU: shapes, estados e dropout entre camadas](https://docs.pytorch.org/docs/stable/generated/torch.nn.GRU.html). A página estável pode acompanhar uma versão mais recente; a execução e as conferências deste pacote usam **2.7.1+cpu**, registrada nos metadados.
- O suporte de entrada/MLP foi preservado do código distribuído em M08.2. As conclusões numéricas acima vêm dos artefatos desta execução, não da documentação de API.
