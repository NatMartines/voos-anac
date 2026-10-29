-- Dia 3: stage interno e formatos de arquivo

USE ROLE VOOS_DEV;
USE WAREHOUSE WH_VOOS;
USE SCHEMA VOOS.RAW;

-- Voos da ANAC: ; como separador, linha 1 é aviso e linha 2 é cabeçalho, "null" vira nulo
CREATE FILE FORMAT FF_VRA
  TYPE = CSV
  FIELD_DELIMITER = ';'
  SKIP_HEADER = 2
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  NULL_IF = ('null', '')
  ENCODING = 'UTF8';

-- Aeroportos (OurAirports): vírgula, cabeçalho na linha 1
CREATE FILE FORMAT FF_AIRPORTS
  TYPE = CSV
  FIELD_DELIMITER = ','
  SKIP_HEADER = 1
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  NULL_IF = ('')
  ENCODING = 'UTF8';

-- Empresas aéreas da ANAC: ; sem aspas, cabeçalho na linha 1
CREATE FILE FORMAT FF_EMPRESAS
  TYPE = CSV
  FIELD_DELIMITER = ';'
  SKIP_HEADER = 1
  NULL_IF = ('')
  ENCODING = 'UTF8';

-- Stage interno: a "pasta" dentro do Snowflake
CREATE STAGE STG_VOOS;