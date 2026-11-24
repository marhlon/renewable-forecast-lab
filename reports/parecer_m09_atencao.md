# Parecer M09.1 — acessos permitidos e representação histórica

Execução autoral Windows de 17/11/2026, com Python 3.12.13, NumPy 2.5.3 e
PyTorch 2.7.1+cpu. A função NumPy foi aplicada à janela real, além da
conferência sem leitura da série. Os oito grupos passaram, com diferença
máxima de `4,440892098500626e-16` para PyTorch, abaixo de `1e-12`.
Os seis testes adicionais também passaram. Isso confere a operação,
sem avaliar capacidade preditiva.

## Conta, eixos e máscara

Nesta execução, Q/K têm shape `[1,24,4]`; V e saída, `[1,24,1]`;
os pesos, `[1,24,24]`. Cada linha é uma consulta e cada coluna uma chave.
O produto troca somente os dois últimos eixos de K e conserva os exemplos
separados. Divide-se por `sqrt(D)` e normaliza-se sobre S, o eixo das
chaves, para cada consulta. A máscara usa **True = permitido**; scores
bloqueados recebem `−inf` antes do softmax. Subtrair o máximo por linha
estabiliza a exponencial. Cada distribuição soma um.

Com scores já escalados `[ln(3),0]`, as exponenciais são proporcionais a
`[3,1]`, produzindo pesos `[0.75,0.25]`. Para valores `[10,30]`, a saída
é `0.75×10+0.25×30=15`. Permitindo somente a segunda chave, os pesos são
`[0,1]` e a saída é 30.

## Três decisões de interpretação

**Atenção livre é permitida neste contexto conhecido.** A origem é
03/07/2026 às 04h; a janela vai de 02/07 às 03h a 03/07 às 02h.
Sob atraso assumido de duas horas, todas as 24 medições estão disponíveis
na origem. Consultá-las livremente respeita esse corte. Os timestamps
continuam sem fuso físico validado. Um prefixo interno exige outra regra:
a posição 5 só pode consultar 0–5 quando esse é o processamento pretendido.
A máscara triangular inferior protege esse acesso. Com V `[0,6,12]` e
scores iguais, a saída livre é `[6,6,6]` e a causal, `[0,3,6]`.

**A última consulta coincide nesta configuração.** Livre e causal permitem
as mesmas 24 chaves na posição final. Com uma camada, mesmos Q/K/V e
sem Dropout, a diferença observada foi zero; ambas produziram representação
64,627211. Isso não se estende automaticamente a camadas empilhadas,
cujas entradas intermediárias podem ter sido construídas com acessos diferentes.

**Os mapas não aprovam uma previsão.** As projeções Q/K são fixas e não
treinadas, e V contém geração histórica. A saída é uma combinação convexa
dos valores permitidos, sem previsão h24, MAE ou RMSE. Um peso alto não
comprova causalidade física nem importância para a geração futura.

Sem posição, permutar conteúdo produziu diferença máxima de
`1,4210854715202004e-14`, compatível com equivariância na tolerância usada.
Com índices posicionais fixos, trocar os conteúdos produziu diferença
`4,6390829343196955`. Esse teste distingue qual conteúdo ocupa cada posição;
permutar conteúdo e posição juntos seria outra operação. Ele não demonstra
que essa codificação melhora previsões.

## Fechamento do M08

Sem repetir treino ou testes, mantenho o HGB histórico como referência
provisória por MAE: 32,323956 MWmed, ante mediana MLP 33,159788 e GRU
34,911227. A GRU 41 tem RMSE 43,066020, melhor que 44,221683 do HGB,
mas MAE 34,573202. O viés observado menos previsto permanece positivo:
+13,119039 no HGB e +14,777710 na GRU 41. O ajuste do HGB registrou
0,69 s; as MLPs, 7,32–11,93 s por semente; as GRUs, 51,37–91,34 s,
incluindo avaliações por época nas redes. Não é benchmark controlado.
Esses números vêm do [resumo Windows auditado](neural/CJU_BA5EIGT/m08_3_gru/20261115T170309Z_90a6625f/summary.csv).
A semana já foi examinada; a decisão precisa de novos períodos com
protocolo fixado antes da avaliação. Nada disso atribui desempenho preditivo
à atenção desta unidade ou autoriza promoção operacional.

## Evidências

[Função](../notebooks/m09_atencao_autoral.py) e [guia](../docs/Explicacao_M09_1_Passo_a_Passo.md);
[conferência autoral](transformer/CJU_BA5EIGT/m09_1_atencao/20261117T144205Z_917f4acf/conferencia.json),
[resultado](transformer/CJU_BA5EIGT/m09_1_atencao/20261117T144205Z_917f4acf/resultado.json),
[relatório HTML](transformer/CJU_BA5EIGT/m09_1_atencao/20261117T144205Z_917f4acf/relatorio.html)
e [mapas exportados](transformer/CJU_BA5EIGT/m09_1_atencao/mapas_atencao_20261116.png).

A [nota de conferência de 17/11](../docs/Conferencia_M09_1_20261117.md)
registra os comandos, logs e hashes da execução com `--autoria`. O laboratório
terminou sem avisos, tratando `UserWarning` como erro. A formatação do HTML
foi conferida em 72 células float e 24 datas, sem alterar os resultados numéricos.
