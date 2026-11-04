with usados as (
    select id_aeroporto_origem  as id_aeroporto 
    from {{ ref('int_voos_enriquecidos') }}

    union

    select id_aeroporto_destino 
    from {{ ref('int_voos_enriquecidos') }}
)

select
    a.id_aeroporto,
    coalesce(a.icao_code, a.gps_code, a.ident) as codigo_icao,
    a.iata_code                                as codigo_iata,
    a.nome_aeroporto,
    a.tipo_aeroporto,
    a.municipio,
    a.uf,
    a.pais,
    a.pais = 'BR'                              as eh_brasil,
    a.latitude,
    a.longitude

from {{ ref('stg_aeroportos') }} a

inner join usados u 
         on a.id_aeroporto = u.id_aeroporto