# M05-01 — intervalos e estabilidade temporal

25/11/2026 · ajuste concluído; avaliação condicionada à liberação do arquivo reservado

Foram ajustados três regressores HGB de quantis: P10, P50 e P90. Usam as 28 variáveis do candidato pontual selecionado no estudo M03-03: 24 valores horários passados e quatro coordenadas cíclicas de hora e dia da semana. Não há previsão meteorológica neste experimento. Os parâmetros são os do protocolo integrado: 60 iterações, 15 folhas, mínimo de 20 amostras por folha, taxa 0,05, regularização 0,1, sem parada antecipada e semente 17.

O treino contém 7.221 origens, todas com alvo disponível estritamente antes de 01/07/2026. Na origem `t`, o último registro admitido nas entradas é `t−2h`; o alvo é `t+24h` e sua disponibilidade assumida é `t+26h`. O horário e o atraso são hipóteses de laboratório, não comprovações da publicação histórica do ONS.

A calibração usa outras 312 origens: 01/07 até 14/07 exclusivo. Os três quantis são ordenados dentro de cada linha por regra fixada antes da avaliação. Isso evita intervalos com extremidades invertidas; não garante a calibração. Houve oito cruzamentos antes dessa ordenação na amostra de calibração.

Para cada alvo da calibração, calculou-se `max(P10−y, y−P90, 0)`. Os 312 resíduos foram ordenados e foi escolhido o de posição `ceil((312+1)×0,8)=251`, contando a primeira posição como 1. A expansão obtida foi **15,1239760153 MWmed**. A regra congelada subtrai esse valor de P10 e o soma a P90, mantendo P50. A expansão é não negativa; isso não significa truncar os limites em zero. Nenhuma correção nova pode ser escolhida após a avaliação.

Na calibração, a cobertura passou de 70,1923% para 80,4487%; a largura média passou de 101,540809 para 131,788761 MWmed. Essas são estatísticas da amostra usada para obter a expansão. Não são a avaliação futura. A dependência temporal impede interpretar automaticamente a regra CQR como garantia conformal de cobertura para este processo.

O código congelado prevê uma comparação em 695 origens de outubro, com semanas fixas de 168 horas e uma parte final de 23 horas. Para períodos de pelo menos 48 origens, o alerta documental será acionado se a cobertura se afastar de 80% em mais de dez pontos percentuais. A parte de 23 horas será exibida sem esse julgamento. Interval score, largura, cobertura e Pinball Loss das extremidades efetivamente utilizadas serão registrados separadamente para a versão bruta ordenada e para a expandida.

Também foi fixado antes da leitura de outubro um bootstrap circular de blocos de 24 horas, 2.000 reamostragens e semente 17. A mesma sequência de índices será utilizada para os dois métodos. Serão mostrados percentis 2,5% e 97,5% das coberturas e da diferença CQR menos bruto, condicionais ao recorte e ao esquema de blocos. Isso não fornece uma garantia de independência, intercambialidade ou validade operacional futura.

O ajuste utilizou um limite de uma thread. O estudo pontual M03 tem configuração de execução própria; os tempos dessas rotinas não serão usados como comparação de desempenho computacional entre modelos.

O pipeline é `notebooks/bloco2_validacao_risco.py`. As chamadas `--preparar` e `--ajustar` terminaram com código 0. Código, fonte, bundle pontual, modelos, expansão e protocolos estão em `freeze.json`. Até este ponto nenhum arquivo de outubro foi lido por esta rotina. A implementação e a interpretação foram fornecidas com assistência de Codex, sem atribuir autonomia pessoal ao usuário.
