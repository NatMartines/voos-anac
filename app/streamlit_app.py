import base64
import html
import json
import unicodedata
from pathlib import Path

import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Atrasos de voos no Brasil", page_icon="✈️", layout="wide")

# Tema escuro: tudo cabe numa tela
st.markdown(
    """
    <style>
      .stApp {background: #15181E;}
      [data-testid="stSidebar"] {background: #1D2128; border-right: 1px solid #2B313A;}
      [data-testid="stSidebar"] label, [data-testid="stSidebar"] label p {font-weight: 700 !important;}

      /* Barra de filtros alinhada ao topo: o botão « vai para o canto e o conteúdo sobe.
         Para alinhar melhor com o cabeçalho laranja, ajuste o 26px. */
      [data-testid="stSidebarHeader"] {
          position: absolute !important; top: 0; right: 0;
          height: auto !important; padding: 6px 8px !important; z-index: 5;
      }
      [data-testid="stSidebarUserContent"] {padding-top: 26px !important;}

      /* Título "Filtros" com traço laranja (mesma altura do cabeçalho laranja) */
      .titulo-filtros {height: 60px; display: flex; flex-direction: column; justify-content: center;}
      .titulo-filtros .texto {font-size: 1.3rem; font-weight: 700; color: #F2F2F2; line-height: 1.2;}
      .titulo-filtros .traco {width: 36px; height: 3px; background: #E8743B; border-radius: 2px; margin-top: 6px;}

      /* Bordinha laranja em todos os filtros (a caixa, sem o nome do filtro) */
      [data-testid="stSidebar"] [data-testid="stMultiSelect"] > div:not([data-testid="stWidgetLabel"]):not(:has(label)),
      [data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
          outline: 1px solid #E8743B !important;
          outline-offset: -1px;
          border-radius: 8px !important;
      }

      /* Logo no rodapé da barra de filtros.
         Tamanho: mude o 240. Posição: aumente o 680 para subir, diminua para descer. */
      .logo-rodape {
          margin-top: max(40px, calc(100vh - 680px));
          text-align: center;
      }
      .logo-rodape img {width: 240px; max-width: 100%; display: inline-block;}

      /* Margens do dashboard: pouco espaço à esquerda (perto dos filtros)
         e espaço à direita para o dashboard terminar antes do botão Run do Snowflake */
      .block-container {padding-top: 0.6rem !important; padding-bottom: 0 !important;
                        padding-left: 1.5rem !important; padding-right: 7rem !important;}
      h4 {font-size: 0.95rem !important; margin: 0 0 0.4rem 0 !important; padding: 0 !important;
          color: #F2F2F2 !important;}

      /* Cabeçalho */
      .cabecalho {
          display: flex; align-items: center; gap: 12px;
          background: linear-gradient(90deg, #C2531C, #E8743B);
          border-radius: 8px; padding: 8px 18px; margin-bottom: 0.9rem;
      }
      .cabecalho .icone {
          width: 34px; height: 34px; border-radius: 50%; background: #ffffff; color: #E8743B;
          display: flex; align-items: center; justify-content: center; font-size: 17px;
      }
      .cabecalho .titulo {font-size: 1.3rem; font-weight: 700; color: #ffffff; line-height: 1.2;}
      .cabecalho .subtitulo {font-size: 0.75rem; color: #FDE3D3;}

      /* Cartões dos indicadores: com a faixa laranja */
      [data-testid="stMetric"] {
          background: #20252D;
          border: 1px solid #2B313A;
          border-left: 5px solid #E8743B;
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.35);
          padding: 4px 16px;
      }
      [data-testid="stMetricLabel"] p {font-size: 0.7rem !important; color: #9AA0AA !important;
                                       text-transform: uppercase; letter-spacing: 0.03em;}
      [data-testid="stMetricValue"] {font-size: 1.45rem !important; font-weight: 700; color: #ffffff;}

      /* Cartões dos gráficos: mesmo fundo, borda e sombra, sem a faixa laranja */
      [class*="st-key-cartao"] {
          background: #20252D !important;
          border: 1px solid #2B313A !important;
          border-radius: 8px !important;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.35) !important;
          padding: 12px 16px !important;
      }

      /* Cartão do mapa: o título fica por cima (não ocupa espaço), o mapa usa a altura toda
         e não aparece barra de rolagem. Para descer/subir o título, mude o "top: 12px". */
      .st-key-cartao_mapa {
          position: relative !important;
          gap: 0 !important;
          padding-top: 2px !important; padding-bottom: 0 !important;
          overflow: hidden !important;
      }
      .titulo-mapa {
          position: absolute; top: 12px; left: 0; z-index: 3;
          font-size: 0.95rem; font-weight: 700; color: #F2F2F2; white-space: nowrap;
      }

      /* Legenda das cores (gráfico de companhias) */
      .legenda-cores {display: flex; justify-content: center; gap: 22px;
                      font-size: 0.78rem; color: #C9CDD3; margin-top: -6px;}
      .legenda-cores i {display: inline-block; width: 11px; height: 11px; border-radius: 2px;
                        margin-right: 6px; vertical-align: middle;}

      /* Ranking de rotas */
      .rk {display: flex; gap: 10px; align-items: center; height: 27px; font-size: 0.8rem; color: #E8E8E8;}
      .rk .pos {width: 20px; height: 20px; border-radius: 50%; flex: none; color: #fff;
                display: flex; align-items: center; justify-content: center;
                font-size: 0.68rem; font-weight: 700;}
      .rk .corpo {flex: 1; min-width: 0;}
      .rk .linha {display: flex; justify-content: space-between; gap: 8px;}
      .rk .nome {white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}
      .rk .de {color: #9AA0AA;}
      .rk .seta {color: #E8743B; font-weight: 700; margin: 0 3px;}
      .rk .para {font-weight: 700;}
      .rk .pct {font-weight: 700; flex: none;}
      .rk .trilho {height: 4px; background: #2B313A; border-radius: 2px; margin-top: 2px;}
      .rk .trilho div {height: 100%; border-radius: 2px;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Conexão e dados ----------
conn = st.connection("snowflake")
session = conn.session()

CONTAGENS = ["voos", "cancelados", "voos_com_previsao", "atrasados"]

NOMES_COMPANHIAS = {
    "AZU": "Azul", "GLO": "Gol", "TAM": "LATAM Brasil", "ACN": "Azul Conecta",
    "PTB": "Voepass", "ARG": "Aerolíneas Argentinas", "TAP": "TAP Air Portugal",
    "CMP": "Copa Airlines", "AAL": "American Airlines", "LAN": "LATAM Chile",
    "LPE": "LATAM Peru", "SKU": "Sky Airline", "AFR": "Air France", "KLM": "KLM",
    "IBE": "Iberia", "DAL": "Delta Air Lines", "UAL": "United Airlines",
}

# Nome exibido de alguns aeroportos: em português, ou com o aeroporto quando a cidade tem mais de um
NOMES_AEROPORTOS = {
    "SBGR": "São Paulo (Guarulhos)", "SBSP": "São Paulo (Congonhas)",
    "SBGL": "Rio de Janeiro (Galeão)", "SBRJ": "Rio de Janeiro (Santos Dumont)",
    "SBJR": "Rio de Janeiro (Jacarepaguá)", "SBCF": "Belo Horizonte (Confins)",
    "SBBH": "Belo Horizonte (Pampulha)",
    "SUMU": "Montevidéu", "LPPT": "Lisboa", "SAEZ": "Buenos Aires (Ezeiza)",
    "SABE": "Buenos Aires (Aeroparque)", "SCEL": "Santiago", "KMIA": "Miami",
    "KJFK": "Nova York", "LFPG": "Paris", "EGLL": "Londres", "LEMD": "Madri",
}

COR_ACIMA = "#E8743B"   # laranja: acima da média
COR_ABAIXO = "#2E6BD9"  # azul: abaixo da média
COR_TEXTO = "#E8E8E8"   # texto claro sobre o fundo escuro
COR_CINZA = "#9AA0AA"   # texto secundário ("de X voos")

ALTURA_CARTAO = 355     # todos os cartões de gráfico com a mesma altura
ALTURA = 275            # altura dos gráficos dentro dos cartões
ALTURA_MAPA = 350       # o mapa ocupa todo o espaço do cartão

# Faixas do mapa: (limite superior, cor, texto da legenda)
FAIXAS = [
    (5,   "#FDD8B5", "Até 5%"),
    (7,   "#FDAE6B", "5% a 7%"),
    (9,   "#F16913", "7% a 9%"),
    (999, "#A63603", "Acima de 9%"),
]

UFS = {
    "acre": "AC", "alagoas": "AL", "amapa": "AP", "amazonas": "AM", "bahia": "BA",
    "ceara": "CE", "distrito federal": "DF", "espirito santo": "ES", "goias": "GO",
    "maranhao": "MA", "mato grosso": "MT", "mato grosso do sul": "MS", "minas gerais": "MG",
    "para": "PA", "paraiba": "PB", "parana": "PR", "pernambuco": "PE", "piaui": "PI",
    "rio de janeiro": "RJ", "rio grande do norte": "RN", "rio grande do sul": "RS",
    "rondonia": "RO", "roraima": "RR", "santa catarina": "SC", "sao paulo": "SP",
    "sergipe": "SE", "tocantins": "TO",
}
# Estados pequenos demais para escrever dentro (aparecem no tooltip)
UFS_PEQUENOS = {"RN", "PB", "PE", "AL", "SE", "DF", "ES", "RJ"}

# Simplificação do contorno dos estados: guarda um ponto a cada ~8 km (invisível no tamanho do mapa)
TOLERANCIA_MAPA = 0.08

PASTA_APP = Path(__file__).parent
ARQUIVO_LOGO = PASTA_APP / "logo.png"


def sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto or "")
                   if unicodedata.category(c) != "Mn").lower().strip()


@st.cache_data(ttl=3600)
def carregar_rotas() -> pd.DataFrame:
    df = session.table("VOOS.MARTS.MART_ROTAS").to_pandas()
    df.columns = [c.lower() for c in df.columns]
    df["mes"] = pd.to_datetime(df["mes"])
    # Contagens em inteiro grande: evita overflow no groupby().sum()
    df[CONTAGENS] = df[CONTAGENS].astype("int64")
    df["atraso_medio_min"] = df["atraso_medio_min"].astype("float64")
    df["companhia"] = df["empresa_icao"].map(NOMES_COMPANHIAS).fillna(
        df["nome_companhia"].str.title().str.slice(0, 22)
    )
    df["mes_abrev"] = df["nome_mes"].str.slice(0, 3)
    df["nome_origem"] = (df["origem"].map(NOMES_AEROPORTOS)
                         .fillna(df["cidade_origem"]).fillna(df["origem"]))
    df["nome_destino"] = (df["destino"].map(NOMES_AEROPORTOS)
                          .fillna(df["cidade_destino"]).fillna(df["destino"]))
    return df


def simplificar_anel(anel: list, tol: float = TOLERANCIA_MAPA) -> list:
    """Reduz os pontos de um contorno: pula pontos muito próximos do último guardado."""
    if len(anel) <= 8:
        return [[round(p[0], 3), round(p[1], 3)] for p in anel]
    mantidos = [anel[0]]
    for pt in anel[1:-1]:
        if abs(pt[0] - mantidos[-1][0]) + abs(pt[1] - mantidos[-1][1]) >= tol:
            mantidos.append(pt)
    mantidos.append(anel[-1])                        # fecha o contorno no mesmo ponto do início
    if len(mantidos) < 4:                            # contorno pequeno demais: mantém o original
        mantidos = anel
    return [[round(p[0], 3), round(p[1], 3)] for p in mantidos]


def centro(geometria: dict) -> tuple:
    """Centro aproximado do maior polígono do estado (para escrever o texto)."""
    poligonos = geometria["coordinates"] if geometria["type"] == "MultiPolygon" else [geometria["coordinates"]]
    maior = max(poligonos, key=lambda p: len(p[0]))[0]
    lons = [pt[0] for pt in maior]
    lats = [pt[1] for pt in maior]
    return (min(lons) + max(lons)) / 2, (min(lats) + max(lats)) / 2


@st.cache_data
def preparar_estados() -> list:
    """Roda uma vez só: lê o geojson, simplifica o contorno e calcula o centro de cada estado."""
    with open(PASTA_APP / "brasil_estados.geojson", encoding="utf-8") as f:
        geo = json.load(f)
    estados = []
    for f in geo["features"]:
        props = f["properties"]
        geom = f["geometry"]
        uf = props.get("sigla") or UFS.get(sem_acento(props.get("name", "")))
        lon, lat = centro(geom)                      # centro calculado no contorno original
        if geom["type"] == "MultiPolygon":
            coords = [[simplificar_anel(anel) for anel in poligono] for poligono in geom["coordinates"]]
        else:
            coords = [simplificar_anel(anel) for anel in geom["coordinates"]]
        estados.append({
            "uf": uf, "nome": props.get("name", uf), "lon": lon, "lat": lat,
            "geometry": {"type": geom["type"], "coordinates": coords},
        })
    return estados


@st.cache_data
def carregar_logo():
    """Logo em base64 para usar no HTML. Se o arquivo não existir, devolve None."""
    if not ARQUIVO_LOGO.exists():
        return None
    return base64.b64encode(ARQUIVO_LOGO.read_bytes()).decode()


def br_int(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def br_pct(p) -> str:
    return "–" if p is None or pd.isna(p) else f"{p:.1f}%".replace(".", ",")


def faixa(p):
    if p is None:
        return None
    for i, (limite, _, _) in enumerate(FAIXAS):
        if p <= limite:
            return i
    return len(FAIXAS) - 1


def metricas(d: pd.DataFrame) -> dict:
    voos = d["voos"].sum()
    com_prev = d["voos_com_previsao"].sum()
    atrasados = d["atrasados"].sum()
    cancelados = d["cancelados"].sum()
    peso = d["voos_com_previsao"].where(d["atraso_medio_min"].notna(), 0)
    atraso_medio = (d["atraso_medio_min"].fillna(0) * peso).sum() / peso.sum() if peso.sum() else None
    return {
        "voos": voos,
        "pct_atrasados": 100 * atrasados / com_prev if com_prev else None,
        "pct_cancelados": 100 * cancelados / voos if voos else None,
        "atraso_medio": atraso_medio,
    }


def lista_aeroportos(d: pd.DataFrame, campo_nome: str, campo_pais: str) -> list:
    """Aeroportos brasileiros primeiro, do mais movimentado para o menos."""
    return (
        d.groupby([campo_nome, campo_pais], dropna=False)["voos"].sum().reset_index()
        .assign(estrangeiro=lambda x: x[campo_pais] != "BR")
        .sort_values(["estrangeiro", "voos"], ascending=[True, False])[campo_nome]
        .drop_duplicates().tolist()
    )


def barras_ranking(dados: pd.DataFrame, campo_nome: str, media: float, titulo_tooltip: str,
                   altura: int = ALTURA):
    """Barras horizontais: maior no topo, laranja/azul pela média.
    Na ponta de cada barra: o % em negrito e, em cinza, "de X voos" (a base do cálculo)."""
    dados = dados.copy()
    dados["rotulo"] = dados["pct"].map(br_pct)
    dados["base_txt"] = "de " + dados["voos_com_previsao"].map(br_int) + " voos"
    dados["cor"] = (dados["pct"] > media).map({True: COR_ACIMA, False: COR_ABAIXO})
    ordem = dados[campo_nome].tolist()
    limite_x = dados["pct"].max() * 1.6           # folga para o texto "27,8% de 2.400 voos" na ponta
    base = alt.Chart(dados).encode(
        y=alt.Y(f"{campo_nome}:N", sort=ordem, title=None,
                axis=alt.Axis(labelLimit=220, domain=False, ticks=False, labelColor=COR_TEXTO,
                              labelFontSize=12)),
        x=alt.X("pct:Q", axis=None, scale=alt.Scale(domain=[0, limite_x])),
    )
    barras = base.mark_bar(cornerRadiusEnd=3).encode(
        color=alt.Color("cor:N", scale=None, legend=None),
        tooltip=[alt.Tooltip(campo_nome, title=titulo_tooltip),
                 alt.Tooltip("rotulo", title="Atrasados"),
                 alt.Tooltip("voos_com_previsao:Q", title="Voos", format=",")],
    )
    # % em negrito logo depois da barra
    pct_txt = base.mark_text(align="left", dx=4, fontSize=11, fontWeight="bold",
                             color=COR_TEXTO).encode(text="rotulo")
    # "de X voos" em cinza, depois do %: o espaço muda se o % tem 1 ou 2 dígitos antes da vírgula
    base_2dig = (base.transform_filter(alt.datum.pct >= 10)
                 .mark_text(align="left", dx=42, fontSize=11, color=COR_CINZA).encode(text="base_txt"))
    base_1dig = (base.transform_filter(alt.datum.pct < 10)
                 .mark_text(align="left", dx=36, fontSize=11, color=COR_CINZA).encode(text="base_txt"))
    return ((barras + pct_txt + base_2dig + base_1dig)
            .properties(height=altura, background="transparent").configure_view(strokeWidth=0))


def ranking_rotas(dados: pd.DataFrame, media: float) -> str:
    """Ranking em HTML: posição, origem → destino, % e uma barrinha embaixo."""
    maximo = dados["pct"].max()
    linhas = []
    for i, r in enumerate(dados.itertuples(), start=1):
        cor = COR_ACIMA if r.pct > media else COR_ABAIXO
        largura = 100 * r.pct / maximo
        dica = f"{r.nome_origem} → {r.nome_destino}: {br_int(r.voos_com_previsao)} voos"
        linhas.append(
            f"<div class='rk' title='{html.escape(dica, quote=True)}'>"
            f"<div class='pos' style='background:{cor}'>{i}</div>"
            f"<div class='corpo'><div class='linha'>"
            f"<span class='nome'><span class='de'>{html.escape(r.nome_origem)}</span>"
            f"<span class='seta'>→</span><span class='para'>{html.escape(r.nome_destino)}</span></span>"
            f"<span class='pct'>{br_pct(r.pct)}</span></div>"
            f"<div class='trilho'><div style='width:{largura:.1f}%;background:{cor}'></div></div>"
            f"</div></div>"
        )
    return "".join(linhas)


df = carregar_rotas()
df = df[df["ano"] == 2024]                          # só o ano da análise
df = df[df["tipo_linha"].isin(["N", "I"])]          # só voos de passageiros (recorte oficial da ANAC)

# ---------- Filtros ----------
st.sidebar.markdown(
    "<div class='titulo-filtros'><div class='texto'>Filtros</div><div class='traco'></div></div>",
    unsafe_allow_html=True,
)

meses = df[["mes", "nome_mes"]].drop_duplicates().sort_values("mes")["nome_mes"].tolist()
mes_sel = st.sidebar.multiselect("Mês", meses, placeholder="Todos")
if mes_sel:
    df = df[df["nome_mes"].isin(mes_sel)]

cias = df.groupby("companhia")["voos"].sum().sort_values(ascending=False).index.tolist()
cia_sel = st.sidebar.multiselect("Companhia", cias, placeholder="Todas")
if cia_sel:
    df = df[df["companhia"].isin(cia_sel)]

# Estado: voos que SAEM do estado escolhido (mesma regra do filtro Aeroporto)
ufs_disponiveis = sorted(df["uf_origem"].dropna().unique())
uf_sel = st.sidebar.multiselect("Estado", ufs_disponiveis, placeholder="Todos")
if uf_sel:
    df = df[df["uf_origem"].isin(uf_sel)]

# Aeroporto: de onde os voos saem
origem_sel = st.sidebar.multiselect(
    "Aeroporto", lista_aeroportos(df, "nome_origem", "pais_origem"), placeholder="Todos"
)
if origem_sel:
    df = df[df["nome_origem"].isin(origem_sel)]

algum_filtro = bool(mes_sel or cia_sel or uf_sel or origem_sel)

# ---------- Logo no rodapé da barra de filtros ----------
logo = carregar_logo()
if logo:
    st.sidebar.markdown(
        f"<div class='logo-rodape'><img src='data:image/png;base64,{logo}' alt='Logo'></div>",
        unsafe_allow_html=True,
    )

# ---------- Cabeçalho e indicadores ----------
st.markdown(
    """
    <div class="cabecalho">
      <div class="icone">✈</div>
      <div>
        <div class="titulo">Atrasos de Voos no Brasil</div>
        <div class="subtitulo">Pontualidade dos voos regulares de passageiros · 2024 · Fonte: ANAC</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if df.empty:
    st.warning("Nenhum voo para os filtros escolhidos.")
    st.stop()

m = metricas(df)
media_pct = m["pct_atrasados"]
k1, k2, k3, k4 = st.columns(4)
k1.metric("Voos", br_int(m["voos"]))
k2.metric("Saíram com mais de 30 min de atraso", br_pct(media_pct))
k3.metric("Atraso médio na partida", "–" if m["atraso_medio"] is None else f"{m['atraso_medio']:.0f} min")
k4.metric("Cancelados", br_pct(m["pct_cancelados"]))

# ---------- Linha 1: mapa + companhias ----------
lin1_a, lin1_b = st.columns(2)

with lin1_a.container(height=ALTURA_CARTAO, border=False, key="cartao_mapa"):
    # Título por cima do cartão: não ocupa espaço, o mapa fica do tamanho todo
    st.markdown("<div class='titulo-mapa'>Em quais estados os voos atrasam mais</div>",
                unsafe_allow_html=True)

    por_uf = (
        df[df["pais_origem"] == "BR"]
        .groupby("uf_origem")[["voos", "atrasados", "voos_com_previsao"]].sum()
    )
    por_uf["pct"] = 100 * por_uf["atrasados"] / por_uf["voos_com_previsao"].where(por_uf["voos_com_previsao"] > 0)

    # A cada filtro, só as cores e os textos mudam: o contorno já vem pronto da memória
    features, rotulos = [], []
    for e in preparar_estados():
        uf = e["uf"]
        linha = por_uf.loc[uf] if uf in por_uf.index else None
        pct = None if linha is None or pd.isna(linha["pct"]) else round(float(linha["pct"]), 1)
        voos = 0 if linha is None else int(linha["voos"])
        i_faixa = faixa(pct)
        cor = "#3A3F48" if i_faixa is None else FAIXAS[i_faixa][1]
        features.append({
            "type": "Feature", "geometry": e["geometry"],
            "properties": {"uf": uf, "nome": e["nome"], "cor": cor,
                           "pct_txt": br_pct(pct), "voos_txt": br_int(voos)},
        })
        if uf not in UFS_PEQUENOS:
            rotulos.append({"lon": e["lon"], "lat": e["lat"], "sigla": uf,
                            "pct_txt": br_pct(pct) if pct is not None else ""})

    estados_pintados = (
        alt.Chart(alt.Data(values=features))
        .mark_geoshape(stroke="#20252D", strokeWidth=1)
        .encode(
            color=alt.Color("properties.cor:N", scale=None, legend=None),
            tooltip=[alt.Tooltip("properties.nome:N", title="Estado"),
                     alt.Tooltip("properties.pct_txt:N", title="Atrasaram (+30 min)"),
                     alt.Tooltip("properties.voos_txt:N", title="Voos que saíram")],
        )
    )

    # Escritas do mapa: contorno branco por baixo + letra preta por cima (legível em qualquer cor)
    base_textos = alt.Chart(pd.DataFrame(rotulos)).encode(longitude="lon:Q", latitude="lat:Q")
    contorno = dict(color="white", stroke="white", strokeWidth=3, strokeJoin="round")
    sigla_fundo = base_textos.mark_text(fontSize=10, fontWeight="bold", dy=-6, **contorno).encode(text="sigla:N")
    sigla = base_textos.mark_text(fontSize=10, fontWeight="bold", dy=-6, color="black").encode(text="sigla:N")
    pct_fundo = base_textos.mark_text(fontSize=10, fontWeight="bold", dy=7, **contorno).encode(text="pct_txt:N")
    pct_texto = base_textos.mark_text(fontSize=10, fontWeight="bold", dy=7, color="black").encode(text="pct_txt:N")

    mapa = (
        (estados_pintados + sigla_fundo + pct_fundo + sigla + pct_texto)
        .project("mercator")
        .properties(height=ALTURA_MAPA, background="transparent", padding=0)
        .configure_view(strokeWidth=0)
    )

    # Legenda na lateral, mapa ao lado
    col_leg, col_mapa = st.columns([1, 4])
    with col_leg:
        st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
        for _, cor, nome in reversed(FAIXAS):          # faixa mais escura em cima
            st.markdown(
                f"<div style='font-size:0.8rem;color:#C9CDD3;margin:8px 0;white-space:nowrap'>"
                f"<span style='display:inline-block;width:12px;height:12px;background:{cor};"
                f"border-radius:2px;margin-right:6px;vertical-align:middle'></span>{nome}</div>",
                unsafe_allow_html=True,
            )
    col_mapa.altair_chart(mapa, use_container_width=True)

with lin1_b.container(height=ALTURA_CARTAO, border=False, key="cartao_companhias"):
    st.markdown("#### Quais companhias atrasam mais")
    min_voos = 1000
    por_cia = (
        df.groupby("companhia", as_index=False)[["atrasados", "voos_com_previsao"]].sum()
        .query("voos_com_previsao >= @min_voos")
        .sort_values("voos_com_previsao", ascending=False)
        .head(10)
        .assign(pct=lambda x: 100 * x["atrasados"] / x["voos_com_previsao"])
        .sort_values("pct", ascending=False)
    )
    if por_cia.empty:
        st.info(f"Nenhuma companhia com pelo menos {br_int(min_voos)} voos nesse filtro.")
    else:
        # Gráfico um pouco mais baixo para caber a legenda embaixo
        st.altair_chart(barras_ranking(por_cia, "companhia", media_pct, "Companhia", altura=ALTURA - 25),
                        use_container_width=True)
        st.markdown(
            f"<div class='legenda-cores'>"
            f"<span><i style='background:{COR_ACIMA}'></i>Acima da média ({br_pct(media_pct)})</span>"
            f"<span><i style='background:{COR_ABAIXO}'></i>Abaixo da média</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

# ---------- Linha 2: meses + rotas ----------
lin2_a, lin2_b = st.columns(2)

with lin2_a.container(height=ALTURA_CARTAO, border=False, key="cartao_meses"):
    st.markdown("#### Em que meses os voos atrasam mais")
    por_mes = (
        df.groupby(["mes", "mes_abrev", "nome_mes"], as_index=False)[["atrasados", "voos_com_previsao"]].sum()
        .assign(pct=lambda x: 100 * x["atrasados"] / x["voos_com_previsao"])
        .sort_values("mes")
    )
    por_mes["rotulo"] = por_mes["pct"].map(br_pct)
    ordem_meses = por_mes["mes_abrev"].tolist()

    base_mes = alt.Chart(por_mes).encode(
        x=alt.X("mes_abrev:N", sort=ordem_meses, title=None,
                axis=alt.Axis(labelAngle=0, labelColor=COR_TEXTO, domain=False, ticks=False,
                              labelFontSize=12)),
        y=alt.Y("pct:Q", title=None, scale=alt.Scale(zero=True),
                axis=alt.Axis(tickCount=4, labelColor="#9AA0AA", gridColor="#2B313A",
                              domain=False, ticks=False)),
    )
    linha = base_mes.mark_line(point=alt.OverlayMarkDef(size=60), color="#5B8DEF", strokeWidth=2.5).encode(
        tooltip=[alt.Tooltip("nome_mes", title="Mês"),
                 alt.Tooltip("rotulo", title="Atrasados"),
                 alt.Tooltip("voos_com_previsao:Q", title="Voos", format=",")],
    )
    valores = base_mes.mark_text(dy=-13, fontSize=11, color=COR_TEXTO).encode(text="rotulo")
    st.altair_chart(
        (linha + valores).properties(height=ALTURA, background="transparent").configure_view(strokeWidth=0),
        use_container_width=True,
    )

with lin2_b.container(height=ALTURA_CARTAO, border=False, key="cartao_rotas"):
    st.markdown("#### Rotas em que os voos atrasam mais")
    # Sem filtro: só rotas com pelo menos 500 voos no ano. Com filtro, o mínimo cai para 50.
    min_voos_rota = 50 if algum_filtro else 500
    por_rota = (
        df.groupby(["nome_origem", "nome_destino"], as_index=False)[["atrasados", "voos_com_previsao"]].sum()
        .query("voos_com_previsao >= @min_voos_rota")
        .assign(pct=lambda x: 100 * x["atrasados"] / x["voos_com_previsao"])
        .sort_values("pct", ascending=False)
        .head(10)
    )
    if por_rota.empty:
        st.info(f"Nenhuma rota com pelo menos {br_int(min_voos_rota)} voos nesse filtro.")
    else:
        st.markdown(ranking_rotas(por_rota, media_pct), unsafe_allow_html=True)