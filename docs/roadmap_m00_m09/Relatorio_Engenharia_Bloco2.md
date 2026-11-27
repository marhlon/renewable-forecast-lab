# Bloco 2 — execução, resultados e decisão

25/11/2026 · Renewcast/P1 · etapas 4–6 · entrega de engenharia aplicada.

Foram construídas, executadas e analisadas nove entregas: M02-06, M02-07, M02-08, M03-01, M03-02, M03-03, M05-01, M05-02 e M05-03. O trabalho fornece as soluções completas. Não exige respostas ou provas do usuário, não certifica autonomia pessoal e não homologa operação. Os aceites e arquivos históricos foram preservados; os ajustes novos têm contrato e diretórios próprios.

O resultado principal é uma decisão delimitada: **a seleção no desenvolvimento não se confirmou na MAE de outubro; os intervalos ficaram excessivamente largos; a calibração de classe melhorou no agregado, mas a política escolhida não foi a de menor custo no teste; o detector horário não emitiu nenhum alarme para os 39 positivos**. Essas falhas estão preservadas. Executar corretamente um estudo inclui registrar quando a solução não atende à finalidade.

## 1. O que entrou e como o teste foi protegido

A fonte de geração é o [ONS — Geração por Usina em Base Horária](https://dados.ons.org.br/dataset/geracao-usina-2), série `CJU_BA5EIGT`, em MWmed. Nesta rodada os modelos novos usam somente geração passada e calendário. Não usam vento previsto, GFS, Open-Meteo, Chronos ou uma instalação nova de bibliotecas.

O arquivo antigo `dist/databricks/CJU_BA5EIGT/m07_3/geracao.parquet` contém 8.760 horas, de setembro/2025 a agosto/2026. Julho e agosto já haviam sido examinados em outros experimentos. Por isso agosto não foi apresentado como teste intocado. As previsões antigas foram reutilizadas para bootstrap e custo, sem refazer seus ajustes.

Para avaliar os modelos novos, foi predefinido outubro/2026, um arquivo ainda não obtido localmente na preparação. O protocolo foi gravado antes do ajuste. Os 29 arquivos de código, modelos, calibradores, política e protocolos foram selados com SHA-256 em **25/11 às 19:27:20 UTC**. O download terminou às **19:54:23 UTC**, e a extração foi validada às **19:54:25 UTC**. O primeiro acesso de avaliação registrado no M03 veio depois, às 19:55:10 UTC. A auditoria confere a ordem e os bytes.

O recurso oficial foi identificado por UUID `6edb2f1a-5772-44f1-8dad-6180b20bf130`; a API CKAN resolveu o endereço S3. Foram baixados 4.629.118 bytes, com 537.384 registros multiusina. O filtro explícito pelo identificador da usina produziu **744 horas únicas, finitas e alinhadas**, de 01/10 às 00h a 31/10 às 23h. Não houve agregação silenciosa de duplicatas, arredondamento de timestamps nem preenchimento de geração faltante com zero.

Depois de reservar o histórico necessário e os alvos h+24, restaram **695 origens comuns**, de 02/10 às 01h a 30/10 às 23h. O último alvo é 31/10 às 23h. As comparações pontual, de intervalos, de probabilidades e de rampas usam essas mesmas origens.

**Limite temporal:** outubro é posterior ao ajuste de julho, mas anterior ao congelamento real de novembro. Esta é uma avaliação retrospectiva em snapshot novo e segregado nesta rodada. O objeto S3 recebido registra `Last-Modified` de 25/11; ele não comprova a versão publicada disponível em cada origem de outubro. Também continuam sem comprovação o fuso físico, a semântica do intervalo ONS, a latência efetiva de publicação e as versões cadastrais. Interpretar os relógios como UTC e assumir atraso de duas horas são hipóteses de estudo.

Os detalhes estão em [protocolo integrado](../../reports/fechamento_m00_m09/bloco2_engenharia/protocolo_integrado.json), [selo](../../reports/fechamento_m00_m09/bloco2_engenharia/congelamento_avaliacao.json) e [recibo da fonte](../../reports/fechamento_m00_m09/bloco2_engenharia/dados_avaliacao/fonte.json). O bruto fica em `data/raw/bloco2_locked`, preservando os arquivos anteriores.

## 2. Etapa 4: bootstrap, perda e decisão

### Bootstrap horário pareado — M02-08 e M02-07

O bootstrap recuperado no bloco 1 foi efetivamente aplicado a previsões salvas. Foram quatro chamadas completas: h+24 e h+6, cada uma contra HGB histórico e persistência. Em cada horizonte há 504 previsões, distribuídas por três semanas de 168 horas. Não houve novo treinamento dos experimentos meteorológicos.

O estimando é o ganho médio de erro absoluto: `|erro_referência| − |erro_candidato|`. Valor positivo favorece história+vento. Reamostrar os mesmos índices de origem preserva o pareamento. Blocos circulares horários de 6, 24 e 48 horas foram fixados antes da análise; não se atravessam os folds. Foram 5.000 réplicas por configuração, semente 42. O agregado pondera pelo número de origens.

| Horizonte | Referência | Ganho médio — MWmed | IC percentil nominal 95%, bloco 24h |
| --- | --- | ---: | --- |
| h+24 | HGB histórico | 9,3841 | [5,2595; 13,6790] |
| h+24 | Persistência | 0,5963 | [−7,2504; 9,1035] |
| h+6 | HGB histórico | 6,2904 | [2,7851; 9,4984] |
| h+6 | Persistência | 33,8080 | [23,8023; 43,1542] |

Contra HGB histórico, o ganho agregado h+24 permanece positivo nos três tamanhos de bloco. Isso não demonstra superioridade sobre a persistência: contra ela os três intervalos agregados incluem zero. Em h+6 o agregado é favorável, mas algumas semanas são muito menos convincentes. A conclusão foi transferida para outro horizonte usando os números desse horizonte, sem copiar automaticamente o resultado de h+24.

Os intervalos são condicionais aos modelos, amostras e previsões preservados. Não incluem incerteza de novo ajuste, seleção de hiperparâmetros, regime futuro, revisão do ONS ou outras usinas. A fração de réplicas com ganho não positivo não é um p-valor. As réplicas individuais da CLI não foram persistidas: a auditoria reconcilia entradas, método testado, recibos e resumos, sem se apresentar como uma nova reprodução independente dos sorteios.

Foram conferidos 48 resumos, seus pareamentos, relógios e hashes. A recomputação dos ganhos/MAEs diferiu no máximo por 7,11×10⁻¹⁵ MWmed, compatível com precisão numérica. Os 59 testes de construção do bloco 1 foram verificados como evidência anterior; não foram anunciados como novamente executados. Veja [análise do bootstrap](Bloco_2_Bootstrap.md) e [auditoria estatística](../../reports/statistical_audit.md).

### Perdas assimétricas — M02-06

A clínica recebida foi localizada, copiada com os mesmos bytes e executada sobre as 168 origens históricas M09.3. Essa coorte já era conhecida e não é a coorte de outubro. Foram recalculadas 36 perdas, além de 66 linhas de custo FP/FN em uma segunda coorte de 504 origens e 113 eventos. As duas coortes não foram misturadas.

| Custo relativo | Menor custo observado nas 168 origens | Perda média |
| --- | --- | ---: |
| Subestimar e superestimar custam igualmente | Chronos P50 | 31,340738 |
| Subestimar custa quatro vezes mais | Chronos P80 | 58,740425 |
| Superestimar custa quatro vezes mais | Chronos P20 | 54,573165 |

Sob perda linear assimétrica, o quantil decisório é `c_sub/(c_sub+c_super)`. Assim 4:1 aponta para P80 e 1:4 para P20. O P80 teve MAE de 39,016937, pior que o P50, mas menor custo quando subestimar custa quatro vezes mais. Os valores são perdas nas unidades/razões hipotéticas do cenário, sem conversão para reais ou receita operacional.

No estudo separado de classificação, baixar o corte HGB de 0,5 para 0,2 reduziu o custo FP1/FN4 de 191 para 158, mas aumentou os alarmes de 109 para 156 e ultrapassou o teto histórico de 120. Essa regra não foi promovida. Três quantis não identificam toda a distribuição nem a probabilidade exata de uma queda arbitrária; para isso foi treinado e calibrado um classificador separado na etapa 6. Veja [decisão e risco](Bloco_2_Decisao_Risco.md).

## 3. Etapa 5: modelos, atributos e explicação local

### Seleção temporal — M03-01 e M03-03

O contrato novo prevê `y(origem+24h)` com histórico disponível até `origem−2h`. As 24 defasagens vão de `origem−2h` a `origem−25h`. Foram preparados cinco resumos (média/desvio de 6 e 24 horas e diferença entre as duas últimas observações) e quatro coordenadas cíclicas de hora/dia da semana. O universo tem 33 atributos.

Oito candidatos foram fixados antes do ajuste: persistência, Ridge com 24 lags e seis combinações HGB por grupos. Todos usam a mesma coorte completa. Não se trata de busca exaustiva de todos os subconjuntos dos 33 atributos, nem de seleção individual completa entre atributos meteorológicos.

As validações são 01–08, 08–15 e 15–22 de junho, 168 origens por fold, com ajuste expansivo. Como o alvo só fica disponível em `origem+26h`, são removidas do ajuste todas as linhas cuja disponibilidade é maior ou igual ao começo da validação. O StandardScaler da Ridge é ajustado somente no treino de cada fold. A seleção usa MAE agregada das 504 origens; quantidade de atributos e ordem fixa resolvem empates.

| Candidato | Atributos | MAE no desenvolvimento — MWmed |
| --- | ---: | ---: |
| HGB — 24 lags + calendário | 28 | 29,537623 |
| Ridge — 24 lags | 24 | 30,304103 |
| HGB — todos | 33 | 30,461331 |
| HGB — 24 lags | 24 | 30,721118 |
| HGB — 24 lags + resumos | 29 | 30,737428 |
| HGB — 6 lags | 6 | 34,051992 |
| Persistência | 1 | 37,908555 |
| HGB — resumos | 5 | 39,329777 |

Foi selecionado o HGB com 28 atributos. Seu ajuste final usa **7.221 linhas**, com disponibilidade de rótulo estritamente anterior a 01/07; a última é 30/06 às 23h. Hiperparâmetros fixos: 60 iterações, 15 folhas, mínimo de 20 linhas por folha, taxa 0,05, L2 0,1, sem early stopping e semente 17. A persistência usa o último valor disponível, sem ajuste.

O desempenho reservado mudou a decisão:

| Modelo congelado | MAE outubro | RMSE outubro | Viés: previsão − observado |
| --- | ---: | ---: | ---: |
| Persistência | **19,218456** | 31,732297 | +0,732986 |
| HGB — 24 lags + calendário | 19,520624 | **24,989582** | +1,054634 |

O HGB perdeu 0,302168 MWmed, aproximadamente 1,57%, na métrica primária, embora reduzisse o RMSE em aproximadamente 21,25%. Isso é compatível com redução de erros grandes sem melhorar a média absoluta. São 695 origens correlacionadas de uma série e um mês; a diferença de MAE não estabelece superioridade geral da persistência. A seleção de junho não foi refeita com outubro. Para o objetivo MAE, os resultados não sustentam promover automaticamente o HGB. O [model card](../model_card.md) registra uso, features, cortes, métricas e limites.

### Explicação local — M03-02

Foi implementado Shapley interventional exato por grupos, sem instalar a biblioteca SHAP. Para o modelo selecionado há três grupos ativos: 6 lags recentes, 18 lags anteriores e calendário. Oito coalizões cobrem todas as combinações. Em cada coalizão, os grupos presentes vêm do exemplo e os ausentes vêm de linhas do treino; a média das previsões define o valor do jogo.

As seis origens de julho, todas às 12h, e os fundos de 16 e 8 observações elegíveis foram fixados previamente. O teste analítico linear verifica os valores; a soma `base + contribuições` reproduz a previsão HGB com resíduo máximo de **7,11×10⁻¹⁵ MWmed**.

Trocar o fundo alterou contribuições em até **19,782388 MWmed**, sem inverter sinais nos 18 pares avaliados. Nenhuma inversão de sinal não significa pouca sensibilidade. Fixar todas as horas às 12h também limita a interpretação sobre outras horas. As combinações híbridas podem ser pouco representativas, pois lags são correlacionados. A soma exata é uma propriedade do jogo escolhido; não prova causalidade física, robustez a outro fundo nem contribuição individual de cada sensor/defasagem.

## 4. Etapa 6: intervalos, probabilidades e rampas

### Separação temporal comum

O ajuste termina antes de 01/07. A calibração usa **312 origens de 01/07 até 14/07 exclusivo**. A seleção da política usa outras **360 origens, de 16/07 até 31/07 exclusivo**. O último alvo da calibração fica disponível antes do primeiro instante de seleção; os alvos da seleção ficam conhecidos antes de 01/08 às 02h. Outubro não participa de ajuste, calibração ou escolha de limiar.

### Intervalos P10–P90 e CQR — M05-01

Três HGB quantílicos foram treinados separadamente. A ordenação P10≤P50≤P90 por linha foi predefinida. Na calibração, o escore CQR é `máximo(P10−y, y−P90, 0)`. O rank `ceil((312+1)×0,8)=251` resultou em expansão de **15,123976 MWmed por lado**. A cobertura de calibração foi de 70,19% para 80,45%.

| Intervalo congelado | Cobertura outubro | Largura média — MWmed | Interval score | Pinball médio |
| --- | ---: | ---: | ---: | ---: |
| P10–P90 ordenado | 97,6978% | 72,920623 | **76,989183** | **5,508005** |
| Com expansão CQR | 98,7050% | 103,168575 | 104,578288 | 6,427642 |

A meta nominal é 80%, com alerta previamente definido fora de 70%–90%. Ambos acionaram o alerta agregado e nas quatro semanas completas. O CQR acrescentou 30,247952 MWmed à largura total e piorou os escores nesse mês. Cobrir mais não torna o intervalo melhor quando a largura fica excessiva. A cobertura não se transferiu como calibração nominal estável.

As quatro semanas têm 168 origens cada; a última fração tem 23 e fica fora do alerta por tamanho mínimo de 48. O bootstrap circular pareado de 24h, 2.000 réplicas e semente 17, predefinido antes do download, deu IC percentil condicional de cobertura de **[94,82%; 99,86%]** no bruto e **[96,83%; 100%]** no CQR. O IC da diferença CQR−bruto foi [0,14; 2,30] pontos percentuais. Dependência, sazonalidade e mudança de regime impedem interpretar isso como garantia conformal ou operacional. Não foi diminuída a expansão para melhorar outubro.

### Probabilidade de classe e alarmes — M05-02

O evento antigo é `y(origem−2h) − y(origem+24h) ≥ 22,77 MWmed`: compara extremidades separadas por **26 horas**. Foi ajustado HGBClassifier e, no período separado, regressão logística sobre o logit da probabilidade — calibração Platt. A frequência positiva do treino serve de baseline.

| Probabilidade, 117 positivos/695 | Brier | Log loss | AP |
| --- | ---: | ---: | ---: |
| Frequência fixa do treino | 0,140752 | 0,455717 | 0,168345 |
| HGB bruto | 0,085677 | 0,250749 | 0,687644 |
| HGB + Platt | **0,083296** | **0,243630** | 0,687644 |

Brier e log loss menores favorecem Platt no agregado. A AP não mudou: a transformação logística é monotônica e preservou a ordenação. Na quarta semana o Brier calibrado piorou de 0,093479 para 0,105639; não há estabilidade uniforme. Bins de confiabilidade e amostras de cada faixa ficam no CSV, inclusive faixas vazias.

A política foi escolhida no desenvolvimento por custo FP=1/FN=4, entre cortes fixos e a alternativa sem alarme. O corte congelado foi **0,3**, com no máximo **seis alarmes por dia do relógio do laboratório**. O limitador aceita os primeiros seis elegíveis em ordem temporal e não consulta os próximos escores para decidir quais seriam os melhores do dia. Um teto observado no desenvolvimento, sozinho, não limitaria a execução futura; aqui o teto é imposto no runtime do replay.

| Comparação predefinida, todas com teto diário | Alarmes | TP | FP | FN | Custo FP+4FN |
| --- | ---: | ---: | ---: | ---: | ---: |
| Bruto em 0,5 | 115 | 45 | 70 | 72 | 358 |
| Calibrado em 0,5 | 55 | 43 | 12 | 74 | **308** |
| Política calibrada congelada em 0,3 | 126 | 48 | 78 | 69 | 354 |
| Frequência em 0,5 / sem alarme | 0 | 0 | 0 | 117 | 468 |

A regra congelada respeitou seis alarmes por dia, detectou 48 dos 117 positivos e reduziu o custo frente a nunca alarmar. O comparador 0,5 teve custo menor no teste. Esse achado é registrado, sem substituir retroativamente a política por 0,5. Precisão da política: 38,10%; recall: 41,03%. As taxas são por origem positiva, não por episódio físico. Não existe prova de que os custos hipotéticos representem a operação real.

### Rampa de uma hora — M05-03

Foi criado outro alvo: `rampa = y(origem) − y(origem+1h)`. Positivo significa queda; evento é rampa≥22,77 MWmed. Como a última observação permitida é origem−2h e o alvo final só chega com atraso assumido de 2h, o rótulo fica disponível em **origem+3h**. O treino próprio desse alvo tem 7.244 linhas. Os 28 atributos foram transferidos do estudo h+24 conforme o plano, sem nova seleção de features no teste.

| Previsão da magnitude da rampa | MAE — MWmed | RMSE — MWmed |
| --- | ---: | ---: |
| HGB de rampa | **6,974245** | **12,029621** |
| Rampa zero | 7,572565 | 14,543587 |
| Última rampa observada | 12,829047 | 21,037676 |

Houve **39 eventos horários em 695 origens**, prevalência de 5,61%, contra 117 positivos no contrato de 26h. O HGB horário teve AP=0,328758 e Brier=0,043731, melhores que a frequência do treino (AP=0,056115; Brier=0,053087). Entretanto, **no corte de probabilidade 0,5 não emitiu alarme algum e perdeu os 39 eventos**. A magnitude prevista pelo regressor também não passou de 22,77. Menor MAE e ranking útil não validam uma política de detecção. Não se baixou o limiar depois de ver esse silêncio.

## 5. O que foi imposto ao projeto

O cadastro preserva seus **45 IDs** e a cópia integral anterior à migração. Os nove itens desta rodada recebem aceite no portão `engenharia`, com critérios, entregáveis, hashes, parecer e responsável efetivos. Os critérios formativos antigos ficam no histórico, sem atribuir ao usuário uma defesa independente.

M05-01 e M05-02 tinham também requisitos operacionais. O estudo retrospectivo não os encerra: as exigências de estabilidade prospectiva de intervalos e probabilidades foram explicitamente preservadas como **M06-05/C3 e C4**, não atendidas, com dependências e origem registradas. Esse item continua no portão `operacao`. Assim não se duplica o backlog nem se torna produção aprovada por mudança de nome. Os quatro bloqueios externos M04 do bloco 1 também continuam abertos.

O README passa a apresentar o resultado desta rodada, inclusive as falhas. O roadmap diferencia a construção/avaliação local do que dependerá de operação real no bloco 3. Não houve commit, push, CI remoto, alteração de serviço em execução nem mudança dos modelos aceitos antigos.

## 6. Verificação e arquivos para abrir

| Arquivo novo | Responsabilidade |
| --- | --- |
| `notebooks/bloco2_modelagem_core.py` | Construir a grade sem esconder lacunas, gerar lags e relógios, filtrar treino pela disponibilidade estrita do alvo |
| `notebooks/selecao_atributos_temporal.py` | Protocolar candidatos, ajustar dentro dos cortes, selecionar e persistir o modelo; aplicar o artefato uma vez no mês reservado |
| `notebooks/explicacao_local.py` | Enumerar coalizões e calcular atribuições locais, base, previsão e sensibilidade ao fundo |
| `notebooks/bloco2_risco_core.py` | Calcular CQR, pinball, cobertura, Brier, confiabilidade, custos e orçamento causal de alarmes |
| `notebooks/bloco2_validacao_risco.py` | Separar ajuste, calibração, seleção de política e avaliação dos três estudos M05 |
| `scripts/obter_avaliacao_bloco2.py` | Selar arquivos antes da rede, resolver recurso ONS, baixar e filtrar o mês com contrato de 744 horas |
| `scripts/auditar_entrega_bloco2.py` | Conferir hashes, cronologia e coortes e recalcular métricas dos CSVs, sem novo treino/inferência |
| `scripts/registrar_bloco2.py` | Migrar o cadastro com cópia integral e critérios históricos, mantendo as exigências operacionais abertas |

Foram executados seis testes de contrato/explicação e oito testes de intervalos/probabilidades/capacidade. A revisão independente do código verificou purga, relógios, separação da calibração, regra causal de orçamento e ausência de ajuste na avaliação. O auditor documental tem oito contraprovas próprias, incluindo hora duplicada numa tabela de 695 linhas, hash adulterado e falsa alegação operacional. São evidências diferentes dos testes antigos do bootstrap.

Para conferir a entrega existente, sem repetir ajuste ou download:

```powershell
Set-Location C:\renewable-forecast-lab
conda activate renewable-forecast
python scripts/obter_avaliacao_bloco2.py verificar
python scripts/verificar_roadmap.py
python scripts/verificar_roadmap.py --bloco 2 --gate engenharia
python scripts/auditar_entrega_bloco2.py --freeze reports/fechamento_m00_m09/bloco2_engenharia/congelamento_avaliacao.json --download-receipt reports/fechamento_m00_m09/bloco2_engenharia/dados_avaliacao/fonte.json --check-registry
```

Os comandos de preparação/ajuste/avaliação e seus códigos de saída estão nos recibos de cada item. A proteção contra sobrescrita impede repetir automaticamente uma seleção ou teste já registrados. Uma nova experiência deve ter diretório e protocolo próprios. Brutos, Parquets derivados e bundles `.joblib` continuam locais conforme o `.gitignore`; código, parâmetros, identidades, CSVs, pareceres e recibos mantêm a trilha de auditoria. Clone sem esses arquivos precisa repor as entradas e reproduzir os artefatos; o verificador local não é uma promessa de CI em clone limpo.

Comece pelo [guia do bloco](Bloco_2_Execucao.md), pelo [model card](../model_card.md) e pelas pastas dos [nove resultados](../../reports/fechamento_m00_m09/bloco2_engenharia/). A [revisão integrada](Revisao_Engenharia_Bloco2.md) delimita o aceite. Nenhum aplicativo precisou ser aberto; a única intervenção de ambiente foi a permissão para baixar o arquivo público ONS. O bloco 3 permanece como próxima etapa planejada, sem iniciar sua execução nesta rodada.
