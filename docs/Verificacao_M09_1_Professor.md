# M09.1 — verificação da entrega

15/11/2026, run `20261115T215729Z_f462e113`, Linux/CPU, dois threads, PyTorch 2.7.1+cpu e NumPy float64. Não houve execução Windows nesta preparação.

O programa foi executado sobre a entrada M07.3 do professor, com os hashes identificados em `resultado.json`. A janela real contém as 24 medições de 02/07/2026 03h a 03/07/2026 02h, para a origem 03/07/2026 04h no eixo sem fuso físico validado. Os valores futuros do alvo não entram em Q, K ou V.

Oito grupos de conferências passaram: NumPy versus PyTorch em lotes e dimensões retangulares; caso manual de saída 15; máscara causal com diagonal; bloqueio de perturbação posterior; igualdade da última consulta em uma camada; softmax estável com scores grandes; rejeição de máscaras inválidas/linha bloqueada; equivariância de permutação sem posição. Maior diferença contra PyTorch: `4,440892098500626e-16`, tolerância `1e-12`.

Shapes reais: Q/K `[1,24,4]`, V `[1,24,1]`, pesos `[1,24,24]`, saída `[1,24,1]`. A diferença entre última consulta livre e causal foi zero. A diferença de permutação sem posição foi aproximadamente `1,42e-14`; mantendo posições fixas e permutando conteúdos, a diferença foi 4,639083 nas representações escalares calculadas.

Esses números verificam a aritmética e a dependência de posição, não acurácia. As projeções são fixas, não treinadas, e as saídas são representações ponderadas do histórico. O pacote não executa Transformer completo, modelo fundacional, novo treino ou avaliação operacional.

A função de referência completa está em `src/renewable_forecast/attention_math.py`. O suporte de dados M08.3 é reutilizado, sem alteração e sem nova cópia no ZIP. Falta ao aluno executar o laboratório, implementar sua função NumPy e defender a semântica de máscara conforme a aula.
