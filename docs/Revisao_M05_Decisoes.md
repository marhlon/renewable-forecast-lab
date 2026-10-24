# M05 — de probabilidades a decisões de alarme

Marlon Alves Bomfim · Renewcast · 03/10/2026 · evidências E61/E62

## Entrega reconhecida

O experimento de eventos foi reproduzido. Os oito arquivos enviados foram auditados: hashes, fonte, rótulos, cortes temporais, três resumos, nove linhas de métricas por fold e 60 linhas de diagnóstico de probabilidades conferem. As 24 linhas da tabela autoral de limiares também conferem em TP, FP, FN, TN e custo. Esta auditoria recalculou métricas; não reajustou os estimadores.

O exemplo autoral `y=[1,0,1,0]`, `p=[0.8,0.3,0.1,0.05]`, limiar 0,2 produz uma ocorrência em cada célula e custo 5: está correto.

Com quantis, calibração e classificação reproduzidos, a macroentrega técnica 7 está concluída no escopo exploratório. O painel passa a **7/10 = 70% das macroentregas do P1**, sem converter esse indicador em percentual de senioridade. A defesa de uma política e sua validação operacional são avaliações separadas. O próximo marco do produto é M06: serviço/lote e observação em shadow.

## O que os resultados sustentam

O evento continua sendo `y(t−2) − y(t+24) >= 22,77 MWmed`, sob atraso assumido de duas horas. Ele compara dois extremos separados por 26 horas; não significa qualquer queda ocorrida dentro das próximas 24 horas. Nas 504 emissões avaliadas, houve 113 rótulos positivos. São decisões horárias, não 113 episódios meteorológicos independentes.

| Método / limiar | Alarmes | TP | FP | FN | Precisão | Recall | Custo FP+4FN |
|---|---:|---:|---:|---:|---:|---:|---:|
| Frequência / 0,2 | 504 | 113 | 391 | 0 | 22,42% | 100,00% | 391 |
| Frequência / 0,5 | 0 | 0 | 0 | 113 | Indefinida | 0,00% | 452 |
| Logística / 0,2 | 146 | 78 | 68 | 35 | 53,42% | 69,03% | 208 |
| Logística / 0,5 | 81 | 53 | 28 | 60 | 65,43% | 46,90% | 268 |
| HGB / 0,2 | 156 | 90 | 66 | 23 | 57,69% | 79,65% | 158 |
| HGB / 0,5 | 109 | 74 | 35 | 39 | 67,89% | 65,49% | 191 |

O HGB/0,2 tem o menor custo agregado **entre as seis regras avaliadas**, sob a hipótese FP=1 e FN=4. A redução contra HGB/0,5 é 33 unidades relativas, ou 17,28%. Não são reais, MWmed nem economia financeira medida.

A troca de limiar recupera 16 positivos, mas acrescenta 31 falsos alarmes. Para uma razão de custos `r = C_FN/C_FP`, com C_FP positivo:

`C(0,2) − C(0,5) = C_FP × (31 − 16r)`.

O ponto de equilíbrio observado é `r = 31/16 = 1,9375`. Acima dele, HGB/0,2 custa menos neste conjunto. Abaixo, HGB/0,5 custa menos. Isso compara duas regras fixas em dados já observados; não estima um limiar universal ótimo.

| Fold | Custo HGB/0,5 | Custo HGB/0,2 | Diferença | Interpretação sob FN=4FP |
|---|---:|---:|---:|---|
| 1 | 81 | 50 | −31 | Oito FN evitados por um FP adicional |
| 2 | 76 | 80 | +4 | Três FN evitados por 16 FP adicionais |
| 3 | 34 | 28 | −6 | Cinco FN evitados por 14 FP adicionais |

No Fold 2, a razão de equilíbrio é 16/3, aproximadamente 5,33. A logística/0,2 custa 72 nessa semana. Escolher retrospectivamente o melhor método em cada semana usa o resultado para tomar uma decisão que deveria antecedê-lo; isso não constitui uma política prospectiva validada.

## Probabilidade, limiar e custo são objetos diferentes

Alterar o limiar conserva `p_event`, Brier e Average Precision; muda alarmes, matriz de confusão e custo. O HGB apresentou Brier agregado 0,111142, contra 0,174640 da frequência e 0,132262 da logística. A logística vence o HGB em Brier no Fold 2. Brier menor, isoladamente, não comprova calibração.

Sob custos constantes e probabilidades condicionais adequadas, o custo esperado de alarmar é `C_FP × (1−p)` e o de não alarmar é `C_FN × p`. Igualando os dois, o corte teórico é `C_FP/(C_FP+C_FN)`, que vale 0,2 para custos 1 e 4. Essa derivação não prova que o `p_event` estimado esteja calibrado nem dispensa avaliar a regra ao longo do tempo.

O ponto 1,9375 é uma **razão de custos de equilíbrio empírica**. O valor 0,2 é um **limiar de probabilidade**. Têm papéis e escalas diferentes.

