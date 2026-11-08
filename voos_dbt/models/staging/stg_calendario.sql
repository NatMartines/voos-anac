-- Calendário base: um dia por linha, de 31/12/2023 a 31/01/2025.
-- Começa em 31/12/2023 porque há voos de 2024 com partida prevista na virada do ano.
with dias as (
    select dateadd(day, row_number() over (order by seq4()) - 1, '2023-12-31'::date) as data
    from table(generator(rowcount => 398))
)

select data
from dias