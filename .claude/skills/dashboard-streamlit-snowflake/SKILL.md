---
name: dashboard-streamlit-snowflake
description: Cria ou ajusta dashboards em Streamlit in Snowflake (Python + Altair) no padrão visual e de cálculo do projeto Voos ANAC: tema escuro, cartões, mapa por estado, rankings e filtros.
---

# Dashboard em Streamlit in Snowflake

Guia para construir um dashboard analítico em **Streamlit in Snowflake** lendo uma tabela da camada MARTS (dbt), no mesmo padrão do projeto *Atrasos de Voos no Brasil* (ANAC 2024). Responda sempre em **português do Brasil**.

## Como trabalhar com a usuária

1. **Antes de mudar o visual, mostre uma imagem de sugestão** (mockup) com 2 ou 3 opções e uma recomendação. Só altere o código depois que ela escolher.
2. **Nunca mude dados ou regras de cálculo** quando o pedido for só de layout. Se uma mudança visual exigir mudar o cálculo, avise antes.
3. **Sempre entregue o `streamlit_app.py` inteiro**, pronto para colar, e diga em 1 ou 2 frases o que mudou. Termine com: "Clique em **Run**. 📸 Me manda o print."
4. Quando um ajuste fino depender da tela dela (alturas, margens), diga **qual número mudar e para que lado**.
5. Avise sobre custo: worksheets e app usam o **WH_VOOS** (coberto pelo resource monitor), e a aba do app deve ser **fechada** ao terminar, porque o compute pool consome créditos.

## Dados e regras de cálculo

- Conexão: `session = st.connection("snowflake").session()` e `session.table("DB.MARTS.TABELA").to_pandas()`.
- Colunas em minúsculo logo após ler: `df.columns = [c.lower() for c in df.columns]`.
- Converta contagens para `int64` antes de qualquer `groupby().sum()` (evita overflow e % negativos).
- **Percentuais sempre recalculados a partir das somas** (ex.: atrasados ÷ voos com horário previsto), nunca média de percentuais.
- Mostre a **base do cálculo** junto do % quando o volume varia muito ("27,8% de 4.079 voos").
- Use **mínimo de amostra** em rankings (ex.: 1.000 voos por companhia; 500 por rota sem filtro e 50 com filtro).
- Filtros que se referem a lugar (Estado, Aeroporto) usam **a mesma regra do mapa** (origem), para todos os gráficos contarem a mesma história.
- Recortes fixos do escopo (ano, tipo de voo) ficam **no código**, não como filtro.
- Formatação brasileira: `br_int` (39.483) e `br_pct` (9,1%).
- Nomes legíveis: dicionário de códigos → nomes comerciais (companhias, aeroportos) + função de limpeza para o resto (tira sufixos como S.A., LTDA, PLC; usa o nome entre parênteses; corta com "…").

## Desempenho

- `@st.cache_data(ttl=3600)` na leitura da mart: os filtros não consultam o warehouse a cada clique.
- Arquivos estáticos (geojson, logo) lidos com `Path(__file__).parent / "arquivo"` e guardados em cache.
- **Simplifique a geometria** do geojson uma vez só (pular pontos a menos de ~0,08° do último guardado e arredondar para 3 casas) e calcule o centro dos estados no cache. A cada filtro, só cores e textos mudam.

## Layout padrão (tema escuro)

- `st.set_page_config(layout="wide")` e `.streamlit/config.toml` com `base="dark"`, `primaryColor="#E8743B"`, `backgroundColor="#15181E"`, `secondaryBackgroundColor="#1D2128"`, `textColor="#E8E8E8"`.
- Paleta: laranja `#E8743B` (acima da média), azul `#2E6BD9` (abaixo da média), cartões `#20252D`, bordas `#2B313A`, texto secundário `#9AA0AA`.
- **Cabeçalho**: faixa com gradiente laranja (`#C2531C → #E8743B`), ícone ✈ num círculo branco, título e subtítulo com a fonte dos dados.
- **4 KPIs** com `st.metric`, em cartões com faixa laranja à esquerda (`border-left: 5px solid #E8743B`).
- **Gráficos em cartões** do mesmo estilo, **sem** a faixa laranja: `st.container(height=ALTURA_CARTAO, border=False, key="cartao_x")` + CSS em `[class*="st-key-cartao"]`.
- Grade 2 × 2 que cabe numa tela: mapa + companhias em cima; meses + rotas embaixo. Todos os cartões com a mesma altura.
- **Barra de filtros**: título "Filtros" com traço laranja alinhado ao cabeçalho, nomes dos filtros em negrito, borda laranja nas caixas (`[data-testid="stMultiSelect"] ... outline`), logo no rodapé (`margin-top: max(40px, calc(100vh - Npx))`).
- Margens: `padding-left` pequeno perto dos filtros e `padding-right` maior para o dashboard terminar antes do botão **Run** (bom para gravar GIF).

## Padrões de gráfico (Altair)

- **Ranking em barras**: barras horizontais, maior no topo, sem eixo X nem grade, cor laranja/azul pela média, % em negrito na ponta e "de X voos" em cinza; legenda das cores embaixo do gráfico.
- **Linha por mês**: pontos com o valor escrito acima, eixo Y discreto, sem título de eixo.
- **Mapa coroplético por estado** (`mark_geoshape` + `project("mercator")`): 4 faixas de cor com legenda na lateral; estados sem dados em cinza `#3A3F48`; rótulos com **halo** (texto preto com contorno branco desenhado por baixo); estados pequenos só no tooltip. Prefira isso a arcos/linhas de rotas, que ficam confusos.
- **Ranking de rotas em HTML**: posição numerada, "origem (cinza) → destino (negrito)", % à direita e barrinha embaixo; tooltip com a quantidade de voos.
- Sempre `background="transparent"` e `configure_view(strokeWidth=0)`.

## Armadilhas já resolvidas

- Arquivos extras (geojson, logo) precisam ser **enviados para a lista de arquivos do app** no Snowflake (+ → Upload), na mesma pasta do `streamlit_app.py`. Não vão no dbt nem em tabelas.
- O Windows esconde extensões: confira se o arquivo não virou `logo.png.png`.
- Seletores CSS do Streamlit mudam entre versões: se um estilo não aplicar, use `key=` nos containers ou `data-testid`, e peça um print do **Inspecionar** do navegador.
- Se o cartão ganhar barra de rolagem, o conteúdo passou da altura: ajuste a altura do gráfico ou tire o título do fluxo (posição absoluta), sem diminuir o que a usuária pediu para manter.
- O app do Streamlit in Snowflake **não é público**: para portfólio, use GIF no README e no LinkedIn.
- Depois de aprovar no Snowflake, copie o código para `app/streamlit_app.py` no repositório e faça o commit a partir da raiz do projeto.