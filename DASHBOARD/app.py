# =========================================================
# PROJETO : AUTOMACAO SINAN
# ARQUIVO : DASHBOARD/app.py
# OBJETIVO:
# Painel Executivo de Vigilancia Epidemiologica
# Arboviroses (DENGUE / CHIKUNGUNYA) - Sao Luis / SEMUS.
# =========================================================

# =========================================================
# IMPORTACOES
# =========================================================

import sys

import re

import json

import base64

import unicodedata

from pathlib import Path

from datetime import datetime

import pandas as pd

import plotly.graph_objects as go

import streamlit as st

# =========================================================
# CAMINHOS DO PROJETO
# =========================================================

PASTA_DASHBOARD = Path(__file__).resolve().parent

PASTA_RAIZ = PASTA_DASHBOARD.parent

PASTA_ASSETS = PASTA_DASHBOARD / "assets"

PASTA_DADOS = PASTA_DASHBOARD / "data"

# =========================================================
# DETECCAO DE AMBIENTE (Cloud vs Local)
# =========================================================

_CLOUD = Path("/mount/src").exists()

# =========================================================
# CONFIGURAR sys.path
# =========================================================

PASTA_SCRIPTS = PASTA_RAIZ / "SCRIPTS_PYTHON"

for _p in [
    PASTA_SCRIPTS,
    Path("/mount/src/automacao-sinan/SCRIPTS_PYTHON"),
]:
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# =========================================================
# MODULOS CENTRAIS DO PROJETO
# =========================================================

from CONFIG_00 import (

    MAPA_AGRAVOS,

    AGRAVOS_ARBOVIROSES,

    ARQUIVO_DICIONARIO,

    STATUS_CONFIRMADO,

    STATUS_DESCARTADO,

    STATUS_INCONCLUSIVO

)

from FUNCOES_GERAIS import (

    ler_dbf,

    preparar_base

)

# FUNCOES_SHAPEFILE usa geopandas — opcional no Cloud
try:
    from FUNCOES_SHAPEFILE import ler_shapefile_distritos
    _TEM_SHAPEFILE = True
except Exception:
    _TEM_SHAPEFILE = False
    def ler_shapefile_distritos(*args, **kwargs):
        return None

# =========================================================
# PALETA AMARELO - VERDE - AZUL
# =========================================================

COR_AZUL = "#0072B2"

COR_AZUL_ESCURO = "#0A2E4D"

COR_VERDE = "#2E933C"

COR_AMARELO = "#E1B000"

COR_VERDE_AZUL = "#137E8E"

COR_VERMELHO = "#C0392B"

# Tons suaves usados nas faixas do mapa coropletico.
COR_AZUL_CLARO = "#AED6F1"      # abaixo de 100 /100 mil

COR_VERDE_CLARO = "#ABEBC6"     # 100 a 300 /100 mil

COR_AMARELO_CLARO = "#F9E154"   # acima de 300 /100 mil (amarelo mais visivel)

ESCALA_INCIDENCIA = "YlGnBu"   # amarelo -> verde -> azul (barras)

CORES_AGRAVO = {

    "DENGUE": COR_AZUL,

    "CHIKUNGUNYA": COR_AMARELO

}

# Cores distintas para cada sorotipo da dengue (DENV1 a DENV4).
CORES_SOROTIPO = {

    "DENV1": COR_AZUL,

    "DENV2": COR_VERDE,

    "DENV3": COR_AMARELO,

    "DENV4": COR_VERDE_AZUL

}

# =========================================================
# CONFIGURACAO DA PAGINA
# =========================================================

st.set_page_config(

    page_title="Vigilancia Epidemiologica - SEMUS Sao Luis",

    page_icon=str(PASTA_ASSETS / "logo_semus.png"),

    layout="wide"

)

# =========================================================
# ESTILO GLOBAL (CSS)
# =========================================================

st.markdown(

    """
    <style>
    .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }

    .app-header {
        background: linear-gradient(90deg, #0A2E4D 0%, #0B3D66 60%, #0072B2 100%);
        border-radius: 14px;
        padding: 16px 26px;
        margin-bottom: 18px;
        color: #FFFFFF;
        box-shadow: 0 4px 16px rgba(0,0,0,0.18);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .header-logos {
        display: flex;
        align-items: center;
        gap: 10px;
        background: #FFFFFF;
        border-radius: 10px;
        padding: 6px 10px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.18);
    }
    .header-logos img { display: block; }
    .app-header h1 { font-size: 26px; margin: 0; font-weight: 800; }
    .app-header p  { margin: 2px 0 0 0; opacity: 0.92; font-size: 13px; font-weight: 600; }
    .header-tag {
        background: rgba(255,255,255,0.16);
        border-radius: 8px;
        padding: 6px 12px;
        font-size: 12px;
        font-weight: 600;
        margin-left: 8px;
        display: inline-block;
    }

    /* ---- Cartao KPI COMPACTO ---- */
    .kpi-card {
        position: relative;
        background: #FFFFFF;
        border: 1px solid #E6EBF0;
        border-radius: 12px;
        padding: 10px 12px 10px 12px;
        box-shadow: 0 2px 8px rgba(13,41,61,0.08);
        border-left: 3px solid #0072B2;
        height: 100%;
        transition: transform 0.12s ease, box-shadow 0.12s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(13,41,61,0.14);
    }
    .kpi-topo  { display: flex; justify-content: space-between; align-items: center; }
    .kpi-icon  { font-size: 24px; line-height: 1; }
    .kpi-chip  {
        font-size: 10px; font-weight: 800; color: #FFFFFF;
        padding: 2px 7px; border-radius: 20px; letter-spacing: 0.3px;
    }
    .kpi-valor { font-size: 20px; font-weight: 800; color: #13293D; line-height: 1.1; margin-top: 3px; }
    .kpi-rotulo{ font-size: 11px; font-weight: 700; color: #3A4A59; text-transform: uppercase; letter-spacing: 0.4px; }
    .kpi-split {
        margin-top: 6px; padding-top: 5px; border-top: 1px dashed #E1E7ED;
        display: flex; gap: 10px; font-size: 10px; font-weight: 700; color: #3A4A59;
    }
    .kpi-split span { display: inline-flex; align-items: center; gap: 4px; }
    .kpi-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }

    .painel {
        background: #FFFFFF;
        border-radius: 14px;
        padding: 14px 16px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.06);
        border: 1px solid #EEF1F4;
    }
    .ind-linha {
        display: flex; justify-content: space-between; align-items: center;
        padding: 8px 0; border-bottom: 1px solid #EEF1F4;
    }
    .ind-rotulo { font-size: 13px; font-weight: 600; color: #2C3947; }
    .ind-valor  { font-size: 18px; font-weight: 800; }

    /* ---- Card de variacao semanal ---- */
    .var-linha {
        display: flex; justify-content: space-between; align-items: center;
        padding: 9px 0; border-bottom: 1px solid #EEF1F4;
    }
    .var-linha:last-child { border-bottom: none; }
    .var-se   { font-size: 13px; font-weight: 700; color: #13293D; }
    .var-casos{ font-size: 11px; font-weight: 600; color: #5A6B7B; }
    .var-delta{
        font-size: 16px; font-weight: 800; color: #C0392B;
        background: #FDECEA; border-radius: 8px; padding: 3px 10px;
    }

    .alerta {
        border-radius: 10px; padding: 9px 13px; margin-bottom: 8px;
        font-size: 13px; font-weight: 600;
    }
    .alerta-vermelho { background: #FDECEA; border-left: 5px solid #C0392B; color: #7A1C14; }
    .alerta-amarelo  { background: #FFF8E1; border-left: 5px solid #E1B000; color: #7A5B00; }
    .alerta-verde    { background: #EAF6EC; border-left: 5px solid #2E933C; color: #1E5E29; }
    .alerta-azul     { background: #E7F1F8; border-left: 5px solid #0072B2; color: #0A456E; }

    .secao-titulo { font-size: 16px; font-weight: 800; color: #0A2E4D; margin: 6px 0 6px 0; }
    </style>
    """,

    unsafe_allow_html=True

)

