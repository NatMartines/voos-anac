{{ config(
    materialized = 'incremental',
    unique_key   = 'id_voo'
) }}

with voos as (
    select * from {{ ref('int_voos_enriquecidos') }}
    {% if is_incremental() %}
    where carregado_em > (select max(carregado_em) from {{ this }})
    {% endif %}
)

select
    id_voo,
    data_voo,
    empresa_icao,
    numero_voo,
    codigo_di,
    codigo_tipo_linha,
    id_aeroporto_origem,
    id_aeroporto_destino,
    aeroporto_origem   as codigo_origem_anac,
    aeroporto_destino  as codigo_destino_anac,
    partida_prevista,
    partida_real,
    chegada_prevista,
    chegada_real,
    situacao_voo,
    codigo_justificativa,
    atraso_partida_min,
    atraso_chegada_min,
    eh_atrasado,
    eh_cancelado,

    case 
       when partida_prevista is not null 
       then 1 else 0 
    end as tem_partida_prevista,
    
    arquivo_origem,
    carregado_em
from voos
qualify row_number() over (partition by id_voo order by carregado_em desc) = 1