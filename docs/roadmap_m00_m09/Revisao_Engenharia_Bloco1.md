# Revisão de engenharia aplicada — bloco 1

25/11/2026 · responsável: Codex, agente principal · escopo aplicado definido pelo usuário.

O usuário esclareceu que deseja execução e explicação de engenharia, sem atuar como aluno em uma avaliação. Os critérios de exercício/resposta independente foram preservados no histórico do cadastro e substituídos, no portão de engenharia, por entregáveis aplicados verificáveis. As soluções são atribuídas ao trabalho técnico fornecido; não há declaração de domínio ou autoria pessoal do usuário.

## Conclusão da revisão

Aprovo tecnicamente as 14 entregas de engenharia do bloco 1: M00-01, M01-01, M01-02, M02-01–05, M04-01, M06-01, M07-04, M08-01, M09-01 e M09-03. A aprovação cobre as análises e os limites declarados; não libera operação do serviço.

| Área | Revisão efetuada |
| --- | --- |
| Fluxo temporal M00 | Relógios da nova configuração formalizados; diferença entre o contrato h+1 e a adaptação descrita sem reidentificar o estimador antigo como outro horizonte |
| SQL M01 | Mês real fixado; contagens, médias, nulos, zeros, lacunas, duplicidades, quarentena, calendário e LAG reconciliados com pandas e conta manual |
| Contexto da janela | Consulta suplementar calcula LAG antes de filtrar o mês; preserva saída inicial e elimina o falso vazio de fronteira com dado real anterior |
| Probabilidade | Contingência e Bayes conferidos com fração exata; taxa-base e sensibilidade separadas |
| Estimação | Média, variância e intervalos derivados e executados; hipótese IID e dependência separadas |
| Hipóteses | Seis médias de blocos usadas sem fabricar série horária; efeito mínimo e família Bonferroni distintos |
| Regressão | OLS/Ridge, fator nλ, shapes, gradiente, estabilidade e posto conferidos analiticamente |
| Bootstrap | Reconstrução com pareamento, circularidade por fold, agregado ponderado e 59 testes; execução real de M02-08 continua no bloco 2 |
| Vento E51 | Chaves exatas, valores finitos, geometria/tolerância, invariância à ordem e 38 casos aprovados sem treino/recarga de modelo |
| Registro e arquivos | Oito arquivos acessíveis na leitura autorizada e hashes corretos; versões históricas e diferenças de código preservadas |
| M07 | Janela, versão simulada, cronômetro, broadcast e limites de AQE explicados sem repetir Databricks |
| Pré-treino | Identidade preservada e sobreposição desconhecida, sem alegar ausência de contaminação |

Os dois executores quantitativos e SQL novos estão separados das demonstrações anteriores. Seus protocolos precedem as execuções e seus recibos registram preservação dos artefatos anteriores. Foram lidos os códigos, soluções e resultados. Os cálculos manuais centrais conferem: Bayes 85/232, s²=20/3, OLS [2;5/4], Ridge [2;10/9], LAG de fronteira -45,057 MWmed e média de 15/11 igual a 1.479,44/24.

A documentação de [origem das previsões](Origem_Dados_e_Previsoes.md) foi conferida contra parâmetros e arquivos locais: ONS é a fonte da geração usada; o vento vem do GFS/NOAA via Open-Meteo; os modelos Renewcast produzem as saídas em MWmed/quantis/probabilidade. Essa distinção não modifica os datasets preservados.

## Aceite separado da operação

M04-02, M04-03, M04-04 e M04-05 conservam estado bloqueado para operação. Produzir relatórios e o mecanismo bitemporal não fornece as datas históricas de publicação, a semântica temporal ONS ou as versões cadastrais que faltam. Esses itens não foram marcados como comprovados.

O portão de engenharia verifica os 14 itens aplicados; os quatro bloqueios devem continuar visíveis fora dele. O fechamento de todos os 18 e o portão operacional permanecem distintos. O código de verificação recebeu testes que impedem confundir esses dois aceites ou aprovar um portão de engenharia vazio.

Os detalhes e valores estão em [Relatorio_Engenharia_Bloco1.md](Relatorio_Engenharia_Bloco1.md). O aceite técnico não exige resposta adicional do usuário e não inicia os blocos 2 ou 3.
