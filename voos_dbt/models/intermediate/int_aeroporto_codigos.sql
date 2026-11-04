with aeroportos as (
    select * from {{ ref('stg_aeroportos') }}
),

codigos as (
    select icao_code as codigo, 
           id_aeroporto, 
           tipo_aeroporto, 
           1 as prioridade
    from aeroportos 
    where icao_code is not null

    union all

    select gps_code, 
           id_aeroporto, 
           tipo_aeroporto, 
           2
    from aeroportos 
    where gps_code is not null

    union all

    select ident, 
           id_aeroporto, 
           tipo_aeroporto, 
           3
    from aeroportos 
    where ident is not null
)

select codigo, 
       id_aeroporto, 
       prioridade
from codigos
qualify row_number() over (
    partition by codigo
    order by prioridade,
             case 
                 when tipo_aeroporto = 'closed' 
                 then 1 else 0 
             end,
             id_aeroporto
) = 1