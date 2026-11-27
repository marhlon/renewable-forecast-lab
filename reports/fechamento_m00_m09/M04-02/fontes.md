# M04-02 — fontes da geração

Consulta em 25/11/2026, com assistência Codex.

- [Dicionário ONS, PDF de 09/06/2023](https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/geracao_usina_2_ho/DicionarioDados_GeracaoPorUsina.pdf): página 1 descreve `din_instante` como “Data de referência”; página 2 informa MWmed para `val_geracao`. O formato temporal não contém offset. As três páginas consultadas não explicitam fuso nem borda do intervalo.
- [Portal ONS do conjunto](https://dados.ons.org.br/dataset/geracao-usina-2): descreve base horária e admite atualizações posteriores à publicação. Não usei a data de consulta como data de disponibilidade histórica.
- `src/renewable_forecast/weather_training.py` e metadados h24 existentes: o projeto declara `America/Sao_Paulo` como hipótese, atraso de duas horas e semântica do intervalo não verificada. São escolhas internas, não documentação primária do produtor.

O documento remoto foi lido pelo navegador de pesquisa; não foi calculado SHA-256 dos bytes originais do PDF ou do HTML. Os hashes de arquivos locais conferidos constam do resultado.

## Perguntas preparadas, não enviadas

1. Para o conjunto CJU_BA5EIGT e o período utilizado, qual é o fuso físico de `din_instante`, inclusive eventuais regras históricas de relógio civil?
2. Uma linha rotulada 03h representa qual intervalo exato? A hora marca início, fim ou outra referência? Quais são as convenções de inclusão das bordas?
3. Existem timestamps de primeira publicação, retificação e versões preservadas que permitam saber qual valor era conhecido em cada emissão?

A unidade está documentada; os demais pontos permanecem sem confirmação suficiente nesta consulta. Não extrapole a ausência neste material para todos os documentos do ONS.
