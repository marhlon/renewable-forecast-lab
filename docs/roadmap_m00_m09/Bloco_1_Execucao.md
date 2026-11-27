# Bloco 1 — entrega de engenharia concluída

25/11/2026 · etapas 1–3 · Renewcast/P1

O usuário esclareceu que deseja código aplicado e explicações, sem exercícios ou avaliação de aluno como condição de entrega. A consolidação foi feita nesse escopo: **14 itens de engenharia validados**, sem nenhuma resposta do usuário pendente. As quatro comprovações de fonte permanecem como restrições para operação.

| Escopo | Resultado atual |
| --- | --- |
| Entrega aplicada de engenharia do bloco 1 | 14/14 itens validados |
| Espera por exercícios/respostas do usuário | Nenhuma para esta entrega |
| Comprovações operacionais M04-02–05 | Quatro restrições preservadas |
| Blocos 2 e 3 | Planejados; não executados nesta consolidação |

## Leia a explicação completa

O [Relatorio_Engenharia_Bloco1.md](Relatorio_Engenharia_Bloco1.md) explica fontes, transformações, código corrigido, testes, resultados e limites em detalhe.

Os relatórios específicos são:

- [Origem dos dados e das previsões](Origem_Dados_e_Previsoes.md): geração ONS, cadastro ONS/ANEEL, vento NOAA/GFS via Open-Meteo e saídas dos modelos.
- [SQL aplicado ao mês real](Diagnostico_SQL_Aplicado.md): 720 horas de novembro/2025, 49 zeros, médias, cobertura, duplicidades e LAG com contexto anterior.
- [Fundamentos aplicados e resultados](Fundamentos_Aplicados_Resultados.md): probabilidade, intervalos, hipóteses, regressão, gradiente e estabilidade, resolvidos por código e por conta.
- [Revisão de engenharia](Revisao_Engenharia_Bloco1.md): escopo do aceite técnico e as restrições que não foram convertidas em fatos.

Os arquivos preparados anteriormente para exercícios continuam preservados como histórico; as novas soluções são técnicas fornecidas, sem atribuição de autoria independente ao usuário.

## O que foi concluído

E51 usa as chaves exatas de vento e passou em 38 casos. O bootstrap tem resumo/CLI completos e passou em 59 testes pequenos. O cadastro bitemporal foi implementado e exclui vigência não comprovada. Os oito arquivos do registro foram conferidos fora do sandbox, com hashes corretos, sem restauração.

O mês real foi analisado em SQL e pandas: 720 horas válidas, 30 dias, 49 zeros e nenhum NULL, gap ou duplicata. A média é 28,2609791667 MWmed. A aplicação do LAG antes do filtro, com a hora anterior de outubro, fornece 720 pares completos; o primeiro delta é -45,057 MWmed.

Os quatro casos quantitativos foram resolvidos integralmente, com quatro testes novos e 24 conferências analíticas aprovados. O controle de roadmap tem 32 testes aprovados e um ignorado por restrição de symlink no Windows.

A rastreabilidade identifica os arquivos de previsão pontual, quantis e probabilidade de queda. M08/M09 usam só geração histórica; os estudos meteorológicos anteriores também usam vento previsto.

## Critério de engenharia e operação

```powershell
python scripts/verificar_roadmap.py --bloco 1 --gate engenharia
python scripts/verificar_entrega_bloco1.py
```

Ambos passaram. A conferência de artefatos compara **258 declarações de hash**, incluindo resultados anteriores e novos.

```powershell
python scripts/verificar_roadmap.py --bloco 1 --gate operacao
python scripts/verificar_roadmap.py --bloco 1 --exigir-fechamento
```

Esses comandos ainda devem apontar M04-02, M04-03, M04-04 e M04-05: fuso/borda do intervalo, publicação histórica da meteorologia, vigência cadastral e homologação point-in-time. Identificar a fonte não fornece os registros históricos que faltam. O [quadro de fontes](Fontes_e_Limites.md) conserva a análise dessas restrições.

O [aceite aplicado](aceite_engenharia_bloco1.json), as [restrições operacionais](restricoes_operacao_bloco1.json), o [cadastro](../../config/roadmap_m00_m09.json) e a [conferência dos artefatos](conferencia_artefatos_bloco1.json) mantêm essas decisões separadas.

Não foi necessário abrir Docker ou outro aplicativo. Não houve treino novo dos benchmarks, download de pesos, contato com provedores ou implantação. Não é necessário responder às perguntas anteriores para seguir com a entrega de engenharia.