# =========================================================
# NORMALIZACAO DE NOMES DE DISTRITO
# =========================================================

def chave_distrito(valor):

    texto = unicodedata.normalize(

        "NFKD",

        str(valor).strip().upper()

    ).encode("ASCII", "ignore").decode("ASCII")

    texto = re.sub(r"[-_]", " ", texto)

    return " ".join(texto.split())

# =========================================================
# SOROTIPO DA DENGUE (SINAN SOROTIPO)
# =========================================================

# Ordem fixa dos sorotipos circulantes da dengue (DENV1 a DENV4).
ORDEM_SOROTIPOS = ["DENV1", "DENV2", "DENV3", "DENV4"]


def rotulo_sorotipo(codigo):

    # Coluna SOROTIPO do DBF da dengue: codigos 1-4 -> DENV1-DENV4.
    # Vazio / outros valores nao representam sorotipo identificado.

    digitos = re.sub(r"\D", "", str(codigo))

    if digitos in {"1", "2", "3", "4"}:

        return f"DENV{digitos}"

    return None

# =========================================================
# IDADE / FAIXA ETARIA (SINAN NU_IDADE_N)
# =========================================================

# Ordem fixa das faixas etarias (padrao RIPSA 6 adaptado) usadas no grafico.
ORDEM_FAIXAS = [
    "<1", "1-4", "5-9", "10-19", "20-39", "40-59", "60+"
]


def idade_em_anos(codigo):

    # NU_IDADE_N do SINAN: 4 digitos, 1o digito = unidade
    # (1=hora, 2=dia, 3=mes, 4=ano), demais 3 = valor.
    # Tambem aceita idade ja gravada como inteiro simples.

    digitos = re.sub(r"\D", "", str(codigo))

    if not digitos:

        return None

    if len(digitos) == 4 and digitos[0] in "1234":

        unidade = digitos[0]

        valor = int(digitos[1:])

        return valor if unidade == "4" else 0

    numero = int(digitos)

    if numero > 130:

        return None

    return numero


def faixa_etaria(anos):

    if anos is None:

        return None

    if anos < 1:

        return "<1"

    if anos <= 4:

        return "1-4"

    if anos <= 9:

        return "5-9"

    if anos <= 19:

        return "10-19"

    if anos <= 39:

        return "20-39"

    if anos <= 59:

        return "40-59"

    return "60+"

# =========================================================
# CARREGAMENTO DE DADOS (COM CACHE)
# =========================================================

@st.cache_data(show_spinner="Lendo e preparando as bases...")
def carregar_base():

    # ---- STREAMLIT CLOUD: le parquet pre-processado ----
    if _CLOUD:
        parquet = PASTA_DADOS / "BASE_DASHBOARD.parquet"
        if parquet.exists():
            try:
                df = pd.read_parquet(parquet)
                if not df.empty:
                    return df
            except Exception as e:
                st.warning(f"Erro ao ler parquet: {e}")
        st.error(
            "⚠️ Dados não disponíveis. "
            "Execute 24_EXPORTAR_GITHUB.py localmente e faça push para atualizar."
        )
        return pd.DataFrame()

    # ---- LOCAL: le DBF e prepara base ----
    # Mapa codigo do distrito -> chave normalizada (aba DISTRITOS).

    mapa_dist = pd.read_excel(

        ARQUIVO_DICIONARIO,

        sheet_name="DISTRITOS"

    )

    cod_para_chave = {

        str(c).strip(): chave_distrito(d)

        for c, d in zip(mapa_dist["CODIGO"], mapa_dist["DESCRICAO"])

    }

    quadros = []

    for agravo in AGRAVOS_ARBOVIROSES:

        config = MAPA_AGRAVOS[agravo]

        arquivo = config["pasta"] / config["arquivo"]

        if not arquivo.exists():

            candidatos = (

                sorted(config["pasta"].glob("*.dbf")) +
                sorted(config["pasta"].glob("*.DBF"))

            )

            if not candidatos:

                continue

            arquivo = candidatos[0]

        df = ler_dbf(arquivo)

        if df is None or df.empty:

            continue

        df = preparar_base(df, aplicar_filtro_municipio=True)

        df["AGRAVO"] = agravo

        quadros.append(df)

    if not quadros:

        return pd.DataFrame()

    base = pd.concat(quadros, ignore_index=True)

    # --- Variaveis temporais ---

    if "DT_NOTIFIC" in base.columns:

        base["DT_NOTIFIC"] = pd.to_datetime(

            base["DT_NOTIFIC"], errors="coerce"

        )

        iso = base["DT_NOTIFIC"].dt.isocalendar()

        base["ANO_EPI"] = iso.year

        base["SEMANA_EPI"] = iso.week

        base["MES"] = base["DT_NOTIFIC"].dt.month

    # --- Faixa etaria ---

    if "NU_IDADE_N" in base.columns:

        base["IDADE_ANOS"] = base["NU_IDADE_N"].map(idade_em_anos)

        base["FAIXA_ETARIA"] = base["IDADE_ANOS"].map(faixa_etaria)

    else:

        base["FAIXA_ETARIA"] = None

    # --- Distrito sanitario ---

    if "ID_DISTRIT" in base.columns:

        codigo = base["ID_DISTRIT"].astype(str).str.strip()

        base["DISTRITO"] = codigo.map(cod_para_chave)

    else:

        base["DISTRITO"] = None

    # --- Obito pelo agravo ---

    if "EVOLUCAO" in base.columns:

        base["OBITO_AGRAVO"] = (

            base["EVOLUCAO"].fillna("").astype(str).str.strip() == "2"

        )

    else:

        base["OBITO_AGRAVO"] = False

    return base


@st.cache_data(show_spinner=False)
def carregar_populacao_municipio():

    if _CLOUD or not ARQUIVO_DICIONARIO.exists():
        return {}

    df = pd.read_excel(ARQUIVO_DICIONARIO, sheet_name="POPULACAO_MUNICIPIO")

    df["ANO"] = pd.to_numeric(df["ANO"], errors="coerce")

    df["POPULACAO"] = pd.to_numeric(df["POPULACAO"], errors="coerce")

    return dict(zip(df["ANO"], df["POPULACAO"]))


@st.cache_data(show_spinner=False)
def carregar_populacao_distrito():

    if _CLOUD or not ARQUIVO_DICIONARIO.exists():
        return {}, 2026

    df = pd.read_excel(ARQUIVO_DICIONARIO, sheet_name="POPULACAO_DISTRITO")

    df["ANO"] = pd.to_numeric(df["ANO"], errors="coerce")

    df["POPULACAO"] = pd.to_numeric(df["POPULACAO"], errors="coerce")

    ano_ref = int(df["ANO"].max())

    recente = df[df["ANO"] == ano_ref]

    return {

        chave_distrito(d): p

        for d, p in zip(recente["DISTRITO"], recente["POPULACAO"])

    }, ano_ref