Referências primárias: [separação entre classificação e decisão](https://scikit-learn.org/stable/modules/classification_threshold.html) e [calibração de probabilidades](https://scikit-learn.org/stable/modules/calibration.html).

## Ajustes no notebook autoral

A fórmula e as contagens foram preservadas. A versão entregue:

- usa uma entrada explícita, sem procurar outro `predictions.csv` pelo projeto;
- valida vetores de mesmo tamanho, rótulos binários e probabilidades finitas;
- exige os mesmos folds, emissões e rótulos nos três métodos;
- usa NaN quando precisão ou recall são indefinidos; zero alarmes não é precisão de 0%;
- acrescenta custo por emissão, sensibilidade de custos e rastreabilidade da origem;
- grava resultados derivados sem alterar probabilidades ou os relatórios do classificador.

O custo por emissão permite comparar janelas de tamanhos diferentes. Ele ainda representa a função de custo adotada; não corrige dependência temporal nem substitui uma avaliação por episódios, caso essa seja a necessidade operacional.

## Instalação e execução

Baixar `renewcast_m05_decisoes_20261003.zip` para `C:\renewable-forecast-lab`. No PowerShell já aberto nessa pasta, com o ambiente `renewable-forecast` ativo:

```powershell
Expand-Archive -LiteralPath .\renewcast_m05_decisoes_20261003.zip -DestinationPath . -Force
python notebooks/inspecao_decisoes.py
```

O pacote instala o notebook em `notebooks/inspecao_decisoes.py` e a documentação em `docs/`. Não é necessário reinstalar dependências nem executar novamente `weather_events`.

Entrada única padrão:

`C:\renewable-forecast-lab\reports\events\CJU_BA5EIGT\h24_d2_july_drop22p77_v1\predictions.csv`

Saída:

`C:\renewable-forecast-lab\reports\events\CJU_BA5EIGT\h24_d2_july_drop22p77_v1\decisions\`

Arquivos: `threshold_metrics.csv`, `cost_sensitivity.csv`, `hgb_tradeoffs.csv` e `metadata.json`. Reexecutar o notebook atualiza somente esses arquivos derivados. A tabela de sensibilidade mantém as regras fixas e compara razões de custos 1, 2, 4, 6 e 8.

A versão entregue foi executada nos arquivos do aluno. Também foram verificados caminho padrão fora da pasta corrente, caminho explícito inexistente, vetores incompatíveis, valores inválidos e rótulos divergentes entre métodos.

## Próxima prática autoral: política com restrição de capacidade

Mantenha `FP=1` e `FN=4`. Acrescente uma restrição **didática**, não fornecida por uma operação real: a equipe consegue tratar no máximo **120 alarmes nas mesmas 504 emissões**. Agora menor custo sozinho não basta; a regra precisa ser viável.

No mesmo `notebooks/inspecao_decisoes.py`, antes de `main`, implemente:

```python
def selecionar_politica(tabela: pd.DataFrame, max_alarms: int) -> dict:
    ...
```

Contrato:

1. Usar somente as linhas `fold == "Geral"` da tabela de decisões.
2. Considerar somente regras com `alarms <= max_alarms`.
3. Escolher o menor `cost_total`. Desempatar por menor número de alarmes e depois por `method` e `threshold`.
4. Se não existir regra viável, emitir `ValueError`; não devolver silenciosamente uma opção que viole a capacidade.
5. Retornar `method`, `threshold`, `alarms`, `cost_total`, `precision` e `recall` com tipos Python serializáveis. Representar razões indefinidas por `None` se for necessário serializar JSON estrito.

Dentro de `main`, imediatamente depois de `decisions = tabela_decisoes(df)`, acrescente:

```python
policy = selecionar_politica(decisions, max_alarms=120)
print("Política sob capacidade hipotética:", policy)
```

Rode o mesmo comando. Envie a função, o resultado e um parecer de quatro a seis linhas: qual regra foi escolhida, por que mudou ou permaneceu em relação à escolha sem restrição, qual compromisso entre alarmes e perdas foi aceito e por que isso ainda é uma decisão de desenvolvimento.

Essa função separa a política de alarme do estimador. Ela será a ponte para o contrato de serviço de M06: inferência devolve probabilidade; a política transforma probabilidade em ação e registra sua versão. Não é necessário novo treino para esta prática.

## Fixação lexical aplicada

| Termo | Significado neste projeto | Evidência no código |
|---|---|---|
| Limiar físico | Define o rótulo de queda de 22,77 MWmed | `event_drop` |
| Limiar de decisão | Transforma probabilidade em alarme | `p >= threshold` |
| Custo assimétrico | Um FN pesa quatro FP na hipótese atual | `FP + 4*FN` |
| Sensibilidade | Mudar custos conservando probabilidades e regras | `cost_sensitivity.csv` |
| Restrição de capacidade | Limita o número de alarmes que podem ser tratados | `alarms <= max_alarms` |
| Política | Regra explícita de escolha e ação | `selecionar_politica` |

Na próxima sessão, explique sem consultar o texto por que um modelo pode conservar o mesmo Brier e produzir uma política diferente. A evidência de aprendizagem será a função autoral e sua defesa, não repetir a definição dos termos.
