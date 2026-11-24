# M08.3 — revisão da execução Windows e da célula GRU recebida

Marlon A. Bomfim · 15/11/2026 · evidência E114

**Aceitos: execução técnica M08.3, implementação NumPy e os cinco testes apresentados.** A revisão não pede novo treinamento nem alteração na função. A interpretação final e a escolha defendida pelo aluno ainda não foram entregues como parecer; podem acompanhar a próxima unidade, sem reabrir a implementação aceita.

## O que foi efetivamente auditado

Execução do aluno `20261115T164955Z_5e435b09`, Windows/Python 3.12.13, PyTorch 2.7.1+cpu, NumPy 2.5.3, pandas 3.0.5 e scikit-learn 1.9.0.

Recebidos nove arquivos: resultado, protocolo, normalização, resumo, previsões, curvas, partições, origens incompletas e relatório HTML. Os oito arquivos que possuem hash dentro de `resultado.json` coincidem com seus hashes registrados, mesmo onde o upload renomeou o arquivo com um sufixo como `(6)` ou `(8)`. O próprio recibo é identificado pelo hash calculado nesta revisão.

As 1.512 linhas de previsões representam nove variantes nas mesmas 168 origens. Foram recalculados MAE, RMSE e viés de todas elas: **27 valores coincidentes**, tolerância absoluta de `1e-12`. As colunas de erro absoluto e quadrático também foram reconciliadas. Os alvos, as origens e a persistência foram conferidos, assim como as fronteiras temporais e os checkpoints declarados pelas curvas.

Divisão confirmada: 7.079 ajuste, 168 seleção, 168 avaliação; 52 exclusões por disponibilidade; 18 contextos iniciais incompletos. O último alvo do ajuste fica disponível antes da primeira origem da seleção; o mesmo vale entre seleção e avaliação. As médias/desvios recebidos são numericamente iguais aos da referência do professor. Os Parquets originais Windows não foram anexados: a igualdade desses normalizadores não prova identidade de todas as entradas.

Os quatro hashes de código declarados coincidem com o código distribuído. Os seis recarregamentos com diferença zero constam do recibo. Como os arquivos `.pt` Windows não foram recebidos, **esse recarregamento não foi reexecutado independentemente nesta revisão**. Não é necessário reenviar os pesos para o aceite técnico desta unidade.

## Revisão do seu código e dos testes

A célula aplica corretamente `x @ weight_ih.T`, `h @ weight_hh.T`, divisão dos blocos em r/z/n e atualização `(1-z)*n + z*h`. A porta reset atua sobre a transformação recorrente completa do candidato, incluindo seu viés, conforme a convenção do PyTorch.

| Teste apresentado | O que ele prova dentro do caso construído |
| --- | --- |
| Escalar com estado não nulo | Confere a direção da atualização: com z=0,75, n=−0,2 e h anterior=0,8, o novo estado é 0,55. |
| Portas neutras e entradas somente para leitura | Confere batch, múltiplas coordenadas, dtype e ausência de alteração nas entradas. |
| Reset depois da transformação com viés | Distingue duas fórmulas que parecem semelhantes, mas produzem estados diferentes. A matriz não diagonal e o viés não nulo tornam o teste relevante. |
| Sigmoide em ±1000 | Confere estabilidade na saturação, sem exponenciar números positivos grandes. |
| Dimensões e NaN | Rejeita casos incompatíveis antes de permitir broadcasting silencioso. |

**Resultado executado nesta revisão: cinco testes aprovados.** A função também passou nos onze grupos do verificador entregue: comparação NumPy/GRUCell em diferentes dimensões, sequência de 24 passos e contratos de estado/lotes/avaliação. A tolerância das comparações float64 com PyTorch foi `1e-12`.

Esta verificação executa a função transcrita da sua mensagem. O treinamento Windows usou `torch.nn.GRU`, como previsto; `authorship_sha256=null` no protocolo original indica que aquela execução não chamou a conferência da sua função NumPy. A conferência foi feita agora, separadamente, sem treinar novamente. O aceite da solução não é uma certificação de autoria independente.

## O que os resultados locais permitem decidir

Todos os valores abaixo são da execução Windows recebida, em MWmed:

| Método | MAE | RMSE | Viés observado − previsto |
| --- | ---: | ---: | ---: |
| Persistência d2 | 37,991646 | 55,434342 | −3,016872 |
| Linear 24h | 33,678664 | 44,938111 | +15,148681 |
| HGB 24h, s17 | **32,323956** | 44,221683 | +13,119039 |
| MLP s17 | 32,724828 | 44,019866 | +10,655947 |
| MLP s29 | 33,700811 | 44,892316 | +12,652757 |
| MLP s41 | 33,159788 | 44,069511 | +13,724280 |
| GRU s17 | 35,675970 | 45,200733 | +18,525120 |
| GRU s29 | 34,911227 | 43,816199 | +17,993098 |
| GRU s41 | 34,573202 | **43,066020** | +14,777710 |

A mediana dos MAEs é 33,159788 para MLP e 34,911227 para GRU. Essas medianas resumem três ajustes; não representam a previsão de um ensemble nem um intervalo de confiança. O HGB tem o menor MAE entre as variantes avaliadas. Seu ganho é 4,02% sobre o linear e 14,92% sobre a persistência neste recorte. São comparações descritivas, sem teste final novo ou demonstração de superioridade estatística em outras semanas.