@st.cache_data(show_spinner=False)
def carregar_geojson_distritos():

    if _CLOUD or not _TEM_SHAPEFILE:
        return {"type": "FeatureCollection", "features": []}

    gdf = ler_shapefile_distritos()

    gdf = gdf[["CHAVE_DISTRITO", "geometry"]].copy()

    gdf["CHAVE_DISTRITO"] = gdf["CHAVE_DISTRITO"].map(chave_distrito)

    return json.loads(gdf.to_json())


@st.cache_data(show_spinner=False)
def carregar_centroides_distritos():

    # Ponto interno (representative_point) de cada distrito, usado para
    # ancorar o rotulo com o nome dentro do poligono no mapa coropletico.
    # representative_point garante um ponto sempre dentro do poligono,
    # mesmo em formas concavas, ao contrario do centroide geometrico.

    from shapely.geometry import shape

    geo = carregar_geojson_distritos()

    centroides = {}

    for feature in geo.get("features", []):

        chave = feature.get("properties", {}).get("CHAVE_DISTRITO")

        if not chave:

            continue

        try:

            ponto = shape(feature["geometry"]).representative_point()

            centroides[chave] = (ponto.x, ponto.y)

        except Exception:

            continue

    return centroides


@st.cache_data(show_spinner=False)
def carregar_poligonos_distritos():

    # Aneis externos (lon, lat) de cada distrito para desenhar o mapa
    # coropletico em eixos cartesianos (go.Scatter com fill="toself").
    # Esse modo permite ancorar anotacoes de texto inclinadas (textangle)
    # dentro de cada poligono, o que o subplot "geo" do Choropleth nao
    # suporta. Poligonos multiplos (MultiPolygon) viram varios aneis.

    from shapely.geometry import shape

    geo = carregar_geojson_distritos()

    poligonos = {}

    for feature in geo.get("features", []):

        chave = feature.get("properties", {}).get("CHAVE_DISTRITO")

        if not chave:

            continue

        try:

            geom = shape(feature["geometry"])

        except Exception:

            continue

        if geom.geom_type == "Polygon":

            partes_geom = [geom]

        elif geom.geom_type == "MultiPolygon":

            partes_geom = list(geom.geoms)

        else:

            continue

        aneis = []

        for parte in partes_geom:

            xs, ys = parte.exterior.coords.xy

            aneis.append((list(xs), list(ys)))

        poligonos[chave] = aneis

    return poligonos

# =========================================================
# FORMATACAO
# =========================================================

def fmt_int(valor):

    return f"{int(valor):,}".replace(",", ".")


def fmt_dec(valor, casas=1):

    if valor is None:

        return "—"

    return f"{valor:.{casas}f}".replace(".", ",")


def hex_rgba(cor_hex, alpha):

    cor_hex = cor_hex.lstrip("#")

    r, g, b = (int(cor_hex[i:i + 2], 16) for i in (0, 2, 4))

    return f"rgba({r},{g},{b},{alpha})"


def quebrar_nome(nome, largura=12):

    # Quebra nomes longos de distrito em varias linhas (separador <br>)
    # para o rotulo caber dentro do poligono sem transbordar.

    linhas = []

    atual = ""

    for palavra in nome.split():

        if atual and len(atual) + 1 + len(palavra) > largura:

            linhas.append(atual)

            atual = palavra

        else:

            atual = f"{atual} {palavra}".strip()

    if atual:

        linhas.append(atual)

    return "<br>".join(linhas)


def cor_faixa_incidencia(valor):

    # Faixas do mapa: azul claro (<100), verde claro (100-300),
    # amarelo claro (>300) por 100 mil habitantes. Sem populacao
    # (incidencia ausente) -> branco.

    if valor is None or pd.isna(valor):

        return "#FFFFFF"

    if valor < 100:

        return COR_AZUL_CLARO

    if valor <= 300:

        return COR_VERDE_CLARO

    return COR_AMARELO_CLARO


@st.cache_data(show_spinner=False)
def logo_data_uri(nome_arquivo):

    # Le um logo da pasta assets e devolve um data URI base64 para uso
    # direto em HTML (cabecalho renderizado via st.markdown).

    caminho = PASTA_ASSETS / nome_arquivo

    if not caminho.exists():

        return ""

    dados = base64.b64encode(caminho.read_bytes()).decode("ascii")

    return f"data:image/png;base64,{dados}"

# =========================================================
# CARREGAR DADOS
# =========================================================

base = carregar_base()

pop_municipio = carregar_populacao_municipio()

pop_distrito, ano_pop_dist = carregar_populacao_distrito()

geojson_dist = carregar_geojson_distritos()

centroides_dist = carregar_centroides_distritos()

poligonos_dist = carregar_poligonos_distritos()

# =========================================================
# CABECALHO (HEADER AZUL ESCURO)
# =========================================================

atualizacao = datetime.now().strftime("%d/%m/%Y %H:%M")

logo_semus_uri = logo_data_uri("logo_semus.png")

logo_vem_uri = logo_data_uri("loco_VEM.png")

logos_html = ""

if logo_semus_uri:

    logos_html += (
        f"<img src='{logo_semus_uri}' alt='SEMUS' "
        f"style='height:46px;width:auto;'/>"
    )

if logo_vem_uri:

    logos_html += (
        f"<img src='{logo_vem_uri}' alt='VEM' "
        f"style='height:46px;width:auto;'/>"
    )

st.markdown(

    f"""
    <div class="app-header">
        <div style="display:flex;align-items:center;gap:14px;">
            <div class="header-logos">{logos_html}</div>
            <div>
                <h1>Vigilancia Epidemiologica</h1>
                <p>Arboviroses - Dengue &middot; Chikungunya &nbsp;|&nbsp; Sao Luis / MA - SEMUS</p>
            </div>
        </div>
        <div style="text-align:right;">
            <span class="header-tag">Atualizado: {atualizacao}</span>
            <span class="header-tag">Pop. distrito: {ano_pop_dist}</span>
        </div>
    </div>
    """,

    unsafe_allow_html=True

)

if base.empty:

    st.error("Nenhuma base encontrada para os agravos configurados.")

    st.stop()

# =========================================================
# SIDEBAR - FILTROS
# =========================================================

st.sidebar.image(str(PASTA_ASSETS / "logo_semus.png"))

st.sidebar.markdown("### Filtros")

opcao_agravo = st.sidebar.selectbox(

    "Agravo",

    options=["Todos (Dengue + Chikungunya)"] + AGRAVOS_ARBOVIROSES

)

anos = sorted(int(a) for a in base["ANO_EPI"].dropna().unique())

ano = st.sidebar.selectbox(

    "Ano epidemiologico",

    options=anos,

    index=len(anos) - 1

)

# ---- Filtro de Semana Epidemiologica ----

semanas_ano = base.loc[base["ANO_EPI"] == ano, "SEMANA_EPI"].dropna()

if not semanas_ano.empty:

    se_min = int(semanas_ano.min())

    se_max = int(semanas_ano.max())

else:

    se_min, se_max = 1, 53

if se_min < se_max:

    se_intervalo = st.sidebar.slider(

        "Semana epidemiologica",

        min_value=se_min,

        max_value=se_max,

        value=(se_min, se_max)

    )

else:

    se_intervalo = (se_min, se_max)

