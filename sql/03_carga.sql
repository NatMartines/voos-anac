-- Dia 4: tabelas RAW e carga com COPY INTO

USE ROLE VOOS_DEV;
USE WAREHOUSE WH_VOOS;
USE SCHEMA VOOS.RAW;

-- Voos (VRA): tudo como texto, mais a origem e a hora da carga
CREATE TABLE RAW_VRA (
  empresa_icao         VARCHAR,
  numero_voo           VARCHAR,
  codigo_di            VARCHAR,
  codigo_tipo_linha    VARCHAR,
  aeroporto_origem     VARCHAR,
  aeroporto_destino    VARCHAR,
  partida_prevista     VARCHAR,
  partida_real         VARCHAR,
  chegada_prevista     VARCHAR,
  chegada_real         VARCHAR,
  situacao_voo         VARCHAR,
  codigo_justificativa VARCHAR,
  arquivo_origem       VARCHAR,
  carregado_em         TIMESTAMP_NTZ
);

-- Rodar de novo não duplica: o Snowflake pula arquivos já carregados (histórico de 64 dias)
COPY INTO RAW_VRA
FROM (
  SELECT $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
         METADATA$FILENAME, CURRENT_TIMESTAMP()
  FROM @STG_VOOS/vra/
)
FILE_FORMAT = (FORMAT_NAME = 'FF_VRA');

-- Aeroportos (OurAirports): só as colunas usadas
CREATE TABLE RAW_AEROPORTOS (
  id VARCHAR, ident VARCHAR, tipo VARCHAR, nome VARCHAR,
  latitude VARCHAR, longitude VARCHAR, pais VARCHAR, regiao VARCHAR,
  municipio VARCHAR, icao_code VARCHAR, iata_code VARCHAR, gps_code VARCHAR,
  arquivo_origem VARCHAR, carregado_em TIMESTAMP_NTZ
);

COPY INTO RAW_AEROPORTOS
FROM (
  SELECT $1, $2, $3, $4, $5, $6, $9, $10, $11, $13, $14, $15,
         METADATA$FILENAME, CURRENT_TIMESTAMP()
  FROM @STG_VOOS/referencias/airports/
)
FILE_FORMAT = (FORMAT_NAME = 'FF_AIRPORTS');

-- Empresas aéreas (ANAC): sem dados pessoais (LGPD)
CREATE TABLE RAW_EMPRESAS (
  razao_social VARCHAR, icao VARCHAR, iata VARCHAR, pais_sede VARCHAR,
  atividades_aereas VARCHAR, id_empresa VARCHAR,
  arquivo_origem VARCHAR, carregado_em TIMESTAMP_NTZ
);

COPY INTO RAW_EMPRESAS
FROM (
  SELECT $1, $2, $3, $5, $14, $17,
         METADATA$FILENAME, CURRENT_TIMESTAMP()
  FROM @STG_VOOS/referencias/empresas/
)
FILE_FORMAT = (FORMAT_NAME = 'FF_EMPRESAS');

-- Resultado da carga (29/10/2026):
-- RAW_VRA        987.024 voos (12 arquivos, 0 erros)
-- RAW_AEROPORTOS  86.293 aeroportos
-- RAW_EMPRESAS       822 empresas