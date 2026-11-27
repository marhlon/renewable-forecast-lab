# Figura proposta para a avaliação final de setembro

Esta é uma especificação editorial. Nenhuma imagem foi gerada nesta revisão. A avaliação de 671 origens não possui figura pronta localizada no inventário consultado.

**Pergunta visual:** como observado, persistência, HGB selecionado e P50/intervalo do Chronos diferem na mesma linha do tempo? Usar uma figura de série temporal, sem fotografias de parques eólicos ou elementos sem correspondência com as medições.

**Entrada:** `reports/fechamento_m00_m09/bloco3_engenharia/M03-04/predictions.csv`, com `forecast_origin`, `target_time`, `y24`, `method` e `prediction`; quantis em `chronos.npz` e definição de alinhamento em `chronos.json`. Conferir os hashes no recibo e os timestamps antes da renderização. Os arrays NPZ são necessários para o intervalo; a tabela agregada não permite reconstruir sua trajetória.

**Recorte:** partição final retrospectiva, setembro/2026; 671 origens de 02/09 01h a 29/09 23h e respectivos alvos de 03/09 01h a 30/09 23h. O eixo temporal conserva a referência da entrada, sem afirmar fuso físico validado.

**Composição:** uma única figura, com linhas para observado, persistência, HGB selecionado e Chronos P50; faixa P10–P90 identificada como quantis brutos do Chronos. Usar todas as origens, mantendo ausências se houver e sem alisar erros. Não usar os gráficos de julho como se representassem setembro.

**Eixos:** timestamp do alvo no horizontal; geração em MWmed no vertical. Legenda com nomes das previsões e identificação explícita da faixa. P50 é mediana predita. Se a figura precisar de detalhe ampliado, a seleção do trecho deve ser declarada e o agregado de 671 origens mantido no texto.

**Legenda proposta:** “Geração observada e previsões h+24 para CJU_BA5EIGT, alvos de 03 a 30/09/2026, em MWmed. Histórico disponível até origem−2h sob atraso assumido. A faixa representa P10–P90 bruto do Chronos. Avaliação retrospectiva identificada por `bloco3_engenharia/M03-04`; não é uma emissão contemporânea.”

**Texto alternativo proposto:** “Série temporal da geração observada, persistência, HGB e mediana do Chronos, com faixa P10–P90 do Chronos, nos 671 alvos de setembro de 2026.”

**Destino futuro:** `docs/images/renewcast_setembro_2026.png`. Esse arquivo ainda não existe; o README não inclui uma referência de imagem para ele. A publicação da figura requer renderização, conferência visual e vínculo dos números aos mesmos arquivos, sem inferência nova.

Imagens históricas existentes: `docs/evidencias_m09_3_local/comparacao_modelos.png` e `intervalos_previsoes.png`. O gerador identifica o run de desenvolvimento `20261117T213329Z_3b201a01`, 168 alvos de julho. Foram inspecionadas visualmente, mas representam outro recorte e não foram reapresentadas como a avaliação final atual.
