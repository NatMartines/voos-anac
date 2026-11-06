# Validação com os números oficiais da ANAC

**Fonte:** ANAC, *Percentuais de atrasos e cancelamentos* (Resolução 218), janeiro de 2024, Anexos II (companhia + rota) e III (rota).
Arquivos em `sistemas.anac.gov.br/dadosabertos/Voos e operações aéreas/Percentuais de atrasos e cancelamentos/2024/01 - janeiro/`.

**Como a ANAC calcula:** % de cancelamentos sobre as etapas previstas; % de atrasos acima de 30 min sobre as etapas **realizadas** (cancelados ficam fora). É a mesma regra do projeto.

## Resultado por rota (janeiro de 2024)

| Rota | Etapas (projeto / ANAC) | % cancel. (projeto / ANAC) | % atraso > 30 min (projeto / ANAC) |
|---|---|---|---|
| SBSP→SBRJ | 1.602 / 1.602 | 6,87 / 6,87 | 8,98 / 8,24 |
| SBRJ→SBSP | 1.586 / 1.586 | 7,00 / 7,76 | 6,44 / 6,43 |
| SBSP→SBBR | 640 / 640 | 1,25 / 1,88 | — / 14,33 |
| SBBR→SBSP | 638 / 638 | 3,45 / 4,08 | 6,66 / 6,54 |
| SBSP→SBCF | 686 / 686 | 3,35 / 3,94 | — / 14,42 |
| SBCF→SBSP | 689 / 689 | 4,06 / 5,22 | 11,50 / 14,40 |

**As etapas previstas batem exatamente em todas as rotas.**

## Resultado total (janeiro de 2024)

| | Projeto | ANAC | Diferença |
|---|---|---|---|
| Etapas previstas (todos os tipos) | 82.348 | 78.448 | +3.900 |
| Etapas previstas (só tipos N + I) | 79.022 | 78.448 | **+574 (0,7%)** |
| % cancelados | 5,22% | 5,17% | +0,05 p.p. |
| % atrasos > 30 min | 11,50% | 11,14% | +0,36 p.p. |

## Conclusões

- O indicador da ANAC considera só os voos regulares **N** (doméstico) e **I** (internacional). Os tipos **C** e **G** (3.326 etapas em janeiro) ficam fora.
- Considerando só N + I, a diferença é de **0,7%** nas etapas previstas.
- Os percentuais diferem em até cerca de 1 p.p. na maioria das rotas. O cancelamento do projeto tende a ficar um pouco abaixo do da ANAC, o que sugere que a ANAC conta como cancelados alguns voos que no VRA aparecem como realizados (hipótese, não confirmada).
- O **Anexo I** (por número de voo) soma 177.213 etapas, mais que o dobro dos Anexos II e III. Ex.: Guarulhos→Recife tem 2.515 no Anexo I contra 513 no Anexo III. Ele segue outra metodologia e não foi usado.