# M02-06 — parecer da aplicação de perdas à decisão

25/11/2026 · entrega de engenharia · Renewcast/P1

A clínica foi recuperada de `D:\Downloads\clinica_decisao_forecast.py` e copiada para `notebooks/clinica_decisao_forecast.py` sem alterar seus 8.024 bytes. O SHA-256 da origem e da cópia é `5d129c89a32bc782390a7f56de74e7faa39b5c390b30f353085ca74bcc3692ec`. A autoria original do arquivo não foi estabelecida pelo conteúdo. A aplicação, a verificação e esta interpretação foram realizadas com assistência de Codex; não constituem comprovação de desempenho independente do usuário.

O protocolo foi gravado antes da execução da clínica. A execução `20261125T162028Z_f0f4439d` terminou com código 0 e gerou seu próprio recibo. Em seguida, um adendo fixou o código da verificação independente antes de ela começar. Essa segunda execução também terminou com código 0, sem chamar modelos ou repetir a clínica. Acentos de algumas linhas do log original foram substituídos na captura do console; os CSVs, os JSONs e os valores numéricos não foram afetados. O recibo registra essa limitação.

## Resultado conferido

Foram recalculadas as 36 combinações de 12 políticas com três cenários de custo, usando as mesmas 168 origens e alvos dentro desse estudo. Em cada linha, o custo coincide com a clínica, com tolerância absoluta de `1e-10`, e a perda assimétrica coincide com a Pinball Loss multiplicada pela soma dos custos. A mediana extraída do arquivo quantílico coincide com a previsão Chronos já arquivada. P20 e P80 foram lidos diretamente da grade nativa, sem interpolação.

| Custo de subestimar : superestimar | Menor custo médio observado | Política |
| --- | ---: | --- |
| 1 : 1 | 31,340738 | Chronos P50 |
| 4 : 1 | 58,740425 | Chronos P80 |
| 1 : 4 | 54,573165 | Chronos P20 |

Os custos são unidades relativas hipotéticas por emissão. No estudo contínuo, correspondem a erros em MWmed multiplicados pelos pesos; não são reais, receita ou estimativa de impacto financeiro. As políticas já tinham sido observadas nessa semana. O menor custo é uma descrição do recorte, sem seleção prospectiva de política.

A aplicação separada de FP/FN produziu 66 linhas sobre 504 origens por método, com 113 eventos positivos. Os três métodos usam exatamente a mesma coorte dentro desse segundo estudo. Com falso negativo custando quatro vezes o falso positivo, o HGB passa de custo 191 no corte 0,5 para 158 no corte 0,2. Entretanto, os alarmes sobem de 109 para 156 e ultrapassam o teto de 120 usado na seleção histórica. A política antiga permanece preservada. Com falso positivo custando quatro vezes o falso negativo, o corte 0,8 dá custo 110 à regressão logística e 132 ao HGB; nunca alarmar custa 113. Isso impede defender o HGB como melhor decisão sob qualquer custo.

## Limites e decisão

Não houve treino, inferência, calibração de probabilidades, download ou alteração dos resultados anteriores. Os hashes das saídas declaradas nos recibos M09.3 e de eventos foram conferidos antes e depois do cálculo. Geração e eventos têm coortes e unidades de custo distintas; seus valores não foram somados ou comparados como se fossem um único ranking.

O evento compara geração disponível e geração alvo separadas por 26 horas. Não valida rampas de uma hora. O corte analítico pressupõe probabilidades adequadas e os custos declarados; a redução de custo histórica não comprova calibração futura. Três quantis não foram convertidos em uma probabilidade de evento. Fuso, borda do intervalo, disponibilidade histórica da meteorologia e versões cadastrais continuam sujeitos às restrições operacionais já registradas.

A entrega aplicada M02-06 está sustentada pelos arquivos, pelas contas e pela interpretação. Para operação, ainda são necessários custos de negócio definidos, orçamento executável de alarmes, acompanhamento de calibração e uma avaliação futura com política fixada antes dos resultados. Esta análise não aprova implantação nem certifica autonomia pessoal.

Os detalhes de reprodução e a explicação completa estão em [Bloco_2_Decisao_Risco.md](../../../../docs/roadmap_m00_m09/Bloco_2_Decisao_Risco.md). O [resultado.json](resultado.json) registra fontes, hashes, verificações e atribuição.
