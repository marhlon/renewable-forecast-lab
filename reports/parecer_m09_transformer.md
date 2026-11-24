# Parecer M09.2 — composição local encoder–decoder

Este laboratório local foi preparado para revisão da M09.2. Sua execução
não constitui aceite curricular automático nem reprodução de um contrato
distribuído anteriormente. A análise usa o run Windows
`20261117T151609Z_61643ec2`: Python 3.12.13, PyTorch 2.7.1+cpu, NumPy 2.5.3
e pandas 3.0.5, em CPU/float64.

## Arquitetura observada

O histórico `[1,24,1]` corresponde às medições de 02/07/2026 às 03h a
03/07 às 02h, para a origem de 03/07 às 04h, sob atraso assumido de duas
horas. A normalização usa somente as 7.079 janelas de ajuste. O eixo
temporal permanece sem fuso físico validado.

A projeção afim de entrada e as posições senoidais produzem `[1,24,16]`.
Dois blocos encoder geram memória com o mesmo shape. As seis consultas
sintéticas começam zeradas em `[1,6,1]`; sua projeção inclui viés e recebe
posição, produzindo `[1,6,16]`. Dois blocos decoder devolvem `[1,6,16]`.
Esses índices são slots, sem associação automática a horizontes futuros.
Não há teacher forcing ou cabeça que converta as coordenadas em MWmed.

Cada atenção projeta Q/K/V, separa quatro cabeças de quatro coordenadas,
normaliza scores sobre as chaves e concatena suas saídas antes da projeção
final. A escala usa `sqrt(d_head)=2`, não a raiz de 16. A FFN aplica
`16→32→16`, com ReLU, separadamente em cada posição.

Os residuais somam a transformação à entrada da subcamada. A LayerNorm
vem depois da soma e atua nas 16 coordenadas de cada token. Há duas
subcamadas no encoder e três no decoder: self-attention causal,
cross-attention e FFN. Na cross-attention, Q vem do decoder; K/V vêm da
memória histórica fixa. Ambas as pilhas têm duas camadas distintas e nenhuma
norma extra ao final. A contagem medida foi **11.200 parâmetros**.

## O que as conferências sustentam

Treze grupos passaram, com diferença máxima de `6,661338147750939e-16`,
abaixo da tolerância absoluta `1e-12`. As comparações copiaram pesos e
vieses para módulos PyTorch equivalentes, incluindo as pilhas de duas camadas.
Os 12 testes unittest também terminaram com retorno 0 e `OK` nos logs.
Essas evidências verificam a composição, sem medir qualidade de previsão.

A implementação usa **True = permitido**. O comparador inverte a máscara,
pois MultiheadAttention e Transformer do PyTorch usam True como bloqueado.
Foram verificadas atenção retangular, soma das probabilidades, bloqueios,
residuais, normalização, dimensões e separação entre exemplos do batch.
Dropout ficou desativado em `eval()` nas comparações.

Na janela real, alterar as duas últimas consultas deixou o prefixo do
decoder com diferença zero, mantendo a memória fixa. Os slots alterados
mudaram em até `3,23832655045314`, mostrando que o modelo respondeu à
perturbação sem transmiti-la aos slots anteriores. O encoder livre pode
consultar todo o contexto fornecido, pois esse histórico já está disponível
na origem sob a hipótese adotada.

Nas contraprovas sintéticas, o diagnóstico de última consulta compara encoders
livre e causal. Com um
bloco, a diferença foi zero; com dois, `0,06132611481851291`. A última
consulta permite todas as chaves em ambos, mas os estados das posições
anteriores já diferem após o primeiro bloco. Isso explica por que a igualdade
de uma camada não é uma propriedade geral do empilhamento. Não indica falha
na proteção dos prefixos do decoder.

Sem posição, a permutação do encoder apresentou diferença de
`4,440892098500626e-16`. Com posições fixas, trocar conteúdos produziu
`1,4627723722006247`. O teste distingue conteúdo de posição, sem escolher
uma codificação pela sua capacidade preditiva.

A sonda não uniforme sobre a saída permitiu verificar gradientes finitos
e não nulos através da projeção de entrada, encoder e cross-attention.
Não houve `optimizer.step()`, e os parâmetros permaneceram iguais.
O checkpoint restaurou configuração, pesos e escalas; o recarregamento
reproduziu memória e decoder com diferença zero.

## Decisão e limites

O fluxo exportado permite acompanhar a expansão para 32 coordenadas na
FFN e o retorno a 16, além das somas e normalizações. Considero a composição
consistente com o desenho documentado e apta à revisão técnica local.
Seus parâmetros continuam aleatórios e não treinados. O estado persistido
não é um Transformer pré-treinado; não houve métricas de acurácia ou
benchmark preditivo. A M09.3 permanece outra entrega.

O HTML contém 12 mapas e 3.024 tooltips. A lógica de seleção das quatro
cabeças passou em teste isolado, com elementos simulados; os pesos exportados
formam 288 distribuições normalizadas, com zeros nos bloqueios causais.
Não houve inspeção visual em navegador, indisponível no ambiente.
A interação visual não foi usada como evidência de funcionamento matemático.

Uma composição Transformer não é, por si só, um modelo de linguagem.
Este exercício usa entradas numéricas e não contém tokenização, vocabulário,
cabeça de geração ou objetivo linguístico treinado.

## Evidências

[Módulo](../src/renewable_forecast/transformer_blocks.py),
[helper de conferência](../notebooks/m09_transformer_verificacao.py),
[laboratório](../notebooks/laboratorio_transformer.py) e
[aula](../docs/Aula_M09_2_Transformer.md).
Execução: [resultado](transformer/CJU_BA5EIGT/m09_2_transformer/20261117T151609Z_61643ec2/resultado.json),
[conferência](transformer/CJU_BA5EIGT/m09_2_transformer/20261117T151609Z_61643ec2/conferencia.json),
[fluxo](transformer/CJU_BA5EIGT/m09_2_transformer/20261117T151609Z_61643ec2/fluxo.csv),
[relatório HTML](transformer/CJU_BA5EIGT/m09_2_transformer/20261117T151609Z_61643ec2/relatorio.html)
e [recibo dos testes](transformer/CJU_BA5EIGT/m09_2_transformer/20261117T151609Z_61643ec2/execucao_testes.json).
O [diagrama de fluxo](transformer/CJU_BA5EIGT/m09_2_transformer/fluxo_transformer_20261117.png)
resume a composição; a [validação dos artefatos](transformer/CJU_BA5EIGT/m09_2_transformer/20261117T151609Z_61643ec2/validacao_artefatos.json)
registra as conferências adicionais dos CSVs e do HTML.
