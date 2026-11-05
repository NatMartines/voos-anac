{{ config(severity = 'warn') }}

select id_voo, codigo_tipo_linha, atraso_partida_min
from {{ ref('fct_voos') }}
where atraso_partida_min > 1440