distritos_opcoes = sorted(

    d for d in base["DISTRITO"].dropna().unique()

)

distritos_sel = st.sidebar.multiselect(

    "Distrito sanitario",

    options=distritos_opcoes,

    default=distritos_opcoes

)

sexo_opcao = "Todos"

if "DESC_CS_SEXO" in base.columns:

    sexos = ["Todos"] + sorted(

        s for s in base["DESC_CS_SEXO"].dropna().unique()

    )

    sexo_opcao = st.sidebar.selectbox("Sexo", options=sexos)

st.sidebar.caption(

    "Incidencia e letalidade calculadas sobre os casos confirmados "
    "(STATUS_MS = CONFIRMADO) com criterio laboratorial ou "
    "clinico-epidemiologico, para Dengue e Chikungunya."

)

# =========================================================
# APLICAR FILTROS
# =========================================================

# Filtro base (ano / semana / distrito / sexo), sem agravo -> usado no donut.

filtro_comum = base["ANO_EPI"] == ano

# Filtro de semana epidemiologica: so restringe quando o intervalo
# escolhido e menor que o disponivel, preservando registros sem SE
# informada quando o intervalo esta cheio.

if se_intervalo != (se_min, se_max):

    filtro_comum = filtro_comum & base["SEMANA_EPI"].between(

        se_intervalo[0], se_intervalo[1]

    )

# So filtra por distrito quando um subconjunto e escolhido; com todos
# selecionados mantem inclusive os registros sem distrito informado,
# para a manchete de notificados nao subcontar.

if distritos_sel and len(distritos_sel) < len(distritos_opcoes):

    filtro_comum = filtro_comum & base["DISTRITO"].isin(distritos_sel)

if sexo_opcao != "Todos" and "DESC_CS_SEXO" in base.columns:

    filtro_comum = filtro_comum & (base["DESC_CS_SEXO"] == sexo_opcao)

df_sem_agravo = base[filtro_comum].copy()

# Filtro completo (inclui agravo) -> usado no resto do painel.

if opcao_agravo in AGRAVOS_ARBOVIROSES:

    df = df_sem_agravo[df_sem_agravo["AGRAVO"] == opcao_agravo].copy()

else:

    df = df_sem_agravo.copy()

# =========================================================
# INDICADORES PRINCIPAIS
# =========================================================

# Mostra o detalhamento Dengue/Chikungunya quando nao ha agravo filtrado.

mostrar_breakdown = opcao_agravo not in AGRAVOS_ARBOVIROSES

status = df.get("STATUS_MS", pd.Series(dtype=str))

criterio = (

    df.get("CRITERIO", pd.Series(index=df.index, dtype=str))
    .astype(str)
    .str.strip()

)

# Mascaras de classificacao.
#
# As regras de classificacao (STATUS_MS, CRITERIO, EVOLUCAO/obito) sao
# derivadas do dicionario unico CLASSIFICACAO_FINAL em preparar_base e
# aplicadas igualmente as duas arboviroses. Por isso, estas mascaras
# valem identicamente para DENGUE e CHIKUNGUNYA; a unica analise
# exclusiva da dengue e o sorotipo (DENV1-DENV4).

mask_descartado = status == STATUS_DESCARTADO

# Confirmados contam APENAS casos com STATUS_MS = CONFIRMADO E criterio
# de confirmacao laboratorial (1) ou clinico-epidemiologico (2). Vale
# igualmente para DENGUE e CHIKUNGUNYA. Incidencia e letalidade usam
# esse total de confirmados com criterio definido.

mask_com_criterio = criterio.isin(["1", "2"])

mask_confirmado = (status == STATUS_CONFIRMADO) & mask_com_criterio

mask_obito = df["OBITO_AGRAVO"]

mask_provavel = ~mask_descartado                  # notificados nao descartados

mask_lab = mask_confirmado & (criterio == "1")    # confirmacao laboratorial

mask_clin = mask_confirmado & (criterio == "2")   # clinico-epidemiologico


def por_agravo(mask):

    contagem = df.loc[mask, "AGRAVO"].value_counts()

    return {

        a: int(contagem.get(a, 0))

        for a in AGRAVOS_ARBOVIROSES

    }


brk_notif = por_agravo(pd.Series(True, index=df.index))

brk_provaveis = por_agravo(mask_provavel)

brk_confirmados = por_agravo(mask_confirmado)

brk_obitos = por_agravo(mask_obito)

brk_lab = por_agravo(mask_lab)

brk_clin = por_agravo(mask_clin)

total_notificados = len(df)

total_provaveis = int(mask_provavel.sum())

total_confirmados = int(mask_confirmado.sum())

total_obitos = int(mask_obito.sum())

total_lab = int(mask_lab.sum())

total_clin = int(mask_clin.sum())

populacao_ano = pop_municipio.get(ano)


def calc_incidencia(confirmados):

    if populacao_ano and populacao_ano > 0:

        return confirmados / populacao_ano * 100000

    return None


def calc_letalidade(obitos, confirmados):

    return obitos / confirmados * 100 if confirmados > 0 else 0.0


taxa_incidencia = calc_incidencia(total_confirmados)

letalidade = calc_letalidade(total_obitos, total_confirmados)

taxa_confirmacao = (

    total_confirmados / total_notificados * 100

    if total_notificados > 0 else 0.0

)

brk_incidencia = {

    a: calc_incidencia(brk_confirmados[a])

    for a in AGRAVOS_ARBOVIROSES

}

brk_letalidade = {

    a: calc_letalidade(brk_obitos[a], brk_confirmados[a])

    for a in AGRAVOS_ARBOVIROSES

}

# =========================================================
# CARTOES KPI (COMPACTOS)
# =========================================================

def cartao_kpi(coluna, icone, rotulo, valor, cor, breakdown=None, fmt=fmt_int):

    # Faixa de detalhamento por agravo (apenas no modo "Todos").

    split_html = ""

    if breakdown is not None and mostrar_breakdown:

        valor_d = fmt(breakdown.get("DENGUE", 0))

        valor_c = fmt(breakdown.get("CHIKUNGUNYA", 0))

        split_html = (

            f"<div class='kpi-split'>"
            f"<span><span class='kpi-dot' style='background:{COR_AZUL};'></span>"
            f"Dengue {valor_d}</span>"
            f"<span><span class='kpi-dot' style='background:{COR_AMARELO};'></span>"
            f"Chik {valor_c}</span>"
            f"</div>"

        )

    # Chip com o agravo quando ha um filtrado.

    chip_html = ""

    if not mostrar_breakdown:

        rotulo_chip = "CHIK" if opcao_agravo == "CHIKUNGUNYA" else "DENGUE"

        chip_html = (

            f"<span class='kpi-chip' style='background:{cor};'>"
            f"{rotulo_chip}</span>"

        )

    coluna.markdown(

        f"""<div class="kpi-card" style="border-left-color:{cor};">
<div class="kpi-topo">
<div class="kpi-icon">{icone}</div>
{chip_html}
</div>
<div class="kpi-valor">{valor}</div>
<div class="kpi-rotulo">{rotulo}</div>
{split_html}
</div>""",

        unsafe_allow_html=True

    )


# --- Linha 1: visao geral (sem card "Descartados") ---

k1, k2, k3, k4 = st.columns(4)

cartao_kpi(k1, "📋", "Notificados", fmt_int(total_notificados), COR_AZUL, brk_notif)

