with voos as (
    select distinct empresa_icao 
    from {{ ref('int_voos_enriquecidos') }}
),

empresas as (
    select * from {{ ref('stg_empresas') }}
    where empresa_icao is not null
    qualify row_number() over (partition by empresa_icao order by id_empresa) = 1
)

select
    v.empresa_icao,
    e.empresa_iata,
    coalesce(e.razao_social, v.empresa_icao) as nome_companhia,
    e.pais_sede,
    e.razao_social is not null               as tem_cadastro_anac

from voos v

left join empresas e 
        on v.empresa_icao = e.empresa_icao