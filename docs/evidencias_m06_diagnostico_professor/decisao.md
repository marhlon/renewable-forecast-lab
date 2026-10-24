# Diagnóstico do exercício HTTP

Execução: `1c51054df97b439fa22c7d2dcc9f6edd`.

Prioridade: falhas 5xx na fase `incident`. Taxa 10.00%, acima do limite didático de 1.00%.

- `2edffe09155646bfbb27d5e43ecaf82f`: HTTP 500; 0.4430 ms; fault_injection=error; error_type=não registrado.
- `4fb0af4d1177493a9c1472605e844cb9`: HTTP 500; 0.7331 ms; fault_injection=error; error_type=não registrado.

Causa registrada: injeção intencional de resposta HTTP 500 pelo laboratório. O código do exercício produz essa resposta antes de executar o estimador. Não há evidência aqui de exceção não tratada. A ação é registrar a detecção da falha controlada; em uma restauração real, confirmar o comportamento após retirar a injeção. A fase normal é a referência anterior, não uma medição posterior de recuperação.

Latência também ultrapassou a regra didática:

- `incident`: P95 dos sucessos=800.741300 ms; 3 sucessos acima de 250 ms.
  IDs: `5470d8836e8d44dc8a8f34875fc87da5`, `67affebb8ac84578812e0617f94a5a5f`, `40d7e3190df2496b89d0579d41229cd3`.
  Os atrasos têm marcação de injeção `slow`. Esses registros não justificam atribuir o atraso a E/S ou ao modelo.

## Denominadores e alcance

Quando uma fase contém somente rejeições, sem 2xx nem 5xx, a taxa 5xx é 0/0 e fica indefinida. Sem sucessos, mediana e P95 de sucesso também ficam indefinidos. Zero significaria uma medição que não ocorreu.

Foram avaliadas 45 chamadas, com 38 sucessos e 1 valor(es) distinto(s) de probabilidade nesses sucessos. As chamadas medidas compartilham as identidades de modelo e política verificadas no manifesto.

O exercício repete um pedido histórico. Probabilidades iguais demonstram repetibilidade neste pedido; não demonstram acurácia ou calibração. Falhas HTTP e atrasos não constituem evidência para retreinar o modelo. Não há novos rótulos nem medição de drift nesta inspeção.

Esta medição é sequencial, local e com falhas controladas. Não estima uptime, capacidade sob concorrência ou um SLO operacional. Os hashes verificam consistência com o manifesto recebido; não são uma assinatura de autenticidade.