cartao_kpi(k2, "🔎", "Casos provaveis", fmt_int(total_provaveis), COR_VERDE_AZUL, brk_provaveis)

cartao_kpi(k3, "✅", "Confirmados", fmt_int(total_confirmados), COR_VERDE, brk_confirmados)

cartao_kpi(k4, "⚰️", "Obitos (agravo)", fmt_int(total_obitos), COR_AZUL_ESCURO, brk_obitos)

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# --- Linha 2: criterio de confirmacao e taxas ---

m1, m2, m3, m4 = st.columns(4)

cartao_kpi(m1, "🧪", "Conf. laboratorio", fmt_int(total_lab), COR_AZUL, brk_lab)

cartao_kpi(m2, "🩺", "Conf. clinico-epid.", fmt_int(total_clin), COR_VERDE, brk_clin)

cartao_kpi(

    m3, "🦟", "Taxa incid. /100 mil", fmt_dec(taxa_incidencia),
    COR_AMARELO, brk_incidencia, fmt=fmt_dec

)

cartao_kpi(

    m4, "📉", "Letalidade (%)", fmt_dec(letalidade, 2),
    COR_VERMELHO, brk_letalidade, fmt=lambda v: fmt_dec(v, 2)

)

st.caption(

    "ℹ️ **Confirmados** consideram apenas casos com STATUS_MS = CONFIRMADO "
    "**e** criterio de confirmacao **laboratorial** ou "
    "**clinico-epidemiologico** preenchido (Dengue e Chikungunya); "
    "confirmados sem criterio informado nao entram na contagem, nas taxas "
    "nem na incidencia."

)

st.markdown("<br>", unsafe_allow_html=True)

# =========================================================
# AGREGACOES POR DISTRITO
# =========================================================

def agregar_distritos(quadro, chaves):

    # Garante uma linha para cada distrito selecionado (mesmo com 0 casos),
    # para que todos aparecam no mapa e no ranking.

    chaves = sorted(chaves)

    com_dist = quadro.dropna(subset=["DISTRITO"])

    if com_dist.empty:

        notificados = pd.Series(0, index=chaves)

        confirmados = pd.Series(0, index=chaves)

    else:

        notificados = (

            com_dist.groupby("DISTRITO").size()
            .reindex(chaves, fill_value=0)

        )

        # Confirmados = STATUS_MS = CONFIRMADO com criterio definido
        # (laboratorial = 1 ou clinico-epidemiologico = 2).

        crit_dist = (

            com_dist.get("CRITERIO", pd.Series(index=com_dist.index, dtype=str))
            .astype(str).str.strip()

        )

        confirmados = (

            com_dist[
                (com_dist["STATUS_MS"] == STATUS_CONFIRMADO)
                & crit_dist.isin(["1", "2"])
            ]
            .groupby("DISTRITO").size()
            .reindex(chaves, fill_value=0)

        )

    resumo = pd.DataFrame({

        "DISTRITO": chaves,

        "NOTIFICADOS": notificados.values,

        "CONFIRMADOS": confirmados.values

    })

    resumo["POPULACAO"] = resumo["DISTRITO"].map(pop_distrito)

    resumo["INCIDENCIA"] = (

        resumo["CONFIRMADOS"] / resumo["POPULACAO"] * 100000

    ).round(1)

    return resumo


chaves_mapa = distritos_sel if distritos_sel else distritos_opcoes

resumo_dist = agregar_distritos(df, chaves_mapa)

# =========================================================
# LINHA 1 : SERIE SEMANAL + DONUT POR AGRAVO
# =========================================================

col_serie, col_donut = st.columns([2, 1])

# ---- Casos por Semana Epidemiologica ----

with col_serie:

    st.markdown(

        "<div class='secao-titulo'>Casos por Semana Epidemiologica</div>",

        unsafe_allow_html=True

    )

    base_se = df.dropna(subset=["SEMANA_EPI"]).copy()

    if not base_se.empty:

        base_se["SEMANA_EPI"] = base_se["SEMANA_EPI"].astype(int)

        semanas = list(

            range(

                int(base_se["SEMANA_EPI"].min()),

                int(base_se["SEMANA_EPI"].max()) + 1

            )

        )

        fig_se = go.Figure()

        for agravo in AGRAVOS_ARBOVIROSES:

            sub = base_se[base_se["AGRAVO"] == agravo]

            if sub.empty:

                continue

            serie = (

                sub.groupby("SEMANA_EPI").size()
                .reindex(semanas, fill_value=0)

            )

            fig_se.add_trace(go.Scatter(

                x=semanas,

                y=serie.values,

                mode="lines",

                name=agravo.capitalize(),

                line=dict(color=CORES_AGRAVO.get(agravo, COR_AZUL), width=2.5),

                fill="tozeroy",

                fillcolor=hex_rgba(CORES_AGRAVO.get(agravo, COR_AZUL), 0.20)

            ))

        fig_se.update_layout(

            height=320,

            margin=dict(t=10, r=10, b=10, l=10),

            plot_bgcolor="#FFFFFF",

            paper_bgcolor="#FFFFFF",

            legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0),

            xaxis_title="Semana epidemiologica",

            yaxis_title="Casos"

        )

        fig_se.update_xaxes(dtick=2, showgrid=False)

        fig_se.update_yaxes(showgrid=True, gridcolor="#ECECEC")

        st.plotly_chart(fig_se, width="stretch")

    else:

        st.info("Sem dados semanais para o filtro atual.")

# ---- Donut por agravo ----

with col_donut:

    st.markdown(

        "<div class='secao-titulo'>Casos por Agravo</div>",

        unsafe_allow_html=True

    )

    contagem_agravo = (

        df_sem_agravo.groupby("AGRAVO").size()
        .reindex(AGRAVOS_ARBOVIROSES, fill_value=0)

    )

    if contagem_agravo.sum() > 0:

        fig_donut = go.Figure(go.Pie(

            labels=[a.capitalize() for a in contagem_agravo.index],

            values=contagem_agravo.values,

            hole=0.58,

            marker=dict(

                colors=[CORES_AGRAVO.get(a, COR_AZUL) for a in contagem_agravo.index]

            ),

            textinfo="percent"

        ))

        fig_donut.update_layout(

            height=320,

            margin=dict(t=10, r=10, b=10, l=10),

            paper_bgcolor="#FFFFFF",

            legend=dict(orientation="h", yanchor="bottom", y=-0.05, x=0.1),

            annotations=[dict(

                text=f"<b>{fmt_int(contagem_agravo.sum())}</b><br>casos",

                x=0.5, y=0.5, font_size=16, showarrow=False

            )]

        )

        st.plotly_chart(fig_donut, width="stretch")

    else:

        st.info("Sem casos no filtro atual.")

# =========================================================
# LINHA 2 : FAIXA ETARIA + EVOLUCAO MENSAL + 3 SEMANAS
# =========================================================

col_faixa, col_mensal, col_var = st.columns([1.2, 1.2, 1])

# ---- Grafico por faixa etaria (confirmados) ----