Se o critério principal é MAE, o **HGB é a referência provisória mais forte entre os modelos testados aqui**. Isso não exige que a GRU vença para que a unidade esteja concluída tecnicamente. A representação recorrente e seu treinamento funcionaram; o ganho preditivo é outra questão.

### Por que a GRU 41 melhora RMSE e piora MAE?

Nos dados recebidos, a GRU 41 ganha em erro absoluto em 72 origens e perde em 96. Os ganhos somam 737,191910 MWmed em distâncias absolutas; as perdas somam 1.115,065267. O saldo de 377,873357 dividido por 168 explica o **MAE 2,249246 MWmed maior que o HGB**.

Ao elevar os erros ao quadrado, o saldo se inverte: a GRU reduz a soma quadrática em 16.947,028611 MWmed², ou o MSE em 100,875170 MWmed² por exemplo. Reduções em alguns erros grandes compensam outras perdas nesse critério.

| Origem | Real | HGB | GRU 41 | Erro absoluto HGB → GRU |
| --- | ---: | ---: | ---: | ---: |
| 03/07 04h | 182,0555 | 48,9966 | 73,3077 | 133,0589 → 108,7478 |
| 10/07 02h | 74,3265 | 169,8058 | 133,7653 | 95,4793 → 59,4388 |
| 04/07 08h | 115,0835 | 100,0692 | 65,7108 | 15,0143 → 49,3727 |

Os dois primeiros exemplos contribuem para a redução quadrática; o terceiro mostra uma perda importante. Os horários são os rótulos sem fuso físico validado do laboratório. A semente 41 é examinada por ser o exemplo do contraste entre métricas, não escolhida como campeã para uma operação.

Apenas ter MSE como função de treino não garante menor RMSE na avaliação: a GRU 17 perde nos dois critérios. A perda define o que o otimizador tenta reduzir no ajuste, enquanto a avaliação contém outras origens.

### Curvas, viés e custo

As melhores épocas e paradas coincidem com as curvas: MLP 8/16, 20/28, 15/23; GRU 23/31, 38/46, 24/32. Cada parada ocorreu após oito épocas sem melhora estrita. Para a GRU 29, entre a melhor época 38 e a parada 46, a perda do ajuste não melhora; portanto não se deve repetir automaticamente a explicação de sobreajuste usada nas MLPs. O recibo registra o checkpoint correto; a forma da curva não identifica sozinha a causa de cada oscilação.

O viés positivo indica subestimação média: todas as GRUs subestimam mais que o HGB. O viés absoluto menor da persistência não compensa automaticamente seu MAE/RMSE maiores; são critérios distintos.

Os tempos das três MLPs somam 47,54 s; os das GRUs, 126,80 s, aproximadamente 2,67 vezes mais nesta execução. As redes têm 833 e 929 parâmetros: a GRU tem apenas 11,5% mais parâmetros, mas reutiliza transformações ao longo de 24 passos. Contagem de parâmetros não equivale ao tempo de treinamento. Esses tempos incluem avaliações por época e diferentes quantidades de épocas; não isolam o custo por atualização nem provam uma razão universal de desempenho.

O pico de 396,28 MiB informado é do processo inteiro. Não é o consumo exclusivo de uma GRU, nem deve ser comparado diretamente ao pico Linux como medida de eficiência de cada arquitetura.

## Por que o HGB difere da referência Linux?

O HGB Windows tem MAE 32,323956; a referência Linux, 31,846768. Nas 168 previsões, a diferença absoluta média é 3,082646 MWmed e a máxima é 10,179216. **Isso não é diferença apenas na última casa decimal.**

Estão documentadas diferenças de sistema, NumPy/pandas, scikit-learn **1.9.0 versus 1.8.0** e identidade binária dos pacotes de entrada. Em contraste, partições e normalizadores são numericamente iguais; os alvos de avaliação são idênticos; as previsões neurais diferem no máximo cerca de `2,38e-5` MWmed. Não foi realizado um experimento que alterasse apenas a versão da biblioteca ou apenas a entrada, portanto **a causa da diferença do HGB não foi isolada**.

Usar a mesma semente não fixa essas outras condições. Não há motivo para invalidar sua execução nem para substituir seu resultado pelo número Linux. A decisão local deve usar 32,323956 MWmed. Também não se recomenda trocar dependências do ambiente existente só para forçar coincidência; uma investigação de reprodução exata, se necessária no futuro, deve usar ambiente separado e entradas fixadas.

Referência de persistência/versões: [scikit-learn 1.8 — Model persistence](https://scikit-learn.org/1.8/model_persistence.html). As equações conferidas seguem [PyTorch 2.7 — GRUCell](https://docs.pytorch.org/docs/2.7/generated/torch.nn.GRUCell.html). Essas referências apoiam os contratos de API, não identificam a causa concreta da divergência.

## Situação e continuação

E114 aceita a execução e a implementação M08.3. Não há novo teste ou treino a exigir para esse aceite. Para consolidar a defesa, o aluno ainda precisa formular sua escolha provisória e explicar por que menor RMSE não resolveu o trade-off de MAE/viés/custo; a análise acima é do professor, não atribuída ao aluno.

M09.1 é a próxima prática: atenção escalada, Q/K/V, softmax estável, máscaras e posição. O pacote dessa unidade trabalha a matemática de atenção e uma janela histórica real; não apresenta pesos aleatórios como um modelo preditivo treinado. M09.2/posição/Transformer e M09.3/modelo temporal pré-treinado continuam escopos próprios. O inventário P1 permanece oito de dez entregas técnicas; não se inventa percentual global da formação.
