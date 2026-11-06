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


def br_int(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def br_pct(p) -> str:
    return "–" if p is None or pd.isna(p) else f"{p:.1f}%".replace(".", ",")


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

# Aeroportos: brasileiros primeiro, do mais movimentado para o menos
aeros = (
    df.groupby(["origem", "nome_origem", "cidade_origem", "pais_origem"], dropna=False)["voos"]
    .sum().reset_index()
    .assign(
        estrangeiro=lambda x: x["pais_origem"] != "BR",
        rotulo=lambda x: (
            x["cidade_origem"].fillna("?") + " – "
            + x["nome_origem"].fillna("").str.slice(0, 40)
            + " (" + x["origem"] + ")"
        ),
    )
    .sort_values(["estrangeiro", "voos"], ascending=[True, False])
)
mapa_aero = dict(zip(aeros["rotulo"], aeros["origem"]))
aero_sel = st.sidebar.multiselect("Aeroporto (origem ou destino)", list(mapa_aero), placeholder="Todos")
if aero_sel:
    codigos = [mapa_aero[a] for a in aero_sel]
    df = df[df["origem"].isin(codigos) | df["destino"].isin(codigos)]

# ---------- Cabeçalho e cards ----------
st.title("✈️ Atrasos de voos no Brasil · 2024")
st.caption("Um voo é considerado atrasado quando sai mais de 30 minutos depois do horário previsto "
           "(mesmo corte da ANAC). Voos cancelados não entram no % de atrasos.")

if df.empty:
    st.warning("Nenhum voo para os filtros escolhidos.")
    st.stop()

m = metricas(df)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Voos", br_int(m["voos"]))
c2.metric("Saíram com mais de 30 min de atraso", br_pct(m["pct_atrasados"]))
c3.metric("Atraso médio na partida", "–" if m["atraso_medio"] is None else f"{m['atraso_medio']:.0f} min")
c4.metric("Cancelados", br_pct(m["pct_cancelados"]))

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
        pior = por_mes.loc[por_mes["pct"].idxmax()]
        melhor = por_mes.loc[por_mes["pct"].idxmin()]
        st.caption(f"Mais atrasos em **{pior['nome_mes']}** ({br_pct(pior['pct'])}) e "
                   f"menos em **{melhor['nome_mes']}** ({br_pct(melhor['pct'])}).")

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
        media_pct = m["pct_atrasados"]
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
        rotulos = base.mark_text(align="left", dx=4, fontSize=11).encode(text="rotulo")
        st.altair_chart((barras + rotulos).properties(height=340), use_container_width=True)
        st.caption("As 10 companhias com mais voos no filtro (mínimo de 1.000 voos). "
                   "Passe o mouse sobre a barra para ver a quantidade de voos.")

st.divider()
st.caption("Fonte: ANAC, Voo Regular Ativo (VRA) 2024, e OurAirports. Projeto de portfólio, não é um painel oficial.")