with col_faixa:

    st.markdown(

        "<div class='secao-titulo'>Confirmados por Faixa Etaria</div>",

        unsafe_allow_html=True

    )

    df_conf = df[mask_confirmado].dropna(subset=["FAIXA_ETARIA"])

    if not df_conf.empty:

        fig_faixa = go.Figure()

        for agravo in AGRAVOS_ARBOVIROSES:

            sub = df_conf[df_conf["AGRAVO"] == agravo]

            if sub.empty:

                continue

            serie = (

                sub.groupby("FAIXA_ETARIA").size()
                .reindex(ORDEM_FAIXAS, fill_value=0)

            )

            fig_faixa.add_trace(go.Bar(

                x=serie.values,

                y=ORDEM_FAIXAS,

                orientation="h",

                name=agravo.capitalize(),

                marker_color=CORES_AGRAVO.get(agravo, COR_AZUL)

            ))

        fig_faixa.update_layout(

            height=320,

            barmode="stack",

            margin=dict(t=10, r=10, b=10, l=10),

            plot_bgcolor="#FFFFFF",

            paper_bgcolor="#FFFFFF",

            legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0),

            xaxis_title="Confirmados",

            yaxis_title="Faixa etaria (anos)"

        )

        # Mantem a ordem RIPSA6 com a menor faixa no topo.

        fig_faixa.update_xaxes(showgrid=True, gridcolor="#ECECEC")

        fig_faixa.update_yaxes(

            showgrid=False,
            categoryorder="array",
            categoryarray=list(reversed(ORDEM_FAIXAS))

        )

        st.plotly_chart(fig_faixa, width="stretch")

    else:

        st.info("Sem idade informada para o filtro atual.")

# ---- Evolucao de confirmados acumulados por mes ----

with col_mensal:

    st.markdown(

        "<div class='secao-titulo'>Confirmados Acumulados por Mes</div>",

        unsafe_allow_html=True

    )

    df_mes = df[mask_confirmado].dropna(subset=["MES"]) if "MES" in df.columns else pd.DataFrame()

    if not df_mes.empty:

        nomes_mes = {

            1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",

            7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"

        }

        meses = list(range(1, 13))

        fig_mes = go.Figure()

        for agravo in AGRAVOS_ARBOVIROSES:

            sub = df_mes[df_mes["AGRAVO"] == agravo]

            if sub.empty:

                continue

            serie = (

                sub.groupby(sub["MES"].astype(int)).size()
                .reindex(meses, fill_value=0)
                .cumsum()

            )

            fig_mes.add_trace(go.Scatter(

                x=[nomes_mes[m] for m in meses],

                y=serie.values,

                mode="lines+markers",

                name=agravo.capitalize(),

                line=dict(color=CORES_AGRAVO.get(agravo, COR_AZUL), width=2.5)

            ))

        fig_mes.update_layout(

            height=320,

            margin=dict(t=10, r=10, b=10, l=10),

            plot_bgcolor="#FFFFFF",

            paper_bgcolor="#FFFFFF",

            legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0),

            xaxis_title="Mes",

            yaxis_title="Confirmados acumulados"

        )

        fig_mes.update_xaxes(showgrid=False)

        fig_mes.update_yaxes(showgrid=True, gridcolor="#ECECEC")

        st.plotly_chart(fig_mes, width="stretch")

    else:

        st.info("Sem confirmados com data para o filtro atual.")

# ---- Card: 3 semanas de maior aumento ----

with col_var:

    st.markdown(

        "<div class='secao-titulo'>Maiores Aumentos Semanais</div>",

        unsafe_allow_html=True

    )

    base_var = df.dropna(subset=["SEMANA_EPI"]).copy()

    linhas_var = ""

    if not base_var.empty:

        base_var["SEMANA_EPI"] = base_var["SEMANA_EPI"].astype(int)

        semanas_v = list(

            range(

                int(base_var["SEMANA_EPI"].min()),

                int(base_var["SEMANA_EPI"].max()) + 1

            )

        )

        serie_v = (

            base_var.groupby("SEMANA_EPI").size()
            .reindex(semanas_v, fill_value=0)

        )

        # Variacao absoluta em relacao a semana anterior.

        variacao = serie_v.diff().fillna(0)

        top3 = variacao.sort_values(ascending=False).head(3)

        for se, delta in top3.items():

            if delta <= 0:

                continue

            casos = int(serie_v.loc[se])

            linhas_var += (

                f"<div class='var-linha'>"
                f"<div><div class='var-se'>SE {int(se):02d}</div>"
                f"<div class='var-casos'>{fmt_int(casos)} casos notificados</div></div>"
                f"<div class='var-delta'>+{fmt_int(int(delta))}</div>"
                f"</div>"

            )

    if linhas_var:

        st.markdown(

            f"<div class='painel'>{linhas_var}</div>",

            unsafe_allow_html=True

        )

    else:

        st.info("Sem aumento semanal no filtro atual.")

# =========================================================
# LINHA 3 : PIRAMIDE POPULACIONAL POR SEXO E FAIXA ETARIA
# =========================================================

# Cores da piramide: masculino (esquerda) e feminino (direita).
COR_MASCULINO = COR_AZUL

COR_FEMININO = COR_AMARELO

st.markdown(
    "<div class='secao-titulo'>Piramide de Confirmados por Sexo e Faixa Etaria</div>",
    unsafe_allow_html=True
)

if "DESC_CS_SEXO" in df.columns:

    df_sexo = (
        df[mask_confirmado]
        .dropna(subset=["DESC_CS_SEXO", "FAIXA_ETARIA"])
        .copy()
    )

    df_sexo["DESC_CS_SEXO"] = (
        df_sexo["DESC_CS_SEXO"].astype(str).str.strip().str.upper()
    )

    df_sexo = df_sexo[df_sexo["DESC_CS_SEXO"].isin(["MASCULINO", "FEMININO"])]

else:

    df_sexo = pd.DataFrame()

if not df_sexo.empty:

    # Contagem por faixa RIPSA6 para cada sexo, na ordem fixa das faixas.

    masc = (
        df_sexo[df_sexo["DESC_CS_SEXO"] == "MASCULINO"]
        .groupby("FAIXA_ETARIA").size()
        .reindex(ORDEM_FAIXAS, fill_value=0)
    )

    fem = (
        df_sexo[df_sexo["DESC_CS_SEXO"] == "FEMININO"]
        .groupby("FAIXA_ETARIA").size()
        .reindex(ORDEM_FAIXAS, fill_value=0)
    )

    fig_pir = go.Figure()

    # Masculino projetado a esquerda (valores negativos).

    fig_pir.add_trace(go.Bar(
        y=ORDEM_FAIXAS,
        x=[-int(v) for v in masc.values],
        orientation="h",
        name="Masculino",
        marker_color=COR_MASCULINO,
        customdata=[int(v) for v in masc.values],
        text=[int(v) for v in masc.values],
        texttemplate="%{text}",
        textposition="outside",
        cliponaxis=False,
        hovertemplate="Masculino<br>Faixa %{y}: %{customdata}<extra></extra>"
    ))

    # Feminino a direita (valores positivos).

    fig_pir.add_trace(go.Bar(
        y=ORDEM_FAIXAS,
        x=[int(v) for v in fem.values],
        orientation="h",
        name="Feminino",
        marker_color=COR_FEMININO,
        customdata=[int(v) for v in fem.values],
        text=[int(v) for v in fem.values],
        texttemplate="%{text}",
        textposition="outside",
        cliponaxis=False,
        hovertemplate="Feminino<br>Faixa %{y}: %{customdata}<extra></extra>"
    ))

    # Eixo X simetrico com rotulos sempre positivos (modulo).

    limite = int(max(int(masc.max()), int(fem.max()), 1) * 1.18)

    passo = max(1, limite // 4)

    ticks = list(range(-limite, limite + 1, passo))

    fig_pir.update_layout(
        height=360,
        barmode="relative",
        bargap=0.12,
        margin=dict(t=10, r=20, b=10, l=20),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0),
        xaxis_title="Confirmados (Masculino  |  Feminino)",
        yaxis_title="Faixa etaria (anos)"
    )

    fig_pir.update_xaxes(
        showgrid=True,
        gridcolor="#ECECEC",
        zeroline=True,
        zerolinecolor="#B5C0CA",
        tickvals=ticks,
        ticktext=[fmt_int(abs(t)) for t in ticks]
    )

    fig_pir.update_yaxes(
        showgrid=False,
        categoryorder="array",
        categoryarray=list(reversed(ORDEM_FAIXAS))
    )

    st.plotly_chart(fig_pir, width="stretch")

    st.caption(
        "Piramide etaria dos casos confirmados: barras a esquerda (azul) "
        "representam o sexo masculino e a direita (amarelo) o feminino, "
        "por faixa etaria RIPSA6. Registros sem sexo masculino/feminino "
        "ou sem idade informada nao entram na piramide."
    )

