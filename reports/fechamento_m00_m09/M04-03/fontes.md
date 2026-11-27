# M04-03 — fontes de disponibilidade meteorológica

Consulta em 25/11/2026, com assistência Codex.

1. [Single Runs API](https://open-meteo.com/en/docs/single-runs-api): a identificação UTC da rodada corresponde à inicialização, não à primeira disponibilidade pública. Recuperar uma rodada arquivada não certifica o horário em que ela podia ser consultada no passado.
2. [Model Updates](https://open-meteo.com/en/docs/model-updates): diferencia inicialização, conversão e disponibilização. Também descreve replicação com diferenças temporárias entre servidores. Não usei essa página de estado como um histórico observado de julho.
3. `src/renewable_forecast/weather_runs.py`: grava coleta, resposta e protocolo separadamente; `weather_available_at` é calculado a partir da latência assumida.
4. `data/external/weather/CJU_BA5EIGT/*/metadata.json`: recibos locais contêm `fetched_at_utc`, `availability_is_assumed=true` e `historical_availability_verified=false`. O CSV `disponibilidade.csv` enumera os registros efetivamente auditados e seus hashes.

O atraso de seis horas permanece hipótese. Um horário típico descrito pelo serviço não substitui a publicação observada para cada rodada, versão e servidor usados no experimento.

## Perguntas preparadas, não enviadas

- Há registros históricos da primeira disponibilização das rodadas GFS utilizadas em julho de 2026, incluindo eventuais atrasos e versões corrigidas?
- Qual registro permitiria vincular os bytes recuperados à versão que estava acessível antes de cada origem, considerando replicação e atualização do arquivo?
- Quais campos ou logs preservados distinguem inicialização, processamento, primeira publicação e consulta efetiva na API pertinente?

Nenhuma API meteorológica ou novo dataset foi consultado nesta auditoria. Somente documentação e caches já existentes foram lidos.
