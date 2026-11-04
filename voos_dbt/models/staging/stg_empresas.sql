select
    trim(id_empresa)          as id_empresa,
    trim(razao_social)        as razao_social,
    upper(trim(icao))         as empresa_icao,
    upper(trim(iata))         as empresa_iata,
    trim(pais_sede)           as pais_sede,
    trim(atividades_aereas)   as atividades_aereas
from {{ source('raw', 'raw_empresas') }}