else:

    if "DESC_CS_SEXO" not in df.columns:

        st.warning(
            "Coluna DESC_CS_SEXO nao encontrada na base — "
            "verifique se FUNCOES_TRADUCAO traduz CS_SEXO corretamente."
        )

    else:

        st.info(
            "Sem registros com sexo (Masculino/Feminino) e idade "
            "informados simultaneamente para o filtro atual."
        )

# =========================================================
# LINHA 4 : SOROTIPOS CIRCULANTES DA DENGUE
# =========================================================

# O sorotipo so existe para a dengue: o card e ocultado quando o
# agravo selecionado e CHIKUNGUNYA.

mostrar_sorotipo = opcao_agravo != "CHIKUNGUNYA"

if mostrar_sorotipo:

    st.markdown(
        "<div class='secao-titulo'>Sorotipos Circulantes da Dengue (DENV)</div>",
        unsafe_allow_html=True
    )

    # Restringe aos registros de dengue (no modo "Todos" descarta a chik).

    df_den = df[df["AGRAVO"] == "DENGUE"] if "AGRAVO" in df.columns else df

    if "SOROTIPO" in df_den.columns:

        contagem_soro = (
            df_den["SOROTIPO"].map(rotulo_sorotipo)
            .dropna()
            .value_counts()
            .reindex(ORDEM_SOROTIPOS, fill_value=0)
        )

    else:

        contagem_soro = pd.Series(0, index=ORDEM_SOROTIPOS)

    if int(contagem_soro.sum()) > 0:

        fig_soro = go.Figure(go.Bar(
            x=ORDEM_SOROTIPOS,
            y=contagem_soro.values,
            marker_color=[CORES_SOROTIPO[s] for s in ORDEM_SOROTIPOS],
            text=contagem_soro.values,
            texttemplate="%{text}",
            textposition="outside",
            cliponaxis=False
        ))

        fig_soro.update_layout(
            height=320,
            margin=dict(t=10, r=10, b=10, l=10),
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            showlegend=False,
            xaxis_title="Sorotipo",
            yaxis_title="Casos com sorotipo identificado"
        )

        fig_soro.update_xaxes(showgrid=False)

        fig_soro.update_yaxes(showgrid=True, gridcolor="#ECECEC")

        st.plotly_chart(fig_soro, width="stretch")

        st.caption(
            "Distribuicao dos sorotipos da dengue (coluna SOROTIPO do SINAN) "
            "entre os registros com sorotipagem identificada (DENV1 a DENV4)."
        )

    else:

        st.info("Sem sorotipo identificado para a dengue no filtro atual.")

# =========================================================
# LINHA 5 : MAPA COROPLETICO + CASOS POR DISTRITO
# =========================================================

col_mapa, col_barras = st.columns(2)

# ---- Mapa coropletico (incidencia por distrito) ----
# Faixas de incidencia: azul (<100), verde (100-300), amarelo (>300).

with col_mapa:

    st.markdown(

        "<div class='secao-titulo'>Incidencia por Distrito (Mapa)</div>",

        unsafe_allow_html=True

    )

    if not resumo_dist.empty:

        fig_mapa = go.Figure()

        # ---- Poligonos preenchidos por faixa de incidencia ----
        # Desenhados em eixos cartesianos (lon=x, lat=y) para permitir
        # anotacoes de texto inclinadas (textangle) dentro de cada
        # distrito, recurso indisponivel no subplot "geo" do Choropleth.

        for distrito, incid in zip(
            resumo_dist["DISTRITO"], resumo_dist["INCIDENCIA"]
        ):

            aneis = poligonos_dist.get(distrito)

            if not aneis:

                continue

            cor = cor_faixa_incidencia(incid)

            nome = str(distrito).title()

            inc_txt = "—" if pd.isna(incid) else f"{incid:.1f}"

            for xs, ys in aneis:

                fig_mapa.add_trace(go.Scatter(

                    x=xs,

                    y=ys,

                    fill="toself",

                    fillcolor=cor,

                    mode="lines",

                    line=dict(color="#11314A", width=1.2),

                    hoveron="fills",

                    hoverinfo="text",

                    text=f"{nome}<br>Incidencia: {inc_txt} /100 mil",

                    showlegend=False

                ))

        # ---- Anotacoes: nome do distrito, inclinado, dentro do poligono ----
        # Nomes longos quebrados em varias linhas; texto escuro sobre
        # halo branco translucido para leitura sobre o fundo claro.

        anotacoes_mapa = []

        for distrito in resumo_dist["DISTRITO"]:

            ponto = centroides_dist.get(distrito)

            if not ponto:

                continue

            anotacoes_mapa.append(dict(

                x=ponto[0],

                y=ponto[1],

                text=quebrar_nome(str(distrito).title()),

                showarrow=False,

                textangle=0,

                align="center",

                xanchor="center",

                yanchor="middle",

                font=dict(size=7, color="#11314A", family="Arial Black"),

                bgcolor="rgba(255,255,255,0.55)",

                borderpad=1

            ))

        # ---- Legenda de faixas de incidencia (entradas so de legenda) ----

        faixas_legenda = [

            ("Menor que 100 /100 mil", COR_AZUL_CLARO),

            ("100 a 300 /100 mil", COR_VERDE_CLARO),

            ("Acima de 300 /100 mil", COR_AMARELO_CLARO),

        ]

        for rotulo_faixa, cor_faixa in faixas_legenda:

            fig_mapa.add_trace(go.Scatter(

                x=[None],

                y=[None],

                mode="markers",

                marker=dict(

                    symbol="square",

                    size=16,

                    color=cor_faixa,

                    line=dict(color="#11314A", width=1)

                ),

                name=rotulo_faixa,

                showlegend=True

            ))

        fig_mapa.update_layout(

            height=560,

            margin=dict(t=0, r=0, b=44, l=0),

            paper_bgcolor="#FFFFFF",

            plot_bgcolor="#FFFFFF",

            annotations=anotacoes_mapa,

            legend=dict(

                title=dict(text="Incidencia /100 mil hab.", side="top"),

                orientation="h",

                yanchor="top",

                y=-0.02,

                xanchor="center",

                x=0.5,

                bgcolor="rgba(255,255,255,0.88)",

                bordercolor="#E6EBF0",

                borderwidth=1,

                font=dict(size=12)

            )

        )

        # Eixos ocultos; aspecto travado (lat ~ -2.5 -> distorcao lon/lat
        # desprezivel) para o mapa nao deformar.

        fig_mapa.update_xaxes(visible=False)

        fig_mapa.update_yaxes(

            visible=False,

            scaleanchor="x",

            scaleratio=1.0

        )

        st.plotly_chart(fig_mapa, width="stretch")

        st.caption(

            "Faixas: azul abaixo de 100 | verde 100-300 | amarelo acima de 300 /100 mil."

        )

    else:

        st.info("Sem dados de distrito para o mapa.")

