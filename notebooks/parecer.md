# Parecer Técnico de Monitoramento de Lote (M06.3)

**Data de Emissão:** 2026-10-05  
**Ativo do Modelo:** CJU_BA5EIGT / `h24_event_api_v1`  
**Lote Avaliado:** `h24_event_batch_v1`  

---

## 1. Métricas Probabilísticas Recalculadas de Forma Independente

A recomputação executada via consulta SQL direta e leitura do manifesto gerou os seguintes resultados:

* **Tamanho da Amostra Observada ($N$):** 24 emissões observadas
* **Frequência de Referência no Treino ($p_0$):** 0.242075 ($168 / 694$)
* **Brier Score do Modelo ($BS_{modelo}$):** 0.281875
* **Brier Score da Referência ($BS_{ref}$):** 0.187563
* **Brier Skill Score ($Skill$):** -50.28%

### Diagnóstico Estatístico
O ganho relativo descritivo sobre a referência fixa de treino é de **-50.28%**. No entanto, como $N = 24 < 168$ (limite mínimo de amostragem), o status retido é `insufficient_evidence`. As alterações no Brier Score decorrem unicamente da variação na composição da amostra avaliada, não indicando degradação do modelo.

---

## 2. Diagnóstico dos Quatro Relatórios de Monitoramento

| Cenário | Diagnóstico | Quantidade Afetada | Conduta Recomendada |
| :--- | :--- | :---: | :--- |
| **Lote Normal** | Registro coerente; 24 resultados disponíveis | 0 | Continuar reunindo evidências |
| **Observação Atrasada** | O prazo venceu, mas falta o resultado | 1 | Investigar a entrada dos dados |
| **Probabilidade Alterada** | Tabela e resposta registrada divergem | 1 | Recuperar a integridade do registro |
| **Avaliação Desaparecida** | Uma emissão ficou sem registro de avaliação | 1 | Investigar a conciliação |

---

## 3. Justificativa da Prioridade dos Incidentes

1. **Prioridade Alta — Probabilidade Alterada (`probabilidade_alterada`):**
   * *Nível:* Crítico.
   * *Motivo:* Divergência de integridade entre a predição da tabela e a resposta salva no histórico. Compromete a auditabilidade e indica falha de consistência no banco. Exige imediata recuperação da integridade do registro.

2. **Prioridade Média — Avaliação Desaparecida (`avaliacao_desaparecida`):**
   * *Nível:* Risco de Rastreabilidade.
   * *Motivo:* Uma emissão existente não possui o registro de avaliação correspondente, impedindo o cálculo preciso da cobertura de SLAs/SLOs. Exige investigação na rotina de conciliação.

3. **Prioridade Baixa/Operacional — Observação Atrasada (`observacao_atrasada`):**
   * *Nível:* Operacional Upstream.
   * *Motivo:* O prazo do horizonte de previsão venceu, mas o dado real de geração ainda não deu entrada no sistema. É um atraso temporário na ingestão de dados externos.

---

## 4. Por Que Nenhum Incidente Autoriza Retreinamento Automático

Nenhum dos quatro incidentes observados autoriza ou justifica o disparo de retreinamento automático pelas seguintes razões operacionais e estatísticas:

1. **Falhas de Pipeline de Dados $\neq$ Deterioração Preditiva:**
   Os incidentes apontados (`probabilidade_alterada`, `avaliacao_desaparecida`, `observacao_atrasada`) são anomalias de **engenharia de dados, sincronização e ingestão externa**. Tentar corrigir um erro de persistência ajustando os pesos do modelo geraria contaminação por ruído de infraestrutura.

2. **Insuficiência Amostral ($N = 24$):**
   Variações numéricas no Brier Score sob uma amostra pequena ($N = 24$) decorrem unicamente de flutuação amostral. Decisões de retreinamento exigem amostras estatisticamente representativas ($N \ge 168$) para comprovar *concept drift*.

3. **Governança e Proteção Operacional:**
   Disparar retreinamento sem causa preditiva comprovada viola a governança de modelos, podendo induzir *overfitting* a falhas atípicas de infraestrutura e degradar a calibração do sistema em produção.
