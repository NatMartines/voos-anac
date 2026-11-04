with fonte as (
    select * from {{ source('raw', 'raw_vra') }}
),

convertido as (
    select
        upper(trim(empresa_icao))                as empresa_icao,
        trim(numero_voo)                         as numero_voo,
        trim(codigo_di)                          as codigo_di,
        trim(codigo_tipo_linha)                  as codigo_tipo_linha,
        upper(trim(aeroporto_origem))            as aeroporto_origem,
        upper(trim(aeroporto_destino))           as aeroporto_destino,
        try_to_timestamp(partida_prevista)       as partida_prevista,
        try_to_timestamp(partida_real)           as partida_real,
        try_to_timestamp(chegada_prevista)       as chegada_prevista,
        try_to_timestamp(chegada_real)           as chegada_real,
        upper(trim(situacao_voo))                as situacao_voo,
        nullif(trim(codigo_justificativa), '')   as codigo_justificativa,
        arquivo_origem,
        carregado_em
    from fonte
)

select
    *,
    datediff('minute', partida_prevista, partida_real) as atraso_partida_min,
    datediff('minute', chegada_prevista, chegada_real) as atraso_chegada_min,
    case
        when situacao_voo = 'REALIZADO'
         and datediff('minute', partida_prevista, partida_real) > 30
        then 1 else 0
    end as eh_atrasado,

    case 
        when situacao_voo = 'CANCELADO' 
        then 1 else 0 
    end as eh_cancelado
    
from convertido