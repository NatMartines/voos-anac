with calendario as (
    select * from {{ ref('stg_calendario') }}
)

select
    data,
    year(data)                        as ano,
    quarter(data)                     as trimestre,
    month(data)                       as mes,

    decode(month(data), 1,'Janeiro', 
                        2,'Fevereiro', 
                        3,'Março', 
                        4,'Abril',
                        5,'Maio', 
                        6,'Junho', 
                        7,'Julho', 
                        8,'Agosto', 
                        9,'Setembro',
                        10,'Outubro', 
                        11,'Novembro', 
                        12,'Dezembro') as nome_mes,

    date_trunc('month', data)         as inicio_mes,
    day(data)                         as dia,
    dayofweekiso(data)                as dia_semana_num,

    decode(dayofweekiso(data), 1,'Segunda', 
                               2,'Terça', 
                               3,'Quarta', 
                               4,'Quinta',
                               5,'Sexta', 
                               6,'Sábado', 
                               7,'Domingo') as dia_semana,
    dayofweekiso(data) in (6, 7)      as eh_fim_de_semana

from calendario