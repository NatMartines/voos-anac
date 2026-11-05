{{ config(severity = 'warn') }}

select id_voo, codigo_tipo_linha, partida_real, chegada_real
from {{ ref('fct_voos') }}
where situacao_voo = 'REALIZADO'
  and chegada_real < partida_real