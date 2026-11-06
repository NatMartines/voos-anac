import json
import unicodedata
from pathlib import Path

import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Atrasos de voos no Brasil", page_icon="✈️", layout="wide")

# ---------- Conexão e dados ----------
conn = st.connection("snowflake")
session = conn.session()

CONTAGENS = ["voos", "cancelados", "voos_com_previsao", "atrasados"]

NOMES_CURTOS = {
    "AZU": "Azul", "GLO": "Gol", "TAM": "LATAM Brasil", "ACN": "Azul Conecta",
    "PTB": "Voepass", "ARG": "Aerolíneas Argentinas", "TAP": "TAP", "CMP": "Copa",
    "AAL": "American", "LAN": "LATAM Chile", "LPE": "LATAM Peru", "SKU": "Sky",
    "AFR": "Air France", "KLM": "KLM", "IBE": "Iberia", "DAL": "Delta", "UAL": "United",
}

COR_ACIMA = "#E8743B"   # laranja: acima da média
COR_ABAIXO = "#2E6BD9"  # azul: abaixo da média

# Faixas do mapa: (limite superior, cor, texto da legenda)
FAIXAS = [
    (5,   "#FDD8B5", "Até 5%"),
    (7,   "#FDAE6B", "De 5% a 7%"),
    (9,   "#F16913", "De 7% a 9%"),
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
    df["companhia"] = df["empresa_icao"].map(NOMES_CURTOS).fillna(
        df["nome_companhia"].str.title().str.slice(0, 22)
    )
    df["mes_abrev"] = df["nome_mes"].str.slice(0, 3)
    return df


@st.cache_data
def carregar_estados() -> dict:
    caminho = Path(__file__).parent / "brasil_estados.geojson"
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


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


def centro(geometria: dict) -> tuple:
    """Centro aproximado do maior polígono do estado (para escrever o texto)."""
    poligonos = geometria["coordinates"] if geometria["type"] == "MultiPolygon" else [geometria["coordinates"]]
    maior = max(poligonos, key=lambda p: len(p[0]))[0]
    lons = [pt[0] for pt in maior]
    lats = [pt[1] for pt in maior]
    return (min(lons) + max(lons)) / 2, (min(lats) + max(lats)) / 2


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


df = carregar_rotas()
df = df[df["ano"] == 2024]          # só o ano da análise

# ---------- Filtros ----------
st.sidebar.header("Filtros")

so_passageiros = st.sidebar.toggle(
    "Só voos de passageiros", value=True,
    help="Tipos de linha N (doméstico) e I (internacional), o mesmo recorte do indicador oficial "
         "da ANAC. Desligue para incluir os voos de carga (tipos C e G).",
)
if so_passageiros:
    df = df[df["tipo_linha"].isin(["N", "I"])]

abrangencia = st.sidebar.radio("Abrangência", ["Todos", "Domésticos", "Internacionais"], horizontal=True)
domestico = (df["pais_origem"] == "BR") & (df["pais_destino"] == "BR")
if abrangencia == "Domésticos":
    df = df[domestico]
elif abrangencia == "Internacionais":
    df = df[~domestico]

meses = df[["mes", "nome_mes"]].drop_duplicates().sort_values("mes")["nome_mes"].tolist()
mes_sel = st.sidebar.multiselect("Mês", meses, placeholder="Todos")
if mes_sel:
    df = df[df["nome_mes"].isin(mes_sel)]

cias = df.groupby("companhia")["voos"].sum().sort_values(ascending=False).index.tolist()
cia_sel = st.sidebar.multiselect("Companhia", cias, placeholder="Todas")
if cia_sel:
    df = df[df["companhia"].isin(cia_sel)]

# ---------- Cabeçalho e cards ----------
st.title("✈️ Atrasos de voos no Brasil · 2024")
st.caption("Um voo é considerado atrasado quando sai mais de 30 minutos depois do horário previsto "
           "(mesmo corte da ANAC). Voos cancelados não entram no % de atrasos.")

if df.empty:
    st.warning("Nenhum voo para os filtros escolhidos.")
    st.stop()

m = metricas(df)
media_pct = m["pct_atrasados"]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Voos", br_int(m["voos"]))
c2.metric("Saíram com mais de 30 min de atraso", br_pct(media_pct))
c3.metric("Atraso médio na partida", "–" if m["atraso_medio"] is None else f"{m['atraso_medio']:.0f} min")
c4.metric("Cancelados", br_pct(m["pct_cancelados"]))

st.divider()

# ---------- Mapa do Brasil por estado ----------
st.subheader("Em quais estados os voos atrasam mais")

por_uf = (
    df[df["pais_origem"] == "BR"]
    .groupby("uf_origem")[["voos", "atrasados", "voos_com_previsao"]].sum()
)
por_uf["pct"] = 100 * por_uf["atrasados"] / por_uf["voos_com_previsao"].where(por_uf["voos_com_previsao"] > 0)

estados = carregar_estados()
features, rotulos = [], []
for f in estados["features"]:
    props = f["properties"]
    uf = props.get("sigla") or UFS.get(sem_acento(props.get("name", "")))
    linha = por_uf.loc[uf] if uf in por_uf.index else None
    pct = None if linha is None or pd.isna(linha["pct"]) else round(float(linha["pct"]), 1)
    voos = 0 if linha is None else int(linha["voos"])
    i_faixa = faixa(pct)
    cor = "#e6e6e6" if i_faixa is None else FAIXAS[i_faixa][1]
    features.append({
        "type": "Feature", "geometry": f["geometry"],
        "properties": {"uf": uf, "nome": props.get("name", uf), "cor": cor,
                       "pct_txt": br_pct(pct), "voos_txt": br_int(voos)},
    })
    if uf not in UFS_PEQUENOS:
        lon, lat = centro(f["geometry"])
        cor_texto = "white" if i_faixa is not None and i_faixa >= 2 else "#333333"
        rotulos.append({"lon": lon, "lat": lat, "sigla": uf,
                        "pct_txt": br_pct(pct) if pct is not None else "",
                        "cor_texto": cor_texto})

estados_pintados = (
    alt.Chart(alt.Data(values=features))
    .mark_geoshape(stroke="white", strokeWidth=1)
    .encode(
        color=alt.Color("properties.cor:N", scale=None, legend=None),
        tooltip=[alt.Tooltip("properties.nome:N", title="Estado"),
                 alt.Tooltip("properties.pct_txt:N", title="Saíram com mais de 30 min de atraso"),
                 alt.Tooltip("properties.voos_txt:N", title="Voos que saíram")],
    )
)
base_textos = alt.Chart(pd.DataFrame(rotulos)).encode(
    longitude="lon:Q", latitude="lat:Q",
    color=alt.Color("cor_texto:N", scale=None, legend=None),
)
siglas = base_textos.mark_text(fontSize=11, fontWeight="bold", dy=-7).encode(text="sigla:N")
percentuais = base_textos.mark_text(fontSize=10, dy=7).encode(text="pct_txt:N")

mapa = (estados_pintados + siglas + percentuais).project("mercator").properties(height=600)

col_leg, col_mapa = st.columns([1, 2])

with col_leg:
    st.markdown("**% de voos que saíram com mais de 30 min de atraso**")
    st.caption(f"Média do filtro: {br_pct(media_pct)}")
    for i in reversed(range(len(FAIXAS))):          # faixa mais escura primeiro
        _, cor, nome = FAIXAS[i]
        st.markdown(
            f"<div style='margin:10px 0'>"
            f"<span style='display:inline-block;width:16px;height:16px;background:{cor};"
            f"border-radius:3px;margin-right:8px;vertical-align:middle'></span>"
            f"<b>{nome}</b></div>",
            unsafe_allow_html=True,
        )
    st.caption("Estados em cinza não tiveram voos no filtro. "
               "Passe o mouse sobre um estado para ver os números.")

col_mapa.altair_chart(mapa, use_container_width=True)

st.divider()

# ---------- Gráficos ----------
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Em que meses os voos atrasam mais")
    por_mes = (
        df.groupby(["mes", "mes_abrev", "nome_mes"], as_index=False)[["atrasados", "voos_com_previsao"]].sum()
        .assign(pct=lambda x: 100 * x["atrasados"] / x["voos_com_previsao"])
        .sort_values("mes")
    )
    por_mes["rotulo"] = por_mes["pct"].map(br_pct)
    ordem_meses = por_mes["mes_abrev"].tolist()

    base_mes = alt.Chart(por_mes).encode(
        x=alt.X("mes_abrev:N", sort=ordem_meses, title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("pct:Q", title="% de voos atrasados", scale=alt.Scale(zero=True)),
    )
    linha = base_mes.mark_line(point=True, color=COR_ABAIXO).encode(
        tooltip=[alt.Tooltip("nome_mes", title="Mês"),
                 alt.Tooltip("rotulo", title="Atrasados"),
                 alt.Tooltip("voos_com_previsao:Q", title="Voos", format=",")],
    )
    valores = base_mes.mark_text(dy=-12, fontSize=11).encode(text="rotulo")
    st.altair_chart((linha + valores).properties(height=340), use_container_width=True)

    if len(por_mes) > 1:
        pior_mes = por_mes.loc[por_mes["pct"].idxmax()]
        melhor_mes = por_mes.loc[por_mes["pct"].idxmin()]
        st.caption(f"Mais atrasos em **{pior_mes['nome_mes']}** ({br_pct(pior_mes['pct'])}) e "
                   f"menos em **{melhor_mes['nome_mes']}** ({br_pct(melhor_mes['pct'])}).")

with col_b:
    st.subheader("Quais companhias atrasam mais")
    min_voos = 1000
    por_cia = (
        df.groupby("companhia", as_index=False)[["atrasados", "voos_com_previsao"]].sum()
        .query("voos_com_previsao >= @min_voos")
        .sort_values("voos_com_previsao", ascending=False)
        .head(10)
        .assign(pct=lambda x: 100 * x["atrasados"] / x["voos_com_previsao"])
        .sort_values("pct", ascending=False)          # maior atraso no topo
    )
    if por_cia.empty:
        st.info(f"Nenhuma companhia com pelo menos {br_int(min_voos)} voos nesse filtro.")
    else:
        acima = f"Acima da média ({br_pct(media_pct)})"
        abaixo = f"Abaixo da média ({br_pct(media_pct)})"
        por_cia["rotulo"] = por_cia["pct"].map(br_pct)
        por_cia["situacao"] = (por_cia["pct"] > media_pct).map({True: acima, False: abaixo})
        ordem_cias = por_cia["companhia"].tolist()

        base = alt.Chart(por_cia).encode(
            y=alt.Y("companhia:N", sort=ordem_cias, title=None, axis=alt.Axis(labelLimit=200)),
            x=alt.X("pct:Q", title="% de voos que saíram com mais de 30 min de atraso"),
        )
        barras = base.mark_bar().encode(
            color=alt.Color("situacao:N", title=None,
                            scale=alt.Scale(domain=[acima, abaixo], range=[COR_ACIMA, COR_ABAIXO]),
                            legend=alt.Legend(orient="bottom")),
            tooltip=[alt.Tooltip("companhia", title="Companhia"),
                     alt.Tooltip("rotulo", title="Atrasados"),
                     alt.Tooltip("voos_com_previsao:Q", title="Voos", format=",")],
        )
        rotulos_cia = base.mark_text(align="left", dx=4, fontSize=11).encode(text="rotulo")
        st.altair_chart((barras + rotulos_cia).properties(height=340), use_container_width=True)
        st.caption("As 10 companhias com mais voos no filtro (mínimo de 1.000 voos). "
                   "Passe o mouse sobre a barra para ver a quantidade de voos.")

st.divider()
st.caption("Fonte: ANAC, Voo Regular Ativo (VRA) 2024, OurAirports e contornos dos estados do "
           "projeto Click That Hood. Projeto de portfólio, não é um painel oficial.")