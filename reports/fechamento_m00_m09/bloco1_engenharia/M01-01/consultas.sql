-- Solucao tecnica assistida. Entradas: recorte e calendario em memoria.
-- Duplicatas inteiras em quarentena; NULL nunca e geracao zero.

-- consulta: diario
WITH frequencias AS (
    SELECT id_ons, din_instante, COUNT(*) AS multiplicidade
    FROM recorte GROUP BY id_ons, din_instante
),
limpo AS (
    SELECT r.* FROM recorte r
    JOIN frequencias f USING (id_ons, din_instante)
    WHERE f.multiplicidade = 1
),
grade AS (
    SELECT c.id_ons, c.din_instante, l.val_geracao,
           CASE WHEN l.din_instante IS NULL THEN 0 ELSE 1 END AS registro_presente
    FROM calendario c LEFT JOIN limpo l USING (id_ons, din_instante)
),
janela AS (
    SELECT *,
           LAG(din_instante) OVER (PARTITION BY id_ons ORDER BY din_instante) AS instante_anterior_1h,
           LAG(val_geracao) OVER (PARTITION BY id_ons ORDER BY din_instante) AS valor_anterior_1h,
           LAG(registro_presente) OVER (PARTITION BY id_ons ORDER BY din_instante) AS registro_anterior_presente
    FROM grade
),
temporal AS (
    SELECT *,
           val_geracao - valor_anterior_1h AS delta_1h,
           CASE WHEN instante_anterior_1h IS NULL THEN 'fronteira_do_recorte'
                WHEN registro_anterior_presente = 0 THEN 'hora_anterior_sem_registro'
                WHEN valor_anterior_1h IS NULL THEN 'medicao_anterior_nula'
                ELSE 'lag_disponivel' END AS estado_lag
    FROM janela
),
bruto_dia AS (
    SELECT id_ons, substr(din_instante,1,10) AS dia, COUNT(*) AS linhas_fonte
    FROM recorte GROUP BY id_ons, dia
),
duplicadas_dia AS (
    SELECT id_ons, substr(din_instante,1,10) AS dia,
           COUNT(*) AS chaves_duplicadas, SUM(multiplicidade) AS linhas_quarentena,
           SUM(multiplicidade-1) AS duplicatas_excedentes
    FROM frequencias WHERE multiplicidade > 1 GROUP BY id_ons, dia
),
diario AS (
    SELECT id_ons, substr(din_instante,1,10) AS dia,
           COUNT(*) AS horas_esperadas, SUM(registro_presente) AS horas_presentes,
           COUNT(val_geracao) AS horas_validas,
           SUM(CASE WHEN registro_presente = 1 AND val_geracao IS NULL THEN 1 ELSE 0 END) AS horas_nulas_presentes,
           SUM(CASE WHEN val_geracao = 0 THEN 1 ELSE 0 END) AS horas_zero,
           COUNT(*) - SUM(registro_presente) AS horas_sem_registro,
           AVG(val_geracao) AS media_geracao_mwmed,
           SUM(registro_presente)*1.0/COUNT(*) AS cobertura_presenca,
           COUNT(val_geracao)*1.0/COUNT(*) AS cobertura_valida,
           COUNT(valor_anterior_1h) AS lags_conhecidos,
           COUNT(*)-COUNT(valor_anterior_1h) AS lags_desconhecidos,
           COUNT(delta_1h) AS pares_validos_delta, AVG(delta_1h) AS media_delta_1h
    FROM temporal GROUP BY id_ons, dia
)
SELECT d.id_ons, d.dia, d.horas_esperadas, COALESCE(b.linhas_fonte,0) AS linhas_fonte,
       COALESCE(q.chaves_duplicadas,0) AS chaves_duplicadas,
       COALESCE(q.linhas_quarentena,0) AS linhas_quarentena,
       COALESCE(q.duplicatas_excedentes,0) AS duplicatas_excedentes,
       d.horas_presentes, d.horas_validas, d.horas_nulas_presentes, d.horas_zero,
       d.horas_sem_registro, d.media_geracao_mwmed, d.cobertura_presenca, d.cobertura_valida,
       d.lags_conhecidos, d.lags_desconhecidos, d.pares_validos_delta, d.media_delta_1h
FROM diario d LEFT JOIN bruto_dia b USING (id_ons,dia)
LEFT JOIN duplicadas_dia q USING (id_ons,dia)
ORDER BY d.id_ons,d.dia;