# ---- Casos por distrito (barras horizontais) ----

with col_barras:

    st.markdown(

        "<div class='secao-titulo'>Casos por Distrito</div>",

        unsafe_allow_html=True

    )

    if not resumo_dist.empty:

        ordenado = resumo_dist.sort_values("NOTIFICADOS", ascending=True)

        fig_bar = go.Figure(go.Bar(

            x=ordenado["NOTIFICADOS"],

            y=[d.title() for d in ordenado["DISTRITO"]],

            orientation="h",

            marker=dict(

                color=ordenado["NOTIFICADOS"],

                colorscale=ESCALA_INCIDENCIA

            ),

            text=ordenado["NOTIFICADOS"],

            texttemplate="%{text}",

            textposition="outside",

            constraintext="none",

            cliponaxis=False

        ))

        # Folga a direita para o rotulo da maior barra (ex.: Coroadinho)
        # nao ser cortado.

        limite_x = float(max(ordenado["NOTIFICADOS"].max(), 1)) * 1.30

        fig_bar.update_layout(

            height=360,

            margin=dict(t=10, r=80, b=10, l=10),

            plot_bgcolor="#FFFFFF",

            paper_bgcolor="#FFFFFF",

            xaxis_title="Casos notificados"

        )

        fig_bar.update_xaxes(

            showgrid=True, gridcolor="#ECECEC", range=[0, limite_x]

        )

        st.plotly_chart(fig_bar, width="stretch")

    else:

        st.info("Sem dados de distrito.")

# =========================================================
# LINHA 6 : RANKING + INDICADORES E ALERTAS
# =========================================================

# ---- Ranking de distritos por incidencia (largura total) ----

st.markdown(

    "<div class='secao-titulo'>Ranking de Distritos - Maior Incidencia</div>",

    unsafe_allow_html=True

)

if not resumo_dist.empty:

    ranking = (

        resumo_dist.sort_values("INCIDENCIA", ascending=False)
        .reset_index(drop=True)

    )

    ranking.insert(0, "Pos.", ranking.index + 1)

    ranking_exibir = ranking.rename(columns={

        "DISTRITO": "Distrito",

        "NOTIFICADOS": "Notificados",

        "CONFIRMADOS": "Confirmados",

        "POPULACAO": "Populacao",

        "INCIDENCIA": "Incid./100k"

    })

    ranking_exibir["Distrito"] = ranking_exibir["Distrito"].str.title()

    # Formatacao no padrao brasileiro: ponto como separador de milhar
    # e virgula como separador decimal (item exigido pela SEMUS).

    for coluna_int in ("Notificados", "Confirmados"):

        ranking_exibir[coluna_int] = ranking_exibir[coluna_int].map(fmt_int)

    ranking_exibir["Populacao"] = ranking_exibir["Populacao"].map(
        lambda v: fmt_int(v) if pd.notna(v) else "—"
    )

    ranking_exibir["Incid./100k"] = ranking_exibir["Incid./100k"].map(
        lambda v: fmt_dec(v) if pd.notna(v) else "—"
    )

    st.dataframe(

        ranking_exibir,

        hide_index=True,

        width="stretch",

        height=360

    )

else:

    st.info("Sem dados para o ranking.")

st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

# ---- Indicadores epidemiologicos + alertas (linha abaixo do ranking) ----

col_ind, col_alerta = st.columns(2, gap="large")

with col_ind:

    st.markdown(

        "<div class='secao-titulo'>Indicadores Epidemiologicos</div>",

        unsafe_allow_html=True

    )

    st.markdown(

        f"""
        <div class="painel">
            <div class="ind-linha">
                <span class="ind-rotulo">Taxa de confirmacao</span>
                <span class="ind-valor" style="color:{COR_VERDE};">{fmt_dec(taxa_confirmacao, 1)}%</span>
            </div>
            <div class="ind-linha">
                <span class="ind-rotulo">Taxa de incidencia /100 mil</span>
                <span class="ind-valor" style="color:{COR_AZUL};">{fmt_dec(taxa_incidencia)}</span>
            </div>
            <div class="ind-linha">
                <span class="ind-rotulo">Letalidade</span>
                <span class="ind-valor" style="color:{COR_VERMELHO};">{fmt_dec(letalidade, 2)}%</span>
            </div>
            <div class="ind-linha" style="border-bottom:none;">
                <span class="ind-rotulo">Obitos pelo agravo</span>
                <span class="ind-valor" style="color:{COR_AZUL_ESCURO};">{fmt_int(total_obitos)}</span>
            </div>
        </div>
        """,

        unsafe_allow_html=True

    )

with col_alerta:

    st.markdown(

        "<div class='secao-titulo'>Alertas</div>",

        unsafe_allow_html=True

    )

    alertas = []

    # Alerta de letalidade.

    if total_obitos > 0:

        alertas.append((

            "vermelho",

            f"{fmt_int(total_obitos)} obito(s) pelo agravo - "
            f"letalidade de {fmt_dec(letalidade, 2)}%."

        ))

    # Alerta de distrito com maior incidencia.

    if not resumo_dist.empty:

        topo = resumo_dist.sort_values("INCIDENCIA", ascending=False).iloc[0]

        if pd.notna(topo["INCIDENCIA"]) and topo["INCIDENCIA"] > 0:

            alertas.append((

                "amarelo",

                f"Maior incidencia: {str(topo['DISTRITO']).title()} "
                f"({fmt_dec(topo['INCIDENCIA'])} /100 mil)."

            ))

    # Alerta de semana de pico.

    base_se_alerta = df.dropna(subset=["SEMANA_EPI"])

    if not base_se_alerta.empty:

        pico = base_se_alerta["SEMANA_EPI"].astype(int).value_counts()

        se_pico = int(pico.idxmax())

        alertas.append((

            "azul",

            f"Semana de pico: SE {se_pico:02d} "
            f"({fmt_int(int(pico.max()))} casos notificados)."

        ))

    # Alerta de baixa confirmacao.

    if total_notificados > 0 and taxa_confirmacao < 30:

        alertas.append((

            "amarelo",

            f"Taxa de confirmacao baixa ({fmt_dec(taxa_confirmacao, 1)}%) - "
            "muitos casos em investigacao."

        ))

    if not alertas:

        alertas.append((

            "verde",

            "Sem alertas criticos para o filtro atual."

        ))

    for cor, texto in alertas:

        st.markdown(

            f"<div class='alerta alerta-{cor}'>{texto}</div>",

            unsafe_allow_html=True

        )

# =========================================================
# RODAPE
# =========================================================

st.divider()

st.caption(

    f"Fonte: SINAN ({opcao_agravo}) | Populacao IBGE - "
    f"municipio {ano} e distritos {ano_pop_dist} | "
    "Confirmados, incidencia e letalidade sobre casos confirmados "
    "(STATUS_MS = CONFIRMADO) com criterio laboratorial ou "
    "clinico-epidemiologico."

)
