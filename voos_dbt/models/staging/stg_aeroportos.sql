select
    try_to_number(id)                    as id_aeroporto,
    trim(ident)                          as ident,
    tipo                                 as tipo_aeroporto,
    nome                                 as nome_aeroporto,
    try_to_double(latitude)              as latitude,
    try_to_double(longitude)             as longitude,
    pais                                 as pais,
    regiao                               as regiao,

    case when pais = 'BR'
         then split_part(regiao, '-', 2) 
    end as uf,
    municipio,
    upper(trim(icao_code))               as icao_code,
    upper(trim(iata_code))               as iata_code,
    upper(trim(gps_code))                as gps_code
    
from {{ source('raw', 'raw_aeroportos') }}