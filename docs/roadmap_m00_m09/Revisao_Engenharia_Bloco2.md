# Revisão técnica de engenharia — bloco 2

25/11/2026 · etapas 4–6 · M02-06, M02-07, M02-08, M03-01, M03-02, M03-03, M05-01, M05-02 e M05-03.

**Decisão: aprovada a entrega aplicada para registro no portão `engenharia`.** A revisão encontrou os nove conjuntos de protocolo, resultado e parecer, preservação dos artefatos congelados, avaliação segregada e interpretação explícita dos resultados desfavoráveis. O aceite é da construção, execução, conferência e análise. Os resultados não sustentam a promoção automática dos modelos ou da política estudada.

Responsável por esta conferência: Codex, agente de auditoria do bloco 2. M03 e M05 foram implementados e executados por outros agentes da mesma sessão; este agente revisou os artefatos em leitura e reconciliou cálculos. Na parte M02-07/08, este agente também finalizou documentação e auditoria das execuções anteriores preservadas. Portanto, não se atribui independência humana a esta revisão nem autoria independente ao usuário. A integração final e o cadastro cabem ao agente principal.

## Evidência objetiva da revisão

O [auditor dos artefatos](../../reports/fechamento_m00_m09/bloco2_engenharia/auditoria_artefatos.json) terminou em 25/11/2026, **20:02:02 UTC**, com `valid: true`, exit code **0**, **798 verificações**, **172 declarações de SHA-256 conferidas** e **43 documentos JSON lidos**, sem erro. O SHA-256 desse relatório é `c7295e2d426aa1cec6ac54cf84487e08b16a3108f16934591d8eb0a4f6f384c1`.

O [script da auditoria](../../scripts/auditar_entrega_bloco2.py) não carrega `.joblib`, não treina, não aplica estimadores e não sorteia novas réplicas. Ele lê recibos, bytes e CSVs. Foram conferidos:

- presença e conteúdo dos protocolos, resultados e pareceres dos nove IDs;
- hashes de fontes, códigos, protocolos, bundles tratados como bytes, políticas, recibos, saídas e documentação declarada;
- precedência dos protocolos e congelamentos, comandos registrados e códigos zero das execuções;
- grade exata das 695 origens de outubro, não apenas contagem de linhas; h+24, histórico até origem−2h e disponibilidade da rampa em origem+3h;
- MAE pontual e, por período, cobertura, largura, interval score, pinball, Brier, prevalência, matrizes/custos de alarmes e MAE/RMSE/viés de rampa;
- execução causal da política com os primeiros seis elegíveis do dia e o limiar congelado, sem consultar escores futuros do mesmo dia;
- publicação dos três blocos 6/24/48h do bootstrap M02 e parâmetros prévios do bootstrap de cobertura M05, sem repetir seus sorteios.

O `--self-test` do auditor terminou com exit code 0 e oito contraprovas aprovadas. Ele rejeita JSON com chave repetida, timestamp de execução sem offset, travessia de caminho, hash adulterado, falsa aprovação operacional e uma tabela de 695 linhas contendo hora duplicada e outra ausente. Também confere os formatos UTC explícitos e a leitura correta do esquema `path`/`sha256`. Esses casos exercitam a auditoria; não foram apresentados como novos testes dos modelos ou nova execução dos 59 testes M02-05.

Comando efetivamente executado para esta evidência final:

```powershell
& 'C:\Users\marhl\miniconda3\envs\renewable-forecast\python.exe' scripts\auditar_entrega_bloco2.py --freeze reports\fechamento_m00_m09\bloco2_engenharia\congelamento_avaliacao.json --download-receipt reports\fechamento_m00_m09\bloco2_engenharia\dados_avaliacao\fonte.json --output reports\fechamento_m00_m09\bloco2_engenharia\auditoria_artefatos.json
```

Os comandos M03 de avaliação estão documentados no recibo original e em um adendo posterior que registra a chamada real e o código zero observado, identificando expressamente quando foi escrito. O adendo não é uma execução nova nem inventa horários externos a partir dos horários internos do programa.

## Separação temporal e identidade da fonte

Os 29 arquivos do [selo integrado](../../reports/fechamento_m00_m09/bloco2_engenharia/congelamento_avaliacao.json) coincidem com seus hashes. O selo foi criado em **19:27:20.852938 UTC**; o bruto foi recebido em **19:54:23.765913 UTC** e o recorte foi extraído em **19:54:25.018459 UTC**. As avaliações começaram depois da extração. O recibo não contém o instante inicial de cada requisição HTTP; a revisão não o inventa. A ordem é corroborada pelos horários persistidos, pelos hashes e pelo código congelado que exige e verifica o selo antes da rede.

O arquivo bruto tem 4.629.118 bytes. O recorte de CJU_BA5EIGT contém 744 horas de outubro e tem SHA-256 `aecb3a89ff306b93fa694d800b9659aa7d4d551763930589b5abad70931a87ab`. Todos os quatro estudos novos usam as mesmas 695 origens. Os artefatos permitem distinguir ajuste antes de julho, calibração de 312 origens, seleção de política de 360 origens e avaliação reservada de outubro. Nenhum dado de outubro entrou na seleção, no calibrador ou na política registrados.

