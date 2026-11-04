with voos as (
    select * from {{ ref('stg_vra') }}
),

codigos as (
    select * from {{ ref('int_aeroporto_codigos') }}
),

de_para as (
    select * from {{ ref('de_para_aeroportos') }}
)

select
    {{ dbt_utils.generate_surrogate_key([
        'v.empresa_icao', 
        'v.numero_voo', 
        'v.codigo_di',
        'v.aeroporto_origem', 
        'v.aeroporto_destino',
        'v.partida_prevista', 
        'v.partida_real', 
        'v.situacao_voo'
    ]) }}                                              as id_voo,
    coalesce(v.partida_prevista, v.partida_real)::date as data_voo,
    o.id_aeroporto                                     as id_aeroporto_origem,
    d.id_aeroporto                                     as id_aeroporto_destino,
    v.*
from voos v

left join de_para dpo 
        on v.aeroporto_origem  = dpo.codigo_anac

left join de_para dpd 
        on v.aeroporto_destino = dpd.codigo_anac

left join codigos o   
        on coalesce(dpo.codigo_atual, v.aeroporto_origem)  = o.codigo

left join codigos d   
        on coalesce(dpd.codigo_atual, v.aeroporto_destino) = d.codigo