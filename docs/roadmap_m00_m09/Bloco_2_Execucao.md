# Bloco 2 — etapas 4, 5 e 6

25/11/2026 · entrega aplicada de engenharia. O [relatório completo](Relatorio_Engenharia_Bloco2.md) explica procedimento, números, decisões e limites.

| Etapa | IDs | Construção e execução |
| --- | --- | --- |
| 4 — Incerteza e decisão | M02-06, M02-07, M02-08 | Clínica recuperada e executada; custos comparados; quatro bootstraps horários pareados aplicados às previsões antigas, com transferência de h24 para h6 |
| 5 — Modelos e atributos | M03-01, M03-02, M03-03 | Oito candidatos e três folds temporais; seleção por grupos; Shapley local exato e sensibilidade ao fundo; artefato congelado aplicado a outubro |
| 6 — Intervalos e eventos | M05-01, M05-02, M05-03 | Quantis/CQR; classificador/Platt e capacidade causal; novo alvo horário; calibração e política em períodos separados; aplicação sem ajuste em 695 origens comuns |

O protocolo e os modelos foram selados antes do download ONS. Outubro é um snapshot histórico recém-obtido nesta rodada, posterior ao ajuste e anterior ao congelamento real; não constitui shadow nem coleta prospectiva. Julho e agosto não foram reclassificados como teste intocado.

Resultados que determinam a decisão:

- HGB selecionado: MAE outubro 19,520624 MWmed; persistência: 19,218456. O ganho de junho não se confirmou na MAE reservada; o HGB melhorou RMSE.
- CQR: cobertura de 98,705%, largura de 103,168575 MWmed para meta de 80%; alerta de calibração acionado. Mais cobertura com largura excessiva não valida o intervalo.
- Platt: Brier agregado 0,083296 frente a 0,085677 bruto; uma semana piorou. Política congelada 0,3: 126 alarmes, 48 TP, 78 FP, 69 FN e custo 354; comparador 0,5 teve custo 308 sem ser promovido no teste.
- Rampa horária: MAE 6,974245 frente a 7,572565 da rampa zero; classificador não emitiu alarmes em 0,5 para os 39 eventos reais desse contrato.

O aceite aplicado abrange código, execução e análise desses resultados, inclusive os negativos. Estabilidade prospectiva de intervalos/classes permanece explicitamente em M06-05/C3–C4 no portão operacional. Os quatro bloqueios externos M04 continuam visíveis. Não há exercício ou resposta do usuário exigidos para o fechamento de engenharia.

Na raiz do projeto:

```powershell
python scripts/verificar_roadmap.py --bloco 2 --gate engenharia
python scripts/obter_avaliacao_bloco2.py verificar
python scripts/auditar_entrega_bloco2.py --freeze reports/fechamento_m00_m09/bloco2_engenharia/congelamento_avaliacao.json --download-receipt reports/fechamento_m00_m09/bloco2_engenharia/dados_avaliacao/fonte.json --check-registry
```

Esses comandos conferem a entrega preservada sem refazer modelos. Os arquivos locais ignorados devem estar presentes. Nenhum Docker, novo ambiente ou aplicativo gráfico é necessário. A permissão de rede para o download público foi concedida e usada. As etapas 7–9 continuam no bloco 3; CI remoto, operação ao vivo e recursos externos terão seus requisitos concretos informados quando esse bloco for executado.
