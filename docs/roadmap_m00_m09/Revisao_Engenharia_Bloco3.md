# Revisão técnica de engenharia — bloco 3

26/11/2026. Revisão por Codex, em passagem separada da produção dos resultados integrados. O agente revisor também implementou as contraprovas neurais desta rodada; a auditoria numérica do benchmark final foi reimplementada a partir dos arquivos salvos, sem carregar estimadores. Não é parecer humano externo, resposta independente do usuário ou certificação de autonomia pessoal. A integração no cadastro e a conferência dos portões pertencem ao agente principal.

**Parecer favorável ao aceite aplicado de 11 IDs, com sete IDs operacionais abertos.** O recorte abrange os 18 itens previstos; três dos sete abertos possuem aceite técnico local parcial. Assim, há 14 entregas técnicas demonstradas em algum alcance, sem interpretar 14 como quantidade de IDs integralmente encerrados.

| Alcance recomendado | IDs |
| --- | --- |
| Engenharia integral no recorte declarado — 11 | M03-04, M05-04, M05-05, M06-03, M07-01, M07-02, M07-03, M08-02, M08-03, M09-02, M09-04 |
| Operação aberta, com demonstração local parcial — 3 | M06-06, M06-07, M06-08 |
| Operação aberta, com preparação/replay/pacote — 4 | M06-02, M06-04, M06-05, M06-09 |

O Model Registry M06-03 tem aceite do mecanismo local delimitado. As versões 1 e 2 contêm o mesmo artefato; a sequência 1→2→1 exercita empacotamento/resolução/rollback, sem afirmar melhoria de modelo ou Registry remoto. M06-06/07/08 preservam os requisitos do ambiente e da operação reais. Não se recomenda apagar critérios, transferi-los para outro ID ou trocar dependências para fazer passar um portão.

## Evidência conferida

O auditor [auditar_bloco3.py](../../scripts/auditar_bloco3.py) lê apenas arquivos locais e grava seu próprio recibo. Não importa joblib, torch, notebooks produtores ou serviços; não treina, não executa modelos e não repete os testes antigos. O resultado corrente é [auditoria_bloco3.json](../../reports/fechamento_m00_m09/bloco3_engenharia/auditoria_bloco3.json), com sete grupos aprovados e retorno 0.

Foram conferidas 172 referências de hashes nos oito manifestos dos agentes: neural, quatro pastas de dados/modelo global, operação local, código/documentação operacional e pacote CI. Há referências repetidas entre manifestos; 172 não significa 172 arquivos distintos. Os 29 arquivos do selo integrado também foram conferidos, além dos hashes encadeados dos recibos, fontes e saídas. Não foi alterado nenhum arquivo produtor, estimador, checkpoint, calibrador, política ou código congelado.

Os protocolos dos 18 itens existem e precedem os timestamps de produção registrados. Os quatro protocolos de dados e os três de transferência neural mantêm os hashes de código previstos. O selo integrado foi gravado às **16:10:57,439880 UTC**; o recibo do novo snapshot registra obtenção às **16:11:00,888494 UTC**. A cadeia aponta para o mesmo SHA-256 do selo e para os brutos/filtrados atuais. São relógios e recibos locais, sem certificação temporal externa; o snapshot recém-obtido é retrospectivo e não prova disponibilidade histórica na origem.

## Recomputação do benchmark final

A auditoria reconstruiu diretamente do Parquet filtrado as 720 referências horárias e as 671 origens comuns. Conferiu os alvos em origem+24h, fim do histórico em origem−2h, disponibilidade do alvo em origem+26h e as 24 entradas cronológicas origem−25h..origem−2h. O arquivo de contexto coincide com esses valores. Cada um dos 14 métodos possui exatamente as mesmas 671 chaves e alvos, totalizando **9.394 linhas de previsões**.

MAE, RMSE e viés observado−previsto foram recalculados para os 14 métodos e confrontados com CSV e resultados JSON dos dois IDs. A previsão Chronos preserva shape `[671,9,26]`, os nove níveis de 0,1 a 0,9 e P50 extraído em `[:,4,25]`. O índice 25 representa o 26º passo depois do fim do histórico, conforme a diferença entre os relógios. As seis sementes MLP/GRU permanecem na comparação.

Persistência teve MAE **35,616479**; Chronos P50, **35,689509**; HGB do bloco 2, **40,160344** MWmed. A recomputação dos blocos circulares pareados de 24 horas, 2.000 réplicas e semente 31 reproduziu os 14 intervalos e ganhos. O candidato HGB perdeu em média **4,543865** MWmed para a persistência; IC condicional 95% **[−10,208299; 1,388840]**. Para Chronos, o ganho foi **−0,073030**, IC **[−3,151100; 2,969704]**. Os intervalos não refazem seleção ou ajuste, não são p-valores e não demonstram generalização para outro regime.

