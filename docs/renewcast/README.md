# Renewcast

Previsão de geração eólica com dados do Operador Nacional do Sistema Elétrico (ONS), comparação temporal e decisões apoiadas por evidências.

Uma previsão só pode usar a informação disponível quando a decisão é tomada. Este estudo pergunta se modelos aprendidos melhoram uma referência simples e como erro, viés e intervalos mudam essa escolha. O recorte principal é o conjunto `CJU_BA5EIGT`, com geração em megawatts médios (MWmed).

A leitura é voltada a profissionais e lideranças de Data Science e Analytics interessados em avaliar modelos antes de aplicá-los ao planejamento de geração. A comparação apresentada usa somente histórico de geração e calendário; os estudos meteorológicos têm contratos separados.

**Figura central proposta:** observado, persistência, modelo aprendido e quantis nas 671 origens da avaliação final de setembro/2026, em MWmed. A [especificação da figura](FIGURA_PROPOSTA.md) identifica entradas, legenda, período e texto alternativo. Não foi localizada uma figura pronta desse recorte; as imagens de desenvolvimento de julho permanecem nos respectivos relatórios.

Os três achados abaixo pertencem à execução Windows/CPU identificada pelo diretório `bloco3_engenharia/M03-04`, partição final retrospectiva de setembro/2026. O [recibo](evidencias/resultado.json) foi concluído em 26/11/2026; ele não contém campo `run_id`. A identificação por diretório, data e hash está no [mapa de evidências](FONTES.md).

1. **A persistência manteve o menor erro absoluto médio.** Nas mesmas 671 origens, o candidato de boosting de gradiente por histogramas (HGB) não atingiu o ganho mínimo predefinido. O erro absoluto médio (MAE) e a raiz do erro quadrático médio (RMSE) estão em MWmed:

   | Previsão | MAE | RMSE |
   | --- | ---: | ---: |
   | Persistência | **35,616479** | 50,351806 |
   | Chronos-Bolt Tiny P50 | 35,689509 | **47,649804** |
   | HGB selecionado no desenvolvimento | 40,160344 | 48,084892 |

   O intervalo condicional de 95% do ganho de MAE do Chronos frente à persistência foi de −3,151100 a 2,969704 MWmed. Isso não demonstrou ganho convincente. [Métricas](evidencias/summary.csv) e [bootstrap](evidencias/bootstrap_pareado.csv).

2. **Reduzir erros grandes não garantiu menor MAE.** As três sementes da rede recorrente com portas (GRU) tiveram RMSE entre 45,015515 e 47,425211, abaixo da persistência; seus MAEs, entre 36,550595 e 38,939038, foram maiores. Todas foram preservadas, sem escolher uma semente pelo teste. P50 estima a mediana; os modelos têm objetivos, entradas e ajustes distintos, portanto esta comparação não isola o efeito da arquitetura. [Todas as variantes](evidencias/summary.csv).

3. **A cobertura melhorou com um intervalo largo demais para o critério fixado.** A calibração conformal de quantis (CQR) elevou a cobertura de 56,04% para 76,15%, com largura média de 135,21 MWmed, acima do limite de 100. Os quantis brutos P10–P90 do Chronos cobriram 67,51%, abaixo da meta nominal de 80%. Não houve recalibração nessa partição. [Intervalos e decisão](evidencias/metricas_intervalos.csv).

**Como foi feito**

- Fixar alvo em origem+24h e usar 24 medições até origem−2h, sob atraso assumido de duas horas.
- Separar ajuste, calibração, escolha de política e avaliação cronologicamente.
- Congelar código e artefatos antes de obter o snapshot de setembro.
- Comparar 14 variantes nas mesmas origens, preservando todas as sementes.
- Reamostrar erros pareados em blocos horários, respeitando a dependência local.
- Manter os critérios de decisão mesmo diante de resultados desfavoráveis.

**Como reproduzir**

Para conferir os resultados salvos na estação Windows documentada: Python 3.12, ambiente `renewable-forecast` já preparado e pacote local de evidências completo. Da raiz:

```powershell
conda activate renewable-forecast
python -X utf8 scripts/verificar_roadmap.py --bloco 3 --gate engenharia
python -X utf8 scripts/conferir_bloco3.py
```

Esses comandos conferem o cadastro e recomputam métricas salvas; não repetem treino ou inferência. O [guia de reprodução](REPRODUCAO.md) detalha dependências, arquivos ausentes do clone e os fluxos separados. Instalar o pacote básico não recompõe pesos e dados locais.

**Limitações e próximo passo**

O snapshot é retrospectivo e já foi examinado. Fuso físico, significado do intervalo e disponibilidade histórica efetiva ainda precisam de comprovação; o atraso é uma hipótese. A sobreposição com o pré-treino do Chronos é desconhecida. O próximo ensaio deve definir outra janela antes da coleta e validar essas condições, preservando esta avaliação e sem promover automaticamente um modelo.

Críticas técnicas são bem-vindas: qual decisão mudaria ao priorizar MAE, erros grandes ou custo assimétrico? Indique o recorte e a evidência que sustentariam a mudança.

Dados: [ONS — Geração por Usina em Base Horária](https://dados.ons.org.br/dataset/geracao-usina-2), conjunto `CJU_BA5EIGT`. Pesos e revisão: [identidade do Chronos](../model_source_m09_3.json). Contribuições e assistência estão registradas nas [revisões do projeto](../roadmap_m00_m09/Consolidado_M01_M09.md).