-- consulta: horario
WITH frequencias AS (
    SELECT id_ons, din_instante, COUNT(*) AS multiplicidade
    FROM recorte GROUP BY id_ons, din_instante
),
limpo AS (
    SELECT r.* FROM recorte r
    JOIN frequencias f USING (id_ons, din_instante)
    WHERE f.multiplicidade = 1
),
grade AS (
    SELECT c.id_ons, c.din_instante, l.val_geracao,
           CASE WHEN l.din_instante IS NULL THEN 0 ELSE 1 END AS registro_presente
    FROM calendario c LEFT JOIN limpo l USING (id_ons, din_instante)
),
janela AS (
    SELECT *,
           LAG(din_instante) OVER (PARTITION BY id_ons ORDER BY din_instante) AS instante_anterior_1h,
           LAG(val_geracao) OVER (PARTITION BY id_ons ORDER BY din_instante) AS valor_anterior_1h,
           LAG(registro_presente) OVER (PARTITION BY id_ons ORDER BY din_instante) AS registro_anterior_presente
    FROM grade
),
temporal AS (
    SELECT *,
           val_geracao - valor_anterior_1h AS delta_1h,
           CASE WHEN instante_anterior_1h IS NULL THEN 'fronteira_do_recorte'
                WHEN registro_anterior_presente = 0 THEN 'hora_anterior_sem_registro'
                WHEN valor_anterior_1h IS NULL THEN 'medicao_anterior_nula'
                ELSE 'lag_disponivel' END AS estado_lag
    FROM janela
)
SELECT id_ons,din_instante,registro_presente,val_geracao,instante_anterior_1h,
       valor_anterior_1h,registro_anterior_presente,delta_1h,estado_lag
FROM temporal ORDER BY id_ons,din_instante;

-- consulta: quarentena
WITH frequencias AS (
    SELECT id_ons, din_instante, COUNT(*) AS multiplicidade
    FROM recorte GROUP BY id_ons, din_instante
),
limpo AS (
    SELECT r.* FROM recorte r
    JOIN frequencias f USING (id_ons, din_instante)
    WHERE f.multiplicidade = 1
),
grade AS (
    SELECT c.id_ons, c.din_instante, l.val_geracao,
           CASE WHEN l.din_instante IS NULL THEN 0 ELSE 1 END AS registro_presente
    FROM calendario c LEFT JOIN limpo l USING (id_ons, din_instante)
),
janela AS (
    SELECT *,
           LAG(din_instante) OVER (PARTITION BY id_ons ORDER BY din_instante) AS instante_anterior_1h,
           LAG(val_geracao) OVER (PARTITION BY id_ons ORDER BY din_instante) AS valor_anterior_1h,
           LAG(registro_presente) OVER (PARTITION BY id_ons ORDER BY din_instante) AS registro_anterior_presente
    FROM grade
),
temporal AS (
    SELECT *,
           val_geracao - valor_anterior_1h AS delta_1h,
           CASE WHEN instante_anterior_1h IS NULL THEN 'fronteira_do_recorte'
                WHEN registro_anterior_presente = 0 THEN 'hora_anterior_sem_registro'
                WHEN valor_anterior_1h IS NULL THEN 'medicao_anterior_nula'
                ELSE 'lag_disponivel' END AS estado_lag
    FROM janela
)
SELECT r.registro_id,r.id_ons,r.din_instante,r.val_geracao,f.multiplicidade
FROM recorte r JOIN frequencias f USING (id_ons,din_instante)
WHERE f.multiplicidade > 1 ORDER BY r.id_ons,r.din_instante,r.registro_id;

-- consulta: lag_esparso
WITH frequencias AS (
    SELECT id_ons, din_instante, COUNT(*) AS multiplicidade
    FROM recorte GROUP BY id_ons, din_instante
),
limpo AS (
    SELECT r.* FROM recorte r
    JOIN frequencias f USING (id_ons, din_instante)
    WHERE f.multiplicidade = 1
),
grade AS (
    SELECT c.id_ons, c.din_instante, l.val_geracao,
           CASE WHEN l.din_instante IS NULL THEN 0 ELSE 1 END AS registro_presente
    FROM calendario c LEFT JOIN limpo l USING (id_ons, din_instante)
),
janela AS (
    SELECT *,
           LAG(din_instante) OVER (PARTITION BY id_ons ORDER BY din_instante) AS instante_anterior_1h,
           LAG(val_geracao) OVER (PARTITION BY id_ons ORDER BY din_instante) AS valor_anterior_1h,
           LAG(registro_presente) OVER (PARTITION BY id_ons ORDER BY din_instante) AS registro_anterior_presente
    FROM grade
),
temporal AS (
    SELECT *,
           val_geracao - valor_anterior_1h AS delta_1h,
           CASE WHEN instante_anterior_1h IS NULL THEN 'fronteira_do_recorte'
                WHEN registro_anterior_presente = 0 THEN 'hora_anterior_sem_registro'
                WHEN valor_anterior_1h IS NULL THEN 'medicao_anterior_nula'
                ELSE 'lag_disponivel' END AS estado_lag
    FROM janela
),
esparso AS (
    SELECT id_ons,din_instante,val_geracao,
           LAG(din_instante) OVER (PARTITION BY id_ons ORDER BY din_instante) AS instante_anterior_fonte,
           LAG(val_geracao) OVER (PARTITION BY id_ons ORDER BY din_instante) AS valor_anterior_fonte
    FROM limpo
)
SELECT *, (CAST(strftime('%s',din_instante) AS INTEGER)
           - CAST(strftime('%s',instante_anterior_fonte) AS INTEGER))/3600.0 AS intervalo_anterior_horas
FROM esparso ORDER BY id_ons,din_instante;
