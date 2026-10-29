# Decisões do projeto

## Pergunta de negócio
Quais rotas, aeroportos e companhias mais atrasam no Brasil, e quanto?

## Escopo
- Voos regulares (base VRA da ANAC), competências de 2024.
- Arquivos baixados em 28/10/2026 (a ANAC republica os arquivos; a data do download fica registrada).

## Regras
- **Atraso:** partida real mais de 30 minutos depois da partida prevista, mesmo corte usado pela ANAC nas faixas de pontualidade.
- **Cancelados:** contados à parte, porque não têm partida real.
- **Fuso:** todos os horários estão em horário de Brasília.

## Sobre o arquivo
- O CSV tem 12 colunas, diferente do dicionário publicado (19). Vale o arquivo.
- Linha 1 é um aviso ("Atualizado em ..."), linha 2 é o cabeçalho.
- Separador `;`, valores entre aspas, UTF-8 com BOM.
- Nulos vêm como o texto "null".

## Limitações
- A justificativa do atraso deixou de ser exigida em abril de 2020: o projeto mostra onde e quanto os voos atrasam, mas não por quê.
- O arquivo não traz nomes de companhias nem coordenadas de aeroportos; essas informações vêm de bases externas.

## Fontes
| Fonte | Arquivo | Uso |
|---|---|---|
| ANAC – Voo Regular Ativo (VRA) | VRA_2024<mês>.csv (12 arquivos) | Voos, horários e situação |
| OurAirports (domínio público) | airports.csv | Nome, cidade e coordenadas dos aeroportos |
| ANAC – Empresas Aéreas Outorgadas | empresas_aereas_20241230.csv (foto de 30/12/2024) | Nome e país das companhias |

## Formatos dos arquivos
| | VRA | airports | empresas_aereas |
|---|---|---|---|
| Separador | `;` | `,` | `;` |
| Cabeçalho | linha 2 | linha 1 | linha 1 |
| Aspas | sim | sim | não |
| Encoding | UTF-8 com BOM | UTF-8 | UTF-8 com BOM |
| Nulos | "null" | vazio | vazio |

## Joins
- Voo → companhia: `ICAO Empresa Aérea` = `ICAO` (empresas_aereas)
- Voo → aeroporto: `ICAO Aeródromo Origem/Destino` = `icao_code` (airports); se vazio, usar `ident`

## Privacidade
- O cadastro de empresas tem dados pessoais (representante legal, telefone, e-mail, endereço).
  Só são carregadas as colunas usadas: Razão Social, ICAO, IATA, País Sede e Atividades Aéreas.

## Validação
- Comparar com a base oficial da ANAC "Percentuais de atrasos e de cancelamentos de cada etapa de voo".

## Descobertas da exploração (Dia 5)

- **Situação dos voos (2024):** 945.244 realizados (95,77%) e 41.780 cancelados (4,23%).
- **Voos sem partida prevista:** 30.942 voos realizados não têm `partida_prevista`. Quase todos têm código DI diferente de `0`.
  **Regra:** o atraso só é calculado para voos com partida prevista (DI `0`, 948.589 voos).
- **Virada do ano:** 13 voos do arquivo de dezembro têm partida em janeiro de 2025. Eles ficam no dado, e a análise usa a data prevista.
- **Etapas no exterior:** há trechos entre aeroportos estrangeiros (ex.: EHAM → ELLX), operados por cargueiras como CLX e FDX.
- **Tipo de linha:** N 796.011 · I 143.485 · G 24.710 · C 22.817. O significado oficial dos códigos ainda precisa ser confirmado.
- **Cruzamento com aeroportos:** 32 códigos não batem com `icao_code`. Alguns aeroportos (ex.: SBCO) guardam o código em `ident` ou `gps_code`.
  **Regra:** criar uma tabela de códigos (icao_code + gps_code + ident) e fazer o join por igualdade. Só **OKBK** (2 voos) fica sem correspondência.
- **Performance:** um join com `IN (col1, col2, col3)` levou 4 min 46 s, e o Query Profile mostrou "Inefficient join condition".
  Reescrito com UNION + join por igualdade, levou **1,7 s**.

## Recursos do Snowflake testados

- **Zero-copy clone:** a cópia da RAW_VRA ficou pronta na hora e sem custo de armazenamento.
- **Time Travel:** `BEFORE (STATEMENT => id)` recuperou a tabela como estava antes de um DELETE.
- **UNDROP:** recupera a tabela como estava no momento do DROP.