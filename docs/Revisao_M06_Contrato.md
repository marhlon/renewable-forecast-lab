# M06 — API reproduzida e contrato de decisão

Marlon Alves Bomfim · Renewcast · 03/10/2026 · E65/E66

Sua execução da API está aceita. O cliente enviou uma probabilidade histórica real, recebeu HTTP 200 e verificou a rejeição HTTP 422 para uma probabilidade impossível, 1,2. Os seis JSONs e as duas capturas recebidos foram reconciliados. Não é necessário repetir esse cliente para encerrar a reprodução.

O pedido real tinha p_event=0,16175954827073333. Como a política exige p_event >= 0,5, a resposta alarm=false está correta. O serviço aplicou uma política a uma probabilidade já calculada; não executou o classificador nessa chamada.

## Por que o Swagger rejeitou

A resposta foi: “O método recebido difere do método selecionado na política.” O exemplo automático estava preenchido com valores genéricos. A política carregada exige as relações abaixo:

| Campo | Exemplo enviado | Contrato da política |
|---|---|---|
| method | historical_frequency | hgb_weather_classifier |
| drop_threshold_mwmed | 1 | 22.77 |
| target_time | Igual à origem | Origem + 24 horas |
| history_end | Igual à origem | Origem − 2 horas |

p_event=0,5 é válido. A validação de compatibilidade para na primeira divergência; trocar somente o método ainda deixaria o limiar físico e os horários incorretos. Um campo ser válido isoladamente não garante que o pedido corresponda à política.

## Pedido completo para usar agora

Abra http://127.0.0.1:8000/docs, expanda POST /decisions, clique em **Try it out**, substitua o corpo inteiro e clique em **Execute**:

```json
{
  "conjunto": "CJU_BA5EIGT",
  "method": "hgb_weather_classifier",
  "forecast_origin": "2026-07-11T06:00:00Z",
  "history_end": "2026-07-11T04:00:00Z",
  "target_time": "2026-07-12T06:00:00Z",
  "drop_threshold_mwmed": 22.77,
  "p_event": 0.5
}
```

Resultado conferido pelo professor: **HTTP 200, threshold=0.5 e alarm=true**. A igualdade aciona o alarme porque a comparação é `>=`. Essa probabilidade de 0,5 é uma entrada didática para demonstrar a fronteira; não é uma nova previsão do modelo para julho.

## Atualizar os exemplos da página

O pacote `renewcast_m06_swagger_20261003.zip` inclui o módulo `src/renewable_forecast/decision_api.py`, esta revisão, o roteiro, o pedido JSON e as evidências da conferência. A alteração usa `Body(openapi_examples=...)` para oferecer exemplos nomeados, coerentes com a política carregada. As validações e a regra de decisão permanecem as mesmas. Referência: https://fastapi.tiangolo.com/tutorial/schema-extra-example/.

Baixe o ZIP para `C:\renewable-forecast-lab`. No terminal que está executando o servidor, pressione **Ctrl+C**. Depois execute na raiz do projeto, com o ambiente `renewable-forecast` ativo:

```powershell
Expand-Archive -LiteralPath .\renewcast_m06_swagger_20261003.zip -DestinationPath . -Force
python -m renewable_forecast.decision_api --policy reports/events/CJU_BA5EIGT/h24_d2_july_drop22p77_v1/decisions/policy.json --port 8000
```

Atualize `/docs`. Em POST /decisions, selecione o exemplo **Válido: probabilidade igual ao limiar — alarme verdadeiro**. Há também uma contraprova explícita de probabilidade inválida. Não é necessário instalar dependências, exportar novamente a política nem treinar modelos.

A conferência executada reproduziu as respostas do aluno, a rejeição original do Swagger e o resultado no limiar. Também verificou que o corpo continua obrigatório e que a entrada inválida continua rejeitada. Os registros estão em `docs/evidencias_m06_contrato/`.

## Fixação e próxima entrega

| Termo | Aplicação neste projeto |
|---|---|
| Contrato | Tipos, campos e relações que o pedido precisa respeitar |
| Exemplo | Um corpo concreto usado para mostrar como chamar a API |
| Replay | Aplicação da política a uma probabilidade histórica já existente |
| Inferência | Execução do classificador sobre features para calcular p_event |
| Política | Regra que transforma p_event em alarme |

`capacity_enforced_at_runtime=false` informa que o serviço não mantém um contador nem impõe uma cota de 120 alarmes. A restrição foi verificada no conjunto de desenvolvimento; o limiar de 0,5 sozinho não garante um limite em dados futuros.

**Próxima entrega:** persistir e carregar o classificador, calcular `predict_proba` a partir das features disponíveis e conectar o resultado à decisão. O aceite deverá demonstrar inferência sem alvo observado, ordem das features conferida e identidade do artefato na resposta. Shadow contínuo e monitoramento vêm depois.

O roteiro 1.36 registra M06.1 reproduzida. O produto permanece em **7/10 macroentregas = 70%**, com avanço dentro da oitava. Esse indicador conta entregas; não representa percentual de domínio profissional.
