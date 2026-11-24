# Aula 1 — da leitura ao início de alarme

**Problema.** O Isolation Forest liderou a Average Precision no M10.2. Essa métrica mede um ranking de instantes. Um operador precisa de notificações, não de uma fila com dezenas de registros do mesmo incidente. Se um escore alto permanece por duas horas, deve ser possível emitir um início e acompanhar sua duração sem enviar um alerta novo a cada leitura.

## 1. Separe escore, condição e notificação

O escore é um número; suas unidades dependem do detector e ele não é uma probabilidade. O limiar \(L\) transforma cada leitura utilizável em uma condição: \(h_t=1\) quando \(s_t\ge L\). A condição precisa persistir por duas leituras consecutivas. A notificação é uma transição, não todo o intervalo em que \(h_t=1\).

Defina a contagem \(c_t=c_{t-1}+1\) se \(h_t=1\), senão \(c_t=0\). Um início de alarme ocorre quando \(c_t=k\), onde \(k=2\) no laboratório. O alerta torna-se disponível nesse instante, sem voltar o carimbo de tempo ao primeiro cruzamento. Com grade de 15 minutos, confirmar em duas leituras exige 15 minutos **entre os dois cruzamentos**. O tempo desde o começo do evento pode ser diferente.

| UTC | Escore | Utilizável | Contagem para limiar 0,80 | Início? |
| --- | ---: | --- | ---: | --- |
| 08h00 | 0,81 | Sim | 1 | Não |
| 08h15 | 0,80 | Sim | 2 | **Sim** |
| 08h30 | 0,90 | Sim | 3 | Não |
| 08h45 | ausente | Não | 0 | Não |
| 09h00 | 0,85 | Sim | 1 | Não |
| 09h15 | 0,87 | Sim | 2 | **Sim** |

A igualdade conta. Uma lacuna interrompe a contagem. Suprimir a linha das 08h45 na tabela antes de calcular mudararia a regra: as 09h00 passariam a parecer consecutivas às 08h30. A saída preserva a posição de cada linha justamente para manter a interpretação de tempo. A primeira leitura de cada período começa com estado zero. Anotações `Rare Event` ou `Communication Gap` são informação da **avaliação**, não motivo para zerar o contador durante o replay se a medição for utilizável.

## 2. Implemente e verifique

Crie `C:\renewable-forecast-lab\satellite-anomaly-monitor\notebooks\m10_3_alarme_autoral.py`. Use `import numpy as np` e implemente:

```python
def iniciar_alarmes(escores, utilizavel, *, limiar, consecutivos):
    """Um início de alarme por sequência; saída booleana com len(escores) posições."""
```

- `escores` é um vetor numérico na ordem da grade regular. Linhas ausentes podem conter NaN.
- `utilizavel` é um vetor booleano. Mesmo que o escore seja finito, `False` reinicia a contagem.
- `limiar` é finito, e `consecutivos` é inteiro positivo. Os insumos do laboratório são válidos.
- Retorne `np.ndarray` booleana. Preserve os argumentos, não filtre linhas, não recalcule o limiar e não consulte rótulos.

**Dica de implementação:** crie uma saída toda falsa, percorra os instantes da esquerda para a direita, atualize a contagem e marque só o instante em que ela alcança `consecutivos`. Se usar `>= consecutivos`, sinalizará repetidamente. Descobrir a duração de uma sequência olhando as linhas seguintes e marcar seu primeiro ponto também viola o contrato, mesmo que produza o mesmo total de alarmes no final.

A referência vetorial está em `src/satmon/alarmes_m10_3.py`. Ela usa o índice do último reset para calcular o comprimento atual da sequência. Você pode usar um laço; o objetivo é declarar a lógica de estado. O runner compara sua função com exemplos, prefixos e **cada** política candidata na grade real. A invariância de prefixo pergunta: se as últimas leituras ainda não chegaram, a notificação que já emiti continua a mesma?

**Prática de transferência:** suponha que o operador peça confirmação com três leituras. Refaça a conta da tabela sem mudar os escores. A regra tem de funcionar sem escrever “segundo” ou “terceiro” dentro da implementação: a quantidade chega pelo argumento. Na Aula 2 você lidará com uma implicação desse requisito: um evento pode ser observável e ainda assim não durar o suficiente para disparar.
