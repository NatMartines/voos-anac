select *
from (
    select
        (select count(*)  from {{ ref('fct_voos') }})   as linhas_fato,
        (select sum(voos) from {{ ref('mart_rotas') }}) as soma_mart
)
where linhas_fato <> soma_mart