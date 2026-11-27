-- DEMONSTRAÇÃO SINTÉTICA RESOLVIDA, ASSISTIDA. Não é a resposta independente.
-- Tabelas em memória: fonte(record_id,id_ons,din_instante,val_geracao),
-- dias(id_ons,dia) e grade(id_ons,din_instante).

CREATE TEMP VIEW chaves_repetidas AS
SELECT id_ons, din_instante, COUNT(*) AS copias
FROM fonte GROUP BY id_ons, din_instante HAVING COUNT(*) > 1;

CREATE TEMP VIEW quarentena AS
SELECT f.* FROM fonte AS f
JOIN chaves_repetidas AS d
  ON f.id_ons=d.id_ons AND f.din_instante=d.din_instante;

CREATE TEMP VIEW limpa AS
SELECT f.* FROM fonte AS f
LEFT JOIN chaves_repetidas AS d
  ON f.id_ons=d.id_ons AND f.din_instante=d.din_instante
WHERE d.id_ons IS NULL;

CREATE TEMP VIEW resumo AS
SELECT id_ons, date(din_instante) AS dia,
       COUNT(*) AS horas_presentes, COUNT(val_geracao) AS horas_validas,
       AVG(val_geracao) AS media_mwmed
FROM limpa GROUP BY id_ons, date(din_instante);

-- LEFT mantém o calendário. Preencher só contagens preserva média desconhecida.
CREATE TEMP VIEW diario_left AS
SELECT d.id_ons, d.dia,
       COALESCE(r.horas_presentes,0) AS horas_presentes,
       COALESCE(r.horas_validas,0) AS horas_validas,
       r.media_mwmed, COALESCE(r.horas_validas,0)/24.0 AS cobertura
FROM dias AS d LEFT JOIN resumo AS r ON d.id_ons=r.id_ons AND d.dia=r.dia;

CREATE TEMP VIEW diario_inner AS
SELECT d.id_ons, d.dia, r.horas_presentes, r.horas_validas, r.media_mwmed
FROM dias AS d JOIN resumo AS r ON d.id_ons=r.id_ons AND d.dia=r.dia;

-- Sobre a fonte esparsa: o deslocamento é de uma LINHA dentro da série.
CREATE TEMP VIEW lag_esparso AS
SELECT id_ons,din_instante,val_geracao,
       LAG(din_instante) OVER(PARTITION BY id_ons ORDER BY din_instante) AS instante_anterior,
       LAG(val_geracao) OVER(PARTITION BY id_ons ORDER BY din_instante) AS valor_linha_anterior
FROM limpa;

-- Depois da grade completa, uma linha anterior equivale a uma hora do relógio.
CREATE TEMP VIEW grade_completa AS
SELECT g.id_ons,g.din_instante,l.val_geracao,
       CASE WHEN l.record_id IS NULL THEN 0 ELSE 1 END AS registro_presente
FROM grade AS g LEFT JOIN limpa AS l
  ON g.id_ons=l.id_ons AND g.din_instante=l.din_instante;

CREATE TEMP VIEW lag_grade AS
SELECT *, LAG(val_geracao) OVER(PARTITION BY id_ons ORDER BY din_instante) AS valor_hora_anterior,
          LAG(registro_presente) OVER(PARTITION BY id_ons ORDER BY din_instante) AS registro_hora_anterior
FROM grade_completa;

SELECT * FROM diario_left ORDER BY id_ons,dia;
-- Os demais SELECTs de auditoria são executados pelo laboratório e documentados no guia.
