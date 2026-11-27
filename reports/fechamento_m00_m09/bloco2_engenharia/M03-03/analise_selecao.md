# Interpretação da seleção de atributos

Codex — 25/11/2026. Análise das saídas do novo ajuste local, fornecida integralmente; não é resposta independente do usuário. Este texto não altera o protocolo nem a escolha congelada.

A escolha responde a uma pergunta delimitada: qual dos oito conjuntos previamente definidos tem menor desvio absoluto em MW nas mesmas 504 origens de junho, sob previsão h24 e história encerrada duas horas antes da origem? Ela não estabelece uma lista universal de atributos importantes nem garante menor erro em outubro ou em outra usina.

| Candidato | Features | MAE MW | RMSE MW | Viés MW |
| --- | ---: | ---: | ---: | ---: |
| HGB com 24 lags e calendário | 28 | 29,537623 | 38,939629 | −7,048328 |
| Ridge com 24 lags | 24 | 30,304103 | 39,749284 | −5,672242 |
| HGB com todos os grupos | 33 | 30,461331 | 40,052329 | −7,190257 |
| HGB com 24 lags | 24 | 30,721118 | 40,414456 | −6,210758 |
| HGB com 24 lags e estatísticas | 29 | 30,737428 | 40,349978 | −6,499773 |
| HGB com 6 lags recentes | 6 | 34,051992 | 44,634506 | −8,857041 |
| Persistência disponível | 1 | 37,908555 | 51,606516 | 0,643239 |
| HGB com estatísticas | 5 | 39,329777 | 49,034930 | −6,345130 |

O vencedor reduz a MAE de desenvolvimento em 8,370932 MW frente à persistência, cerca de 22,08%. A diferença frente à Ridge é menor: 0,766480 MW. Estes são contrastes descritivos dentro do desenvolvimento usado para selecionar o vencedor; não são uma prova independente do ganho nem um intervalo de confiança para generalização. Não se ajustou a regra após ver os contrastes.

O calendário ajuda no candidato comparável com 24 lags: a MAE passa de 30,721118 para 29,537623 MW. Acrescentar também as estatísticas resulta em 30,461331 MW. As estatísticas resumem informação já contida nos lags e não demonstraram benefício adicional neste orçamento e recorte. O candidato com apenas estatísticas teve MAE maior que a persistência; este resultado negativo foi conservado. Essas comparações são entre modelos novamente ajustados e incluem efeitos de parametrização/interações, não efeitos causais isolados dos atributos.

A importância de agregar os folds aparece nos próprios resultados: o melhor candidato da primeira semana foi HGB com todos os grupos; o da segunda, Ridge; o da terceira, HGB com lags e estatísticas. O candidato vencedor agregado não foi o melhor individual em nenhuma semana. A regra fixada evita escolher a semana mais favorável. Cada uma tem 168 origens; a MAE agregada coincide com a média das três MAEs porque os tamanhos são iguais. A RMSE agregada é calculada pela raiz da média ponderada dos erros quadráticos, não pela média simples das RMSEs.

O viés é previsão menos observado. Seu valor negativo em todos os aprendidos indica subestimação média nas semanas examinadas. A persistência tem menor viés absoluto, mas maior MAE e RMSE: compensar erros positivos e negativos não torna suas previsões individualmente próximas dos valores reais. Para custos assimétricos ou alarmes, é preciso explicitar outra perda/regra; o estudo de eventos do bloco faz isso separadamente.

O tempo registrado soma ajuste e previsão das três rodadas locais: cerca de 0,63 s para o vencedor, 0,19 s para Ridge e 0,007 s para persistência, depois da importação das bibliotecas. O mesmo processo usou duas threads. Isso descreve o ensaio no computador atual, inclui efeitos de aquecimento e não é benchmark de serviço, latência p95, capacidade ou custo financeiro. O receipt registra o tempo total e as versões; não se inferiu prontidão operacional.

O artefato final usa 7.221 linhas com rótulos disponíveis antes de 01/07/2026; a última origem elegível é 29/06 às 21h, cujo alvo está disponível em 30/06 às 23h. Ao contrário de um corte só por origem, a purga também impede usar as últimas 26 horas de rótulos ainda indisponíveis no corte. O ajuste e o scaler seguem a disponibilidade, e o período de outubro permanece reservado à aplicação posterior do artefato congelado.

Outubro é posterior aos períodos de treino e calibração no eixo da série. O protocolo real foi escrito em novembro: portanto a avaliação é retrospectiva em um snapshot novo, reservado e não examinado antes do congelamento, e não uma coleta prospectiva ou operação shadow.

## Resultado após a abertura autorizada

A inferência única de outubro foi executada em 25/11/2026 às 19:55:10 UTC, nas 695 origens predefinidas, sem ajuste ou nova escolha. A MAE do HGB foi 19,520624 MW e a da persistência 19,218456 MW: o ganho de desenvolvimento não se transferiu para a métrica primária neste recorte. O HGB perdeu 0,302168 MW, cerca de 1,57%. A RMSE melhorou, de 31,732297 para 24,989582 MW; isso sugere menor penalização por erros grandes nesse conjunto, mas não permite mudar a regra de seleção para uma métrica favorável após o teste.

O resultado negativo é parte da evidência de engenharia. Ele impede concluir superioridade por MAE e não autoriza promover o HGB. O artefato selecionado continua preservado, pois selecionar de novo com outubro transformaria o teste em desenvolvimento. O snapshot agora examinado não pode ser chamado de intocado em trabalhos posteriores. O receipt separado registra o hash do arquivo de avaliação, do modelo aplicado e das previsões, mantendo o receipt de ajuste anterior.
