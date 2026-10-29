-- P1: Quais situações de voo existem e quanto cada uma representa?
SELECT situacao_voo,
       COUNT(*) AS voos,
       ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
FROM RAW_VRA
GROUP BY situacao_voo
ORDER BY voos DESC;


-- P2: Quantos voos por mês (pela partida prevista)?
SELECT LEFT(partida_prevista, 7) AS mes,
       COUNT(*) AS voos
FROM RAW_VRA
GROUP BY mes
ORDER BY mes;


-- P3: Quais companhias mais voam?
SELECT v.empresa_icao,
       e.razao_social,
       COUNT(*) AS voos
FROM RAW_VRA v

LEFT JOIN RAW_EMPRESAS e 
   ON v.empresa_icao = e.icao
   
GROUP BY v.empresa_icao, e.razao_social
ORDER BY voos DESC
LIMIT 15;


-- P4: Os voos sem partida prevista são realizados ou cancelados?
SELECT situacao_voo,
       COUNT(*) AS voos,
       COUNT(partida_real) AS com_partida_real
FROM RAW_VRA
WHERE partida_prevista IS NULL
GROUP BY situacao_voo;


-- P5: Exemplos desses voos
SELECT empresa_icao, 
       numero_voo, 
       codigo_di, 
       codigo_tipo_linha,
       aeroporto_origem, 
       aeroporto_destino,
       partida_prevista, 
       partida_real, 
       chegada_prevista, 
       chegada_real, 
       situacao_voo
FROM RAW_VRA
WHERE partida_prevista IS NULL
LIMIT 20;


-- P6: O código DI muda nesses voos?
SELECT codigo_di,
       COUNT(*) AS voos,
       COUNT_IF(partida_prevista IS NULL) AS sem_prevista
FROM RAW_VRA
GROUP BY codigo_di
ORDER BY voos DESC;


-- P7: Tipos de linha
SELECT codigo_tipo_linha,
       COUNT(*) AS voos,
       COUNT_IF(partida_prevista IS NULL) AS sem_prevista
FROM RAW_VRA
GROUP BY codigo_tipo_linha
ORDER BY voos DESC;


-- P8: Quantos voos não tocam o Brasil (nem origem nem destino brasileiros)?
SELECT COUNT(*) AS voos_fora_do_brasil
FROM RAW_VRA v

LEFT JOIN RAW_AEROPORTOS o 
   ON v.aeroporto_origem  = o.icao_code
   
LEFT JOIN RAW_AEROPORTOS d 
   ON v.aeroporto_destino = d.icao_code
   
WHERE COALESCE(o.pais, '') <> 'BR'
AND COALESCE(d.pais, '') <> 'BR';


-- P9: Aeroportos dos voos que não foram encontrados no OurAirports
SELECT v.aeroporto_origem AS aeroporto, 
       COUNT(*) AS voos
FROM RAW_VRA v

LEFT JOIN RAW_AEROPORTOS a 
   ON v.aeroporto_origem = a.icao_code
   
WHERE a.icao_code IS NULL
GROUP BY 1
ORDER BY voos DESC;


-- P10: Como o SBCO aparece no OurAirports?
SELECT ident, 
       icao_code, 
       gps_code, 
       nome, 
       tipo, 
       municipio
FROM RAW_AEROPORTOS
WHERE 'SBCO' IN (ident, icao_code, gps_code);


-- P11: Quantos códigos continuam sem match usando icao_code, gps_code OU ident?
SELECT v.aeroporto_origem AS aeroporto, 
       COUNT(*) AS voos
FROM RAW_VRA v

WHERE NOT EXISTS (
  SELECT 1 FROM RAW_AEROPORTOS a
  WHERE v.aeroporto_origem IN (a.icao_code, a.gps_code, a.ident)
)
GROUP BY 1
ORDER BY voos DESC;


-- P12: Mesma pergunta da P11, com join por igualdade
WITH codigos AS (

  SELECT icao_code AS codigo FROM RAW_AEROPORTOS WHERE icao_code IS NOT NULL
  
  UNION
  
  SELECT gps_code FROM RAW_AEROPORTOS WHERE gps_code IS NOT NULL
  
  UNION
  
  SELECT ident FROM RAW_AEROPORTOS
)
SELECT v.aeroporto_origem AS aeroporto, 
       COUNT(*) AS voos
FROM RAW_VRA v

LEFT JOIN codigos c 
   ON v.aeroporto_origem = c.codigo
   
WHERE c.codigo IS NULL
GROUP BY 1
ORDER BY voos DESC;