Outubro é posterior aos cortes de desenvolvimento e ajuste, mas anterior ao congelamento real de novembro. O estudo é **retrospectivo em um snapshot recém-obtido e reservado nesta rodada**. O `Last-Modified` do objeto recebido é de novembro: os bytes não comprovam quais valores estavam publicados em cada origem histórica. Fuso físico, semântica do intervalo ONS, latência e cadastro operacional continuam limitados. Isso impede apresentar o estudo como coleta prospectiva, shadow ao vivo ou fonte operacional point-in-time comprovada.

## Resultados que limitam a decisão

| Entrega | Constatação revista | Consequência |
| --- | --- | --- |
| M02-06 | Com custos relativos de subestimação 4:1, P80 tem perda histórica 58,740425 e menor custo que P50, embora tenha MAE maior. O estudo de eventos tem outra coorte. | A ação depende da perda e do custo; valores hipotéticos não são moeda nem justificativa operacional. |
| M02-08 / M02-07 | h+24: ganho 9,3841 MWmed contra HGB história, mas apenas 0,5963 contra persistência, com os três ICs deste último incluindo zero. h+6: ganhos agregados de 6,2904 e 33,8080, com heterogeneidade semanal. | A referência muda a pergunta. ICs condicionais não corrigem seleção histórica, e a fração bootstrap ≤0 não é p-valor. |
| M03-01 / M03-03 | O HGB selecionado em junho tem MAE de outubro 19,520624, contra 19,218456 da persistência; piora de 0,302168 MWmed. Seu RMSE é menor, 24,989582 contra 31,732297. | A seleção não se confirmou na métrica primária. Não trocar o objetivo para RMSE depois do teste nem refazer a escolha usando outubro. |
| M03-02 | Aditividade local com resíduo máximo 7,11×10⁻¹⁵ MWmed; mudar o fundo altera contribuições em até 19,782388 MWmed. | A exatidão é do jogo de Shapley escolhido. Sensibilidade, dependência dos grupos e linhas híbridas impedem interpretação causal física. |
| M05-01 | Cobertura bruta 97,6978%, CQR 98,7050%, para nominal de 80%; larguras 72,920623 e 103,168575 MWmed. CQR piora interval score e pinball no recorte. | A calibração nominal não se manteve. Alerta agregado e nas quatro semanas completas; a parte final de 23 origens não atende ao mínimo de 48 para alerta. Não recalibrar outubro. |
| M05-02 | Platt melhora Brier agregado para 0,083296, contra 0,085677 bruto, mas uma semana completa piora. Política congelada em 0,3 custa 354; o comparador calibrado em 0,5 custa 308. | Melhoria de probabilidade não garante a melhor decisão. Preservar a política original e a comparação desfavorável, com teto causal de seis por dia demonstrado no replay. |
| M05-03 | MAE de rampa 6,974245 contra 7,572565 da rampa zero; no corte 0,5, o classificador detecta 0 dos 39 eventos horários. | Erro médio e ranking não validam detecção de extremos. Não baixar o corte no mesmo teste para obter acertos. |

O [relatório integrado](Relatorio_Engenharia_Bloco2.md), o [guia de execução](Bloco_2_Execucao.md), os pareceres M05 e o model card foram lidos. Os números, unidades, sinais de viés, custos, resultados negativos e limites de disponibilidade estão coerentes com os CSVs e recibos. O viés M03 é previsão−observado; o da regressão de rampa é observado−previsto, conforme os rótulos publicados.

## Cadastro e portões

Esta revisão aprova a migração proposta das nove entregas para `engenharia`, preservando os **45 IDs**, o snapshot integral anterior e os critérios/estados históricos em cada item. Foi encontrado e corrigido no registrador, antes de sua aplicação, um compartilhamento de referências que alteraria os critérios históricos junto com os critérios atuais; a versão corrigida usa cópia profunda.

M05-01 e M05-02 não podem continuar com portão `operacao` e estado global `validado` a partir desta evidência retrospectiva. A migração preserva suas exigências prospectivas como **M06-05/C3 e C4**, explicitamente não atendidas, com origem M05 e dependências rastreáveis. O escopo de monitoramento contínuo de serviço e previsões de M06-05 comporta essas comprovações. Os bloqueios externos M04 e as demais exigências operacionais continuam abertos.

No momento da emissão desta revisão, a migração ainda será aplicada pelo agente principal. Após o registro, executar `python scripts/verificar_roadmap.py` e `python scripts/verificar_roadmap.py --bloco 2 --gate engenharia`. O auditor deve ser chamado com `--check-registry`, gravando **outro** relatório, `auditoria_cadastro.json`, para conferir os 45 IDs, igualdade do histórico embutido com o snapshot e as pendências M06-05/C3–C4. Não sobrescrever a auditoria de artefatos nem criar dependência circular de hashes.

A aprovação técnica desta entrega não é encerramento formativo independente, prova de continuidade, aprovação de produção, CI remoto ou autorização para implantar. Os resultados já examinados permanecem examinados, e os experimentos históricos aceitos permanecem preservados.
