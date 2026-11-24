# M10.3: do escore ao início de alarme

Esta unidade separa escore, condição e notificação. A
[função implementada](../../notebooks/m10_3_alarme_autoral.py) percorre a grade
e marca quando uma sequência confirma um alarme. O
[resultado Windows](../../reports/m10_3/20261123T195301Z_332fb306/resultado.json)
identifica a execução `20261123T195301Z_332fb306`, a política congelada e a
comparação com a referência.

## 1. O contador e o instante da confirmação

O contrato recebe dois vetores na ordem da grade: escores numéricos e
`utilizavel` booleano. O limiar deve ser finito, e `consecutivos=k` é
inteiro positivo. A função devolve um vetor booleano do mesmo tamanho,
preservando as entradas e todas as linhas.

Uma condição alta exige `utilizavel=True` e `escore >= limiar`. A igualdade
conta. Se a condição é alta, o contador aumenta; caso contrário, zera:

```text
c_t = c_anterior + 1, quando utilizável e acima ou igual ao limiar
c_t = 0, nos demais casos
início_t = True somente quando c_t == k
```

Usar `>= k` emitiria notificações repetidas na mesma sequência. Com `k=1`,
somente a primeira leitura alta dispara; as seguintes continuam na sequência.
O carimbo é o instante da confirmação, sem voltar ao primeiro cruzamento.
Na grade de 15 minutos, duas leituras exigem 15 minutos entre elas.

## 2. A linha ausente precisa continuar na grade

Para limiar 0,70 e k=2:

| Índice | Escore | Utilizável | Contador | Início |
|---|---:|---|---:|---|
| 0 | 0,70 | Sim | 1 | Não |
| 1 | 0,80 | Sim | 2 | Sim |
| 2 | 0,90 | Sim | 3 | Não |
| 3 | 0,95 | Não | 0 | Não |
| 4 | 0,88 | Sim | 1 | Não |
| 5 | 0,89 | Sim | 2 | Sim |
| 6 | 0,65 | Sim | 0 | Não |
| 7 | 0,71 | Sim | 1 | Não |
| 8 | 0,71 | Sim | 2 | Sim |

Os índices de disparo são **[1,5,8]**. O escore finito da linha 3 não
substitui sua flag de indisponibilidade. Remover essa linha elimina o reset:
as linhas originais 2 e 4 ficam artificialmente adjacentes, a sequência
continua e desaparece a confirmação original do índice 5. Ao mapear para
os índices originais, restariam [1,8].

O contador começa em zero a cada período. Rótulos não entram nessa função;
uma categoria ignorada na avaliação não reinicia a contagem por si só.
A mesma leitura de um prefixo deve produzir decisões iguais antes da
chegada das linhas seguintes.

## 3. Escolher antes de abrir o teste

Os escores de 2008–2010 geram 11 quantis para cada um dos três métodos:
33 pares método–quantil. `method="higher"` escolhe cortes presentes nos
escores. Empates podem produzir limiares iguais e muitos pontos no corte;
o quantil não é probabilidade de evento.

Um candidato precisa detectar pelo menos um ID e respeitar o teto de
**0,50 alarme sem anotação por dia equivalente de exposição**. Entre os
viáveis, maximiza-se IDs detectados; depois minimizam-se taxa sem anotação
e atraso mediano, seguindo a ordem fixa de métodos e o quantil maior
nos empates restantes.

A sequência executada é: selecionar no desenvolvimento, gravar
`politica_congelada.json`, reconstituir somente a floresta original se
necessário, verificar seus escores e disparos no desenvolvimento e só
então avaliar 2011–2013. As árvores foram reconstituídas em 2004–2007,
com configuração e semente originais; a diferença de escores no
desenvolvimento foi zero. O teste não ajusta modelo, limiar ou confirmação.

## 4. Crédito por ID e denominadores

Um evento é a união dos intervalos `Anomaly` do mesmo ID, preservando os
espaços entre intervalos. Um início pode dar crédito a apenas um ID ainda
não detectado. Entre IDs ativos, vence o intervalo que termina primeiro;
empate por ID. Novos inícios num ID já detectado são repetições, sem crédito
adicional. Um alarme anterior ao intervalo não recebe crédito retroativo.

Inícios em `Rare Event` ou `Communication Gap` são ignorados nesta avaliação,
inclusive em sobreposições. Fora das categorias ficam os alarmes sem anotação,
proxy de falso alarme. Isso não comprova ausência de falha física.

Um ID é observável quando possui ao menos um instante elegível. Isso não
garante duração ou cruzamentos suficientes para k confirmações.

Cada instante utilizável sem anotação representa 900 segundos de exposição.
Assim, 96 instantes equivalem a um dia, independentemente dos dias de
calendário. No desenvolvimento Windows:

```text
exposição = 101133 / 96 = 1053,46875 dias equivalentes
taxa = 4 / 1053,46875 = 0,0037969802 alarme/dia equivalente
```

Houve 15 inícios: três primeiros créditos, seis repetições, quatro sem
anotação e dois ignorados. A precisão é `3/(15-2)=3/13`, ou 23,08%.
O orçamento controla alarmes sem anotação, sem limitar sozinho toda a
carga de investigação, que também inclui repetições e ignorados.

## 5. O que o resultado Windows permite concluir

Dos 33 candidatos, 29 foram viáveis. A política escolhida foi Isolation
Forest, limiar **0,7199442558330269**, k=2 e quantil 0,9995.

| Medida | Desenvolvimento | Teste |
|---|---:|---:|
| IDs detectados / observáveis | 3/8 | 0/8 |
| Inícios | 15 | 0 |
| Pontos utilizáveis que atingiram o corte | 2.822 | 0 |
| Maior escore utilizável | 0,7593997321 | 0,7164359651 |

No teste, a taxa sem anotação é zero, mas oito IDs observáveis foram
perdidos. Sem início avaliável, precisão seria 0/0: o relatório conserva
`null`, correspondente a `None`. Os atrasos mediano e P90 também ficam
indefinidos quando não há detecções, em vez de virar atraso zero.
No desenvolvimento, foram 26,82835 e 98,46783 minutos, calculados somente
nos IDs detectados desde o primeiro início anotado do ID.

Aqui o máximo utilizável ficou abaixo do limiar. Logo, por dedução,
reduzir k para 1 mantendo esse corte continuaria sem disparos. É diferente
de encontrar cruzamentos altos esparsos, todos interrompidos antes de k:
nesse segundo cenário, mudar a confirmação poderia alterar os inícios.
Essa distinção é analítica; não executa outra política sobre o teste.

## 6. O próximo diagnóstico precisa preservar esta evidência

Uma hipótese para M10.4 é mudança na distribuição dos canais, de suas
combinações ou dos regimes representados pelo escore. O resultado atual
não identifica causa física, manutenção ou sensor defeituoso.

As ablações devem ser planejadas e comparadas no desenvolvimento, mantendo
dados, transformações e critérios sob controle. Depois de consultar
2011–2013 para diagnóstico, esse período não deve ser chamado de teste
independente de uma nova regra escolhida a partir dele.

Os [candidatos](../../reports/m10_3/20261123T195301Z_332fb306/candidatos_dev.csv),
a [política](../../reports/m10_3/20261123T195301Z_332fb306/politica_congelada.json)
e o [relatório](../../reports/m10_3/20261123T195301Z_332fb306/relatorio.html)
permitem conferir essa sequência. Os dez testes pequenos passaram; isso
verifica a implementação, sem aprovar a política para operação.
