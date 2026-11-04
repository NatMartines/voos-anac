with voos as (select * from {{ ref('fct_voos') }}),
     aero as (select * from {{ ref('dim_aeroporto') }}),
     cia  as (select * from {{ ref('dim_companhia') }})

select
    date_trunc('month', v.data_voo)        as mes,
    v.empresa_icao,
    c.nome_companhia,
    o.codigo_icao                          as origem,
    o.nome_aeroporto                       as nome_origem,
    o.municipio                            as cidade_origem,
    o.uf                                   as uf_origem,
    o.pais                                 as pais_origem,
    o.latitude                             as lat_origem,
    o.longitude                            as lon_origem,
    d.codigo_icao                          as destino,
    d.nome_aeroporto                       as nome_destino,
    d.municipio                            as cidade_destino,
    d.uf                                   as uf_destino,
    d.pais                                 as pais_destino,
    d.latitude                             as lat_destino,
    d.longitude                            as lon_destino,
    (o.eh_brasil or d.eh_brasil)           as envolve_brasil,
    count(*)                               as voos,
    sum(v.eh_cancelado)                    as cancelados,

    sum(case 
            when v.situacao_voo = 'REALIZADO'
            and v.tem_partida_prevista = 1 
            then 1 else 0 
        end) as voos_com_previsao,

    sum(v.eh_atrasado)                                          as atrasados,
    round(100 * atrasados / nullif(voos_com_previsao, 0), 2)    as pct_atrasados,
    round(100 * cancelados / voos, 2)                           as pct_cancelados,

    round(avg(case 
                 when v.situacao_voo = 'REALIZADO'
                 then v.atraso_partida_min 
              end), 1) as atraso_medio_min

from voos v

left join aero o 
        on v.id_aeroporto_origem  = o.id_aeroporto

left join aero d 
        on v.id_aeroporto_destino = d.id_aeroporto

left join cia  c 
        on v.empresa_icao        = c.empresa_icao
        
group by all