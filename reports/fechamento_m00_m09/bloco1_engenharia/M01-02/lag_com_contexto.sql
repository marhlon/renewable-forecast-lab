-- Janela calculada na grade com31/10 23h; filtro de novembro ocorre depois.

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
FROM temporal
WHERE din_instante >= '2025-11-01T00:00:00' AND din_instante < '2025-12-01T00:00:00'
ORDER BY id_ons,din_instante;

