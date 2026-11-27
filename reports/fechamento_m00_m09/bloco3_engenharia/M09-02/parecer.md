# Parecer aplicado — M09-02

Entrega de engenharia de 25/11/2026. Solução, execução e revisão técnica fornecidas pelo Codex, sem resposta independente do usuário nem certificação de autonomia. Antes do cálculo foram registrados contexto 12, cinco slots, E=12, três cabeças de dimensão quatro, FFN de dimensão 24, duas camadas e máscaras de disponibilidade. Não houve treino ou modificação dos blocos históricos.

**Resultado técnico favorável ao aceite aplicado.** Foram confirmados memória `[2,12,12]`, saída `[2,5,12]`, cross Q `[2,3,5,4]` e K/V `[2,3,12,4]`. As probabilidades encoder, decoder self e cross tiveram shapes `[2,3,12,12]`, `[2,3,5,5]` e `[2,3,5,12]`. Há 6.432 parâmetros nas pilhas deste caso. Os slots são consultas sintéticas em origens sucessivas, sem cabeça de previsão e sem associação automática a cinco horizontes horários.

Na cross-attention, a representação do decoder produz Q e a memória do encoder produz K e V. A reconstrução explícita das projeções, `QKᵀ/sqrt(4)`, máscara, softmax nas chaves, produto por V, concatenação e projeção de saída teve diferença zero para o bloco. Probabilidades bloqueadas foram zero; a maior diferença de soma por linha contra um foi **2,220446049250313e−16**.

Todas as equações de soma residual, LayerNorm após a soma e FFN `12→24→12` foram conferidas nas duas camadas de encoder e decoder, com diferença zero. A LayerNorm atua sobre as 12 coordenadas do token; a FFN usa os mesmos pesos separadamente em cada posição. O decoder possui residual/norma para self-attention, cross-attention e FFN. A tolerância predefinida foi `1e−12`.

A fonte j possui disponibilidade sintética j+4. As consultas nas origens 7..11 só podem usar fontes até 3..7. Alterar fontes 4..11 preservou a primeira consulta quando o encoder era causal em todas as camadas e a cross-attention limitava a disponibilidade: **diferença zero**. Com encoder livre e apenas a mesma máscara de cross-attention, a primeira consulta mudou **0,590813770621786**. O motivo é o caminho indireto: memórias permitidas 0..3 já misturaram fontes indisponíveis por meio do encoder livre. Alterar fontes 6..11 também preservou os três primeiros slots do caso seguro, com diferença zero.

Outro teste alterou apenas os slots futuros 3 e 4. Com self-attention causal em cada camada, o prefixo 0..2 ficou igual, diferença zero, e os slots perturbados mudaram **2,9840134975551185**. Com self-attention livre, o prefixo mudou **1,2223850103882634**. A máscara de disponibilidade histórica e a proteção contra consultas futuras são contratos complementares, demonstrados por controles positivos separados.

Quando todo o contexto já está disponível na emissão única, um encoder livre pode combinar esse histórico; isso difere de reconstruir decisões de prefixos anteriores. Para decisões anteriores, truncar a entrada ao que era conhecido ou impor restrições em todos os caminhos é necessário. Máscara causal por índice isolada não garante respeito à latência real de publicação. O CSV registra origem, índice da fonte, disponibilidade assumida, permissão e peso de uma cabeça para as 60 combinações.

O runner terminou com retorno 0 e 16 conferências aprovadas. O teste específico passou. A demonstração usa representações sintéticas e pesos aleatórios, não mede qualidade de previsão em MWmed e não comprova publicação real, shadow ao vivo ou operação. O fornecimento integral da solução atende ao modo de engenharia solicitado e não constitui prova pessoal de transferência independente.

Evidências: `protocolo.json`, `resultado.json`, `disponibilidade_e_atencao.csv`, `notebooks/bloco3_transferencia_neural.py`, `tests/test_bloco3_transferencia_neural.py` e `docs/roadmap_m00_m09/Bloco_3_Transferencia_Neural.md`.
