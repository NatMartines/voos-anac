-- Dia 9: automação nativa do Snowflake
-- Tudo foi testado uma vez e deixado SUSPENSO para não consumir créditos.

-- 1. Permissões (ACCOUNTADMIN)
USE ROLE ACCOUNTADMIN;
GRANT EXECUTE TASK ON ACCOUNT TO ROLE VOOS_DEV;
GRANT CREATE TASK   ON SCHEMA VOOS.RAW   TO ROLE VOOS_DEV;
GRANT CREATE STREAM ON SCHEMA VOOS.RAW   TO ROLE VOOS_DEV;
GRANT CREATE DYNAMIC TABLE ON SCHEMA VOOS.MARTS TO ROLE VOOS_DEV;
USE ROLE VOOS_DEV;

-- 2. Stream: registra as linhas novas de uma tabela (CDC)
--    Testado numa cópia: 5 linhas inseridas apareceram como INSERT
--    e o stream voltou a zero depois de consumido.
CREATE OR REPLACE TABLE VOOS.RAW.RAW_VRA_TESTE CLONE VOOS.RAW.RAW_VRA;
CREATE OR REPLACE STREAM VOOS.RAW.STR_VRA_TESTE ON TABLE VOOS.RAW.RAW_VRA_TESTE;
INSERT INTO VOOS.RAW.RAW_VRA_TESTE SELECT * FROM VOOS.RAW.RAW_VRA LIMIT 5;
SELECT METADATA$ACTION, METADATA$ISUPDATE, empresa_icao, numero_voo
FROM VOOS.RAW.STR_VRA_TESTE;

-- 3. Task: carga mensal do VRA (dia 5, 6h de Brasília)
--    Fica suspensa. Para ligar: ALTER TASK VOOS.RAW.TSK_CARGA_VRA RESUME;
CREATE OR REPLACE TASK VOOS.RAW.TSK_CARGA_VRA
  WAREHOUSE = WH_VOOS
  SCHEDULE  = 'USING CRON 0 6 5 * * America/Sao_Paulo'
  COMMENT   = 'Carga mensal do VRA: dia 5 de cada mês às 6h'
AS
  COPY INTO VOOS.RAW.RAW_VRA
  FROM (
    SELECT $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
           METADATA$FILENAME, CURRENT_TIMESTAMP()
    FROM @VOOS.RAW.STG_VOOS/vra/
  )
  FILE_FORMAT = (FORMAT_NAME = 'VOOS.RAW.FF_VRA');

EXECUTE TASK VOOS.RAW.TSK_CARGA_VRA;   -- teste manual: SUCCEEDED, 0 arquivos novos

SELECT name, state, scheduled_time, completed_time, error_message
FROM TABLE(VOOS.INFORMATION_SCHEMA.TASK_HISTORY(TASK_NAME => 'TSK_CARGA_VRA'))
ORDER BY scheduled_time DESC;

-- 4. Dynamic Table: resumo mensal mantido pelo próprio Snowflake
CREATE OR REPLACE DYNAMIC TABLE VOOS.MARTS.DT_RESUMO_MENSAL
  TARGET_LAG = '1 day'
  WAREHOUSE  = WH_VOOS
AS
SELECT
  DATE_TRUNC('month', data_voo)                                     AS mes,
  COUNT(*)                                                          AS voos,
  SUM(eh_cancelado)                                                 AS cancelados,
  COUNT_IF(situacao_voo = 'REALIZADO' AND tem_partida_prevista = 1) AS voos_com_previsao,
  SUM(eh_atrasado)                                                  AS atrasados,
  ROUND(100 * atrasados / NULLIF(voos_com_previsao, 0), 2)          AS pct_atrasados
FROM VOOS.MARTS.FCT_VOOS
GROUP BY 1;

ALTER DYNAMIC TABLE VOOS.MARTS.DT_RESUMO_MENSAL SUSPEND;

-- 5. Limpeza dos objetos de teste
DROP STREAM IF EXISTS VOOS.RAW.STR_VRA_TESTE;
DROP TABLE  IF EXISTS VOOS.RAW.RAW_VRA_TESTE;