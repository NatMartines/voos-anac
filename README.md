# ✈️ Atrasos de Voos no Brasil · 2024

**Quais estados, companhias, meses e rotas mais atrasam no Brasil?**
Pipeline de dados completo com dados abertos da ANAC: ingestão em Python, modelagem com dbt no **Snowflake** e dashboard em **Streamlit in Snowflake**.

![Dashboard em funcionamento](docs/img/dashboard.gif)

---

## 📊 Principais resultados (voos regulares de passageiros, 2024)

| Indicador | Valor |
|---|---|
| Voos analisados | **939.483** |
| Saíram com mais de 30 min de atraso | **9,1%** |
| Atraso médio na partida | **6 min** |
| Cancelados | **3,5%** |

- **Fim de ano é o pior período:** novembro (13,3%) e dezembro (13,1%) concentram os maiores atrasos; maio (6,3%) é o mês mais pontual.
- **As grandes ficam abaixo da média:** LATAM Brasil (7,1%), Gol (7,3%) e Azul (8,7%), que juntas somam mais de 750 mil voos.
- **Companhias com poucos voos no Brasil atrasam mais:** American Airlines chega a 27,8% (de 4.079 voos). Por isso o dashboard mostra sempre o **% e a base** ("27,8% de 4.079 voos").
- **Rotas internacionais lideram o ranking**, com voos para e de Guarulhos no topo.

> Atraso = partida real mais de 30 minutos depois da prevista, o mesmo corte usado pela ANAC. Cancelados ficam fora da base do % de atrasos.

---

## Arquitetura

```
ANAC (VRA 2024) + OurAirports
        │  Python
        ▼
  Stage interno  ──►  COPY INTO  ──►  dbt (staging → intermediate → marts)  ──►  Streamlit
  (Snowflake)         (RAW)           testes + Elementary                        in Snowflake
```

| Camada | Ferramenta | O que faz |
|---|---|---|
| Ingestão | Python | Baixa os arquivos da ANAC e envia para o stage interno (autenticação por par de chaves) |
| Armazenamento | Snowflake (stage + RAW) | Recebe os arquivos e carrega com `COPY INTO`, guardando o nome do arquivo de origem |
| Processamento | Snowflake (warehouse XSMALL) | Motor SQL com auto-suspend e resource monitor para controlar o custo |
| Transformação | dbt Core + dbt-snowflake | Modelagem em camadas, testes e documentação |
| Qualidade | Elementary | Relatório de testes e lineage |
| Visualização | Streamlit in Snowflake | Dashboard interativo com mapa, rankings e filtros |

### Star Schema

- **Fato:** `fct_voos` (uma linha por voo, incremental)
- **Dimensões:** `dim_aeroporto`, `dim_companhia`, `dim_data`
- **Agregado:** `mart_rotas` (rota × companhia × mês, alimenta o dashboard)

![Lineage dos modelos dbt no Elementary](docs/img/lineage.png)

**Recursos do Snowflake explorados:** stage interno, `COPY INTO`, Time Travel, `UNDROP`, zero-copy clone, Query Profile, streams, tasks e dynamic tables.

---

## ✅ Qualidade e validação

- **Testes dbt:** `unique`, `not_null`, `relationships`, `accepted_values`, `unique_combination_of_columns`, `accepted_range` e testes singulares (ex.: soma do `mart_rotas` igual à fato).
- **Elementary:** relatório completo de testes e lineage em 👉 **[natmartines.github.io/voos-anac/elementary](https://natmartines.github.io/voos-anac/elementary/)**
- **Validação contra os números oficiais da ANAC** (janeiro de 2024, voos N + I):

| | Projeto | ANAC | Diferença |
|---|---|---|---|
| Etapas previstas | 79.022 | 78.448 | **0,7%** |
| % cancelados | 5,22% | 5,17% | +0,05 p.p. |

Nas rotas comparadas, as etapas previstas **batem exatamente**. Detalhes em [`analyses/validacao_anac.md`](analyses/validacao_anac.md).

---

## 🧭 Decisões principais

- **Recorte oficial:** só voos regulares de passageiros (tipos N + I), igual ao indicador da ANAC.
- **% sempre recalculado a partir das somas**, nunca pela média de percentuais.
- **Mínimo de voos nos rankings**, para amostras pequenas não aparecerem no topo por acaso.
- **Mapa por estado em vez de linhas de rotas:** testei arcos e linhas, mas centenas de rotas sobrepostas ficavam ilegíveis.
- **Filtros de Estado e Aeroporto pela origem do voo**, a mesma regra do mapa, para todos os gráficos contarem a mesma história.

Todas as decisões, dia a dia, estão em [`docs/decisoes.md`](docs/decisoes.md).

---

## 💰 Custo

O projeto inteiro custou **cerca de US$ 30** em créditos do período de teste do Snowflake (de US$ 400 disponíveis).

- Warehouse **XSMALL** com auto-suspend de 60 s e **resource monitor** limitando o consumo.
- O maior gasto veio do **app Streamlit aberto por horas** durante os ajustes de layout. Aprendizado: fechar o app quando não estiver usando e preferir cache (`st.cache_data`) para não consultar o warehouse a cada clique.

---

## 🤖 Uso de IA

Usei o **Claude** como par de programação, principalmente no código Python do dashboard, e transformei o que funcionou em **skills reutilizáveis**, versionadas no repositório:

| Skill | Para que serve |
|---|---|
| [`dashboard-streamlit-snowflake`](.claude/skills/dashboard-streamlit-snowflake/SKILL.md) | Padrão visual, regras de cálculo e armadilhas para criar dashboards em Streamlit in Snowflake |
| [`documentar-tabelas-dbt`](.claude/skills/documentar-tabelas-dbt/SKILL.md) | Gera a documentação dos modelos dbt em português (schema.yml, testes e dicionário) |

---

## ⚠️ Limitações

- Análise apenas de **2024**.
- O atraso é medido **na partida**, não na chegada.
- A ANAC parece contar como cancelados alguns voos que aparecem como realizados no VRA (diferença de ~1 p.p. em algumas rotas).
- O app do Streamlit in Snowflake **não é público**: fica dentro da conta Snowflake. Por isso o resultado está no GIF acima.

---

## 🛠️ Tecnologias

`Python` · `uv` · `Snowflake` · `dbt` · `dbt_utils` · `Elementary` · `Streamlit` · `Altair` · `pandas` · `Git`

---

## ▶️ Como rodar

1. Crie uma conta no Snowflake e rode os scripts de `sql/` (warehouse, resource monitor, database, schemas, role, stage e file formats).
2. Instale as dependências:
```bash
   uv sync
```
3. Configure o `.env` com a conta, o usuário e o caminho da chave privada (veja `ingestion/`).
4. Rode a ingestão (download dos CSVs da ANAC e envio para o stage) e o `COPY INTO`.
5. Construa os modelos e rode os testes:
```bash
   cd voos_dbt
   uv run dbt deps
   uv run dbt build
```
6. No Snowsight, crie um app Streamlit e envie os arquivos da pasta `app/`.

---

**Fonte dos dados:** [ANAC · Dados abertos](https://www.gov.br/anac/pt-br/acesso-a-informacao/dados-abertos) (VRA e percentuais de atrasos e cancelamentos) e [OurAirports](https://ourairports.com/data/).

Feito por **Natália Martines** · [GitHub](https://github.com/NatMartines)