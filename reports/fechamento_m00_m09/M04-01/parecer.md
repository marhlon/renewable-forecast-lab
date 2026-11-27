# M04-01 — correção E51 no contrato de vento

25/11/2026 · execução local Windows/CPU · construção e revisão técnica assistidas por Codex.

A seleção de velocidade e componentes passou a usar exclusivamente
`wind_speed_mean_ms`, `wind_u_mean_ms` e `wind_v_mean_ms` em
[`validate_wind_geometry`](../../../src/renewable_forecast/weather_artifact.py).
A função anterior procurava substrings: `wind_speed_cubed_mean_m3s3` podia ser
escolhida como velocidade ou componente, conforme a ordem das chaves. Isso
misturava grandezas em m/s e m³/s³ e permitia decisões diferentes para o mesmo
pedido reordenado.

A correção mantém `np.hypot(u, v)` e a tolerância absoluta de `1e-8 m/s` na
condição `hypot(u, v) - speed <= 1e-8`. Componentes negativas são aceitas;
velocidade escalar negativa é rejeitada. As três entradas são obrigatórias e
devem ser números finitos, sem booleanos ou nulos. Chaves ausentes deixam de
ser silenciosamente ignoradas. O validador completo conserva o contrato das
32 features e a ordenação declarada no manifesto. Nenhuma outra função ou
configuração do estimador foi modificada por esta tarefa.

O [protocolo](protocolo.json) foi registrado antes da execução. Passaram
**37 casos geométricos e uma integração com o pedido histórico**; os mesmos
38 casos também passaram como testes pytest. São duas formas de conferir a
mesma cobertura, não 76 casos independentes. As
[contraprovas](contraprovas.json) registram os resultados e o
[recibo](resultado.json) reúne comandos, códigos de saída, versões e hashes.

Foram aceitos os casos geometricamente válidos com ordem original, invertida
e termo cúbico primeiro; o caso velocidade 12/u 30/v 0 foi rejeitado nas três
ordens. Também passaram as verificações de zero, componentes negativas,
tolerância, números grandes tratados por `hypot`, campos ausentes,
NaN/infinidades, nulos, booleanos, texto e tipo de entrada incompatível.
As entradas foram preservadas tanto em sucesso quanto em rejeição.

A integração leu somente `request.json` e `model/manifest.json` do replay
histórico `h24_replay_20260801T0500Z`. `validate_request` devolveu a mesma linha
de shape `[1, 32]` nas duas ordens e rejeitou o pedido impossível reordenado.
Chamadas a `HistGradientBoostingRegressor.fit` e `joblib.load` foram bloqueadas
durante essa contraprova. Nenhum pickle foi aberto, estimador ajustado,
contêiner iniciado ou recurso externo acessado. Os JSONs históricos mantiveram
seus hashes.

Ambiente observado: Python 3.12.13, NumPy 2.5.3, pandas 3.0.5,
scikit-learn 1.9.0, joblib 1.6.0 e pytest 9.1.1. Os dois comandos concluíram
com saída zero; pytest registrou `38 passed in 20.04s`.

**Decisão proposta:** C1 e C2 foram demonstrados nas verificações locais;
o item fica aguardando a revisão técnica separada e a atualização do cadastro
pelo responsável pela consolidação. Esta implementação foi assistida e não
constitui prova de resposta independente do aluno ou aceite humano.

O resultado fecha apenas a falha de seleção/validação de campos. A condição
geométrica pressupõe médias com os mesmos pesos não negativos; não verifica
por si só a composição dos pesos. Não foram reavaliados desempenho preditivo,
fuso, disponibilidade histórica, cadastro point-in-time ou aprovação operacional.
Os aceites e os artefatos dos experimentos anteriores permanecem preservados.
