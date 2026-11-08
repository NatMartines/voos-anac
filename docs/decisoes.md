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

## Staging (Dia 6)

- **Conversão de datas:** `TRY_TO_TIMESTAMP` converteu 100% das datas (zero falhas nas 4 colunas).
- **Atraso:** 87.456 voos atrasados acima de 30 min, 9,57% dos 914.302 voos realizados com partida prevista. Atraso médio de 7,6 min.
- **Valores extremos:** 1.620 voos saíram mais de 1 h adiantados e 214 mais de 1 dia atrasados (0,2% do total).
  Os adiantados se concentram nos tipos G (1,7% do tipo) e I (0,57%). Nos domésticos (N) são só 0,04%.
  Hipóteses: fuso horário em voos internacionais e reprogramação em voos de carga. Não confirmado.
  **Decisão:** manter na staging e criar um teste com `severity: warn` no Dia 8.

  ## Intermediate e marts (Dia 7)

- **Tabela de códigos (`int_aeroporto_codigos`):** junta icao_code, gps_code e ident, com um único aeroporto por código (prioridade icao > gps > ident; aeroporto fechado perde o desempate). Evita duplicar voos no join.
- **De-para de códigos antigos (seed `de_para_aeroportos`):** OKBK→OKKK (Kuwait), SEQU→SEQM (Quito), GQNN→GQNO (Nouakchott). Resolveu os 18 voos sem aeroporto. Todos os 987.024 voos ficaram com origem e destino.
- **Duplicata na fonte:** 1 voo (IBE 6829, LEMD, 01/09/2024) aparece duas vezes no arquivo da ANAC. Removido na `fct_voos` com `qualify row_number()` por `id_voo`. A fato tem 987.023 linhas.
- **`data_voo`:** data prevista e, se ela não existir, data real. Assim os 30.942 voos sem previsão também entram por data.
- **`fct_voos` incremental:** `unique_key = id_voo`, com filtro por `carregado_em`. Nas próximas cargas, só os voos novos são processados.
- **`mart_rotas`:** 29.746 linhas (mês × companhia × origem × destino). Soma de voos igual à fato.
  Percentuais devem ser recalculados a partir das somas, nunca pela média dos percentuais.
- **Primeiro achado:** nas rotas mais movimentadas, os voos que saem de Congonhas (SBSP) atrasam mais que os que chegam lá (ex.: SP→Brasília 10,54% x Brasília→SP 5,67%).

## Qualidade (Dia 8)

- **39 testes no dbt:** 37 passam e 2 são alertas conhecidos (`severity: warn`).
  - Genéricos: unique/not_null nas chaves, relationships da fato para as 3 dimensões, accepted_values na situação, combinação única e percentuais entre 0 e 100 no mart_rotas.
  - Singulares: soma do mart igual à fato; voos adiantados mais de 1 h (1.620, warn); atrasados mais de 1 dia (214, warn); chegada antes da partida.
- **Chegada antes da partida: zero casos.** Partida e chegada estão no mesmo padrão de horário, inclusive nos voos internacionais. Isso enfraquece a hipótese de fuso horário para os voos adiantados.
- **`dim_data` começa em 31/12/2023:** o teste de relationships encontrou 2 voos internacionais que partiram em 31/12/2023 por volta das 23h e chegaram em 01/01/2024 (CMP Z0216 Panamá→Galeão e ACA 0096 Montreal→Guarulhos). Sem partida prevista, a `data_voo` usa a data real.

## Automação no Snowflake (Dia 9)

- **Stream:** testado numa cópia da RAW_VRA. Registrou as 5 linhas inseridas (`METADATA$ACTION = INSERT`) e voltou a zero depois de consumido. É a base para cargas incrementais (CDC).
- **Task `TSK_CARGA_VRA`:** COPY INTO mensal (dia 5, 6h de Brasília). Testada com `EXECUTE TASK`: SUCCEEDED, sem duplicar linhas, porque o COPY INTO pula arquivos já carregados. **Fica suspensa** para não consumir créditos.
- **Dynamic Table `DT_RESUMO_MENSAL`:** resumo mensal com `TARGET_LAG = 1 day` e refresh INCREMENTAL. **Fica suspensa.**
  Comparação com o dbt: a Dynamic Table é mais simples para um agregado que só depende de uma tabela; o dbt é melhor para o projeto inteiro, porque traz testes, documentação e lineage.
- **Sazonalidade:** % de atrasos acima de 30 min é maior em novembro (13,81%) e dezembro (13,80%) e menor em maio (6,89%).
- **Atenção:** a Dynamic Table lê a `fct_voos`. Um `dbt build --full-refresh` recria a fato e pode exigir recriar a Dynamic Table.

## Dia 11 — Dashboard final (Streamlit in Snowflake)

**Mapa: rotas → estados (coroplético)**
- Testei linhas, arcos 3D e bolhas com pydeck para mostrar as rotas, mas ficaram confusos de ler.
- Troquei por um mapa coroplético por estado (Altair `geoshape`), pintado pelo % de voos que saíram com mais de 30 min de atraso, em 4 faixas de cor.
- Rótulos com contorno branco (halo) para ficarem legíveis em qualquer cor.

**Gráficos**
- Companhias: barras com o % e a base do cálculo ("27,8% de 4.079 voos"), em laranja/azul conforme a média.
- Meses: linha com o % por mês.
- Rotas: ranking "origem → destino" (mín. 500 voos sem filtro; 50 com filtro) para evitar rotas com poucos voos no topo.

**Filtros**
- Recorte fixo no código: ano de 2024 e só voos regulares de passageiros (N + I), igual ao indicador oficial da ANAC.
- Filtros: Mês, Companhia, Estado e Aeroporto.
- Estado e Aeroporto filtram pela **origem** do voo, a mesma regra do mapa, para todos os gráficos contarem a mesma história.

**Regras de cálculo**
- Os % são sempre recalculados a partir das somas (atrasados ÷ voos com horário previsto), nunca pela média de percentuais.
- Os cancelados ficam fora da base do % de atrasados.

**Desempenho**
- Dados em cache por 1 hora (`st.cache_data(ttl=3600)`): os filtros não consultam o warehouse a cada clique.
- Contorno dos estados simplificado e guardado em memória: o mapa ficou bem mais leve ao filtrar.

**Visual**
- Tema escuro, cabeçalho laranja, cartões com borda e sombra, tudo em uma tela só.

**Atualização dos dados**
- Os dados não são em tempo real: a fonte (ANAC) é mensal. Atualização em lote (dbt) é suficiente.
- Para tempo real, seria preciso uma fonte em streaming, Snowpipe/Snowpipe Streaming, dynamic tables e auto-refresh no app, com custo de warehouse bem maior.