Os três conjuntos de intervalos foram recalculados, incluindo cobertura, largura, score e pinball. Não houve cruzamento entre P10/P50/P90 nas saídas avaliadas. O CQR congelado deu cobertura de **76,15%**, porém largura **135,212583** MWmed, superior ao limite de 100. Chronos cobriu **67,51%**, abaixo de 80%. Não se recomenda recalibrar este teste já examinado para mudar seu aceite.

Os 48 cenários de perda pontual foram reproduzidos para 16 ações e três razões de custos. P80 e P20 são ações quantílicas fixadas no código congelado; o menor custo observado posteriormente não autoriza selecionar uma semente ou outra ação pelo teste. O relatório principal preserva essa separação e a unidade de custo relativa, sem convertê-la em cobrança financeira.

## Classe, política e limites operacionais

O evento foi conferido como `último observado − alvo >= 22,77`, entre extremidades separadas por **26 horas**. Não é a rampa horária estudada em outro item. Brier, log loss e average precision foram recalculados das probabilidades salvas, sem usar bibliotecas de modelos. Platt melhora o Brier bruto, mas o baseline constante continua melhor nesse mês.

A política foi reconstruída cronologicamente com limiar congelado e orçamento diário. As colunas de alarme coincidem com o cálculo; o máximo foi **seis por dia**. TP/FP/FN/TN e custos também coincidem. A política calibrada tem custo relativo **574**, contra **724** de nunca alarmar, mas essa vantagem não satisfaz os critérios de ganho MAE, largura do intervalo e contrato operacional. As decisões booleanas do resultado são reproduzidas pela auditoria e mantêm promoção não autorizada.

Os recibos operacionais conservam zero emissões/horas live, continuidade não comprovada, resposta de drift ao vivo não demonstrada e cloud não implantada. Foram verificados os recibos das oito contraprovas HTTP, serviço encerrado e 480 requisições com SLOs locais atendidos. Isso sustenta os aceites técnicos locais, sem homologar TLS/RBAC/exposição pública, custo de produção ou sustentação.

## Falhas preservadas e recuperação

A execução integrada original terminou com retorno **1** ao imprimir stdout do filho Chronos num console CP1252. O NPZ e a metadata já estavam gravados. O recibo de recuperação liga seus hashes à execução original e registra somente a síntese UTF-8 com retorno **0**; o código congelado permaneceu igual. A auditoria não converteu o retorno 1 original em execução completa bem-sucedida, nem atribuiu timestamp de processo ao horário de modificação do arquivo.

No CI local, o primeiro pacote omitiu a dependência transitiva `m08_gru_autoral.py`; o log com 15 testes aprovados e um erro foi preservado. O adendo precede a nova cópia de 14 arquivos. Nessa cópia, o contrato correto retornou 0, a contraprova retornou 1 pelo motivo esperado e os **16 testes** retornaram 0. Os bytes da cópia coincidem com seu manifesto. Isso usa o Conda existente, não um ambiente GitHub novo. O bloqueio de publicação está documentado; não houve execução remota que possa ser usada para validar M06-02.

A falha inicial do MLflow e o adendo de compatibilidade também permanecem em disco. A segunda execução criou o Registry local e registrou paridade zero nas três resoluções do alias. As versões são do mesmo pacote, conforme explicitado no relatório principal.

A primeira passagem deste auditor manteve por engano float32 ao calcular a média da largura Chronos, enquanto o produtor faz a conta em float64. A diferença foi 4,09×10⁻⁷ MWmed. O recibo `auditoria_independente_tentativa1.json` conserva essa passagem não aprovada. Foi corrigido apenas o auditor para usar a aritmética declarada, sem afrouxar a tolerância e sem tocar os produtores. As passagens posteriores reproduziram os números.

## Decisão da revisão

Os documentos [Relatorio_Engenharia_Bloco3.md](Relatorio_Engenharia_Bloco3.md), [Bloco_3_Execucao.md](Bloco_3_Execucao.md), os relatórios dos agentes e as saídas conferidas sustentam a entrega de engenharia delimitada. A decisão negativa dos candidatos no teste final é evidência técnica, não motivo para refazer treinos aceitos ou esconder resultados.

O cadastro deve preservar os 45 IDs e os históricos, registrar as 11 conclusões aplicadas e manter os sete IDs operacionais do bloco 3 abertos, além dos quatro bloqueios M04 anteriores. O verificador documental deve ser executado após a atualização; esta revisão não substitui seu resultado nem afirma que a atualização já ocorreu. O portão operacional deve continuar recusando encerramento enquanto faltarem as comprovações externas. Não houve certificação pessoal, implantação ou aprovação automática de produção.
