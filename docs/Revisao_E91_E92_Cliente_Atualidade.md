# Aceite de autoria e execução — E91 e E92

14 de outubro de 2026 · revisão do material fornecido por Marlon Alves Bomfim

## E91 — cliente Windows 1.0 e lançador

O anexo `Texto colado(8).txt` informa build `20261014T182138Z_d3f59ba1`,
execuções externas `20261014T182236Z_99227dfc` e `20261014T193054Z_58a9fdc4`,
HTTP 200/422, recusa de identidade divergente, indisponibilidade e diferença zero.
Esse mesmo anexo documenta a falha inicial de parâmetros PowerShell sem espaços.

Após a correção, os dois recibos colados pelo aluno registram:

| Instante da consulta UTC | HTTP | Estado | Saída | Resposta |
| --- | --- | --- | --- | --- |
| 2026-10-14T21:38:31.921904+00:00 | 200 | no_alarm | 0 | p=0.20465385372296466 |
| 2026-10-14T21:38:57.036226+00:00 | ausente | unavailable | 3 | null |

Modelo `7ab0a5cbc45a47df62b3ce44166f090b0ab686481aa37872d25e7c6353a1e17d`;
política `309906646dabc7a998a05071982b56dfad1fda140b45383e7b5e3b02d41decb7`.
Executável frozen, diretório de trabalho TEMP, dois recibos com UUID distintos.
O ensaio manual registra Conda ativo no terminal; o protocolo anterior é a
evidência informada de execução do filho com ambiente limpo. Não confundir as provas.

**Aceite:** cliente e lançador funcionaram nos cenários apresentados, no mesmo PC.
Não foi demonstrada instalação em outro computador, operação atual, cloud ou SLA.
Os registros foram recebidos como texto; não se afirma auditoria independente dos
bytes de todos os arquivos de release/recibos do aluno.

## E92 — regra temporal autoral

O código recebido implementa as sete regras na ordem solicitada e devolve exatamente
allowed/state/age_seconds/reason. Os cinco resultados informados coincidem com o
contrato: historical_replay, target_elapsed, current, stale_origin e future_origin.
Idades respectivas: 6453480, 6453480, 3600, 10800 e -60 segundos.

Pontos demonstrados: validação de entrada, precedência de decisões, diferença entre
contextos histórico e operacional, relógio explícito e função sem dependência de I/O.
O parâmetro `max_age` modela a idade de apresentação, não a disponibilidade do alvo.

**Aceite:** regra autoral aprovada no contrato UTC tipado do exercício. A versão
promovida em E93 preserva as decisões e adiciona normalização UTC e tipos explícitos.
Isso evita erro de duração ao generalizar para zonas com mudança de offset.

O termo `operational` descreve o contexto solicitado para apresentação. A função
não avalia qualidade do modelo, meteorologia, calibração ou autorização de operação.

## Próximo resultado verificável

Cliente 1.1 com a regra integrada: pedido antigo válido deve produzir HTTP 200 e
saída 7 no contexto operacional, com `response=null` e evidência em `audit_response`.
A reprodução histórica do mesmo pedido deve continuar permitida e identificada.
Nenhum novo treino ou benchmark de concorrência é necessário.
