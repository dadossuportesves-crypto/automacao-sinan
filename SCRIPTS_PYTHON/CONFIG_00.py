# ============================================================
# CONFIG_00.py
# CONFIGURACAO CENTRAL OFICIAL
# AUTOMACAO SINAN
# ============================================================

import os
from pathlib import Path

# ============================================================
# PASTA RAIZ — detecta automaticamente local vs Streamlit Cloud
# ============================================================

def _detectar_raiz():

    # Streamlit Cloud: /mount/src/automacao-sinan/
    cloud = Path("/mount/src/automacao-sinan")
    if cloud.exists():
        return cloud

    # Local Windows
    local = Path("C:/AUTOMACAO_SINAN")
    if local.exists():
        return local

    # Fallback: pasta pai do CONFIG_00.py
    return Path(__file__).resolve().parent.parent

PASTA_BASE = _detectar_raiz()

# ============================================================
# AGRAVO ATIVO
# ============================================================

AGRAVO_ATIVO = "DENGUE"

# ============================================================
# AGRAVOS PROCESSAMENTO AUTOMATICO
# ============================================================

AGRAVOS_PROCESSAMENTO = [

    "DENGUE",

    "CHIKUNGUNYA"

]

# ============================================================
# PASTAS PRINCIPAIS
# ============================================================

PASTA_DBF = PASTA_BASE / "DBF"

PASTA_RELATORIOS = PASTA_BASE / "RELATORIOS" / AGRAVO_ATIVO

PASTA_LOGS = PASTA_BASE / "LOGS"

PASTA_DICIONARIOS = PASTA_BASE / "DICIONARIOS"

# ============================================================
# PASTAS DBF POR AGRAVO
# ============================================================

PASTA_DBF_DENGUE = PASTA_DBF / "DENGUE"

PASTA_DBF_CHIK = PASTA_DBF / "CHIKUNGUNYA"

PASTA_DBF_NINDINET = PASTA_DBF / "NINDINET"

# ============================================================
# MUNICIPIO PADRAO — SAO LUIS / MA
# ============================================================

MUNICIPIO_PADRAO = "211130"

# ============================================================
# ANO EPIDEMIOLOGICO
# ============================================================

ANO_EPIDEMIOLOGICO = 2026

# ============================================================
# AGRAVOS
# ============================================================

AGRAVOS_ARBOVIROSES = [

    "DENGUE",

    "CHIKUNGUNYA"

]

AGRAVOS_ESPECIAIS = [

    "NINDINET"

]

AGRAVOS = AGRAVOS_ARBOVIROSES + AGRAVOS_ESPECIAIS

# ============================================================
# SISTEMAS
# ============================================================

SISTEMAS = [

    "SINAN_ONLINE",

    "NINDINET"

]

# ============================================================
# ARQUIVOS DBF
# ============================================================

ARQUIVO_DBF_DENGUE   = "DENGON2026.dbf"

ARQUIVO_DBF_CHIK     = "CHIKON2026.dbf"

ARQUIVO_DBF_NINDINET = "NINDINET2026.DBF"

# ============================================================
# MAPA AGRAVOS
# ============================================================

MAPA_AGRAVOS = {

    "DENGUE": {
        "pasta":   PASTA_DBF_DENGUE,
        "arquivo": ARQUIVO_DBF_DENGUE,
        "sistema": "SINAN_ONLINE"
    },

    "CHIKUNGUNYA": {
        "pasta":   PASTA_DBF_CHIK,
        "arquivo": ARQUIVO_DBF_CHIK,
        "sistema": "SINAN_ONLINE"
    },

    "NINDINET": {
        "pasta":   PASTA_DBF_NINDINET,
        "arquivo": ARQUIVO_DBF_NINDINET,
        "sistema": "NINDINET"
    }

}

# ============================================================
# DICIONARIOS
# ============================================================

ARQUIVO_DICIONARIO = (
    PASTA_DICIONARIOS /
    "CENTRAL_DICIONARIOS_EPIDEMIOLOGICOS.xlsx"
)

FORMATO_DICIONARIO = ".xlsx"

USAR_CSV = False

# ============================================================
# EXPORTACAO
# ============================================================

EXTENSAO_EXPORTACAO = ".xlsx"

FORMATO_EXPORTACAO  = "xlsx"

ENCODING_PADRAO     = "utf-8"

# ============================================================
# STATUS EPIDEMIOLOGICOS MS
# ============================================================

STATUS_CONFIRMADO  = "CONFIRMADO"

STATUS_DESCARTADO  = "DESCARTADO"

STATUS_INCONCLUSIVO = "INCONCLUSIVO"

STATUS_OUTRO_AGRAVO = "OUTRO_AGRAVO"

# ============================================================
# REGRAS MS
# ============================================================

STATUS_VALIDOS_INDICADOR = [STATUS_CONFIRMADO]

STATUS_EXCLUIR_INDICADOR = [STATUS_DESCARTADO, STATUS_INCONCLUSIVO]

# ============================================================
# COLUNAS IMPORTANTES
# ============================================================

COLUNA_CLASSIFICACAO    = "CLASSI_FIN"

COLUNA_MUNICIPIO        = "ID_MN_RESI"

COLUNA_EVOLUCAO         = "EVOLUCAO"

COLUNA_DATA_NOTIFICACAO = "DT_NOTIFIC"

COLUNA_DATA_ENCERRAMENTO = "DT_ENCERRA"

COLUNA_SEXO             = "CS_SEXO"

# ============================================================
# COLUNAS POSSIVEIS MUNICIPIO
# ============================================================

COLUNAS_MUNICIPIO = [

    "ID_MN_RESI",

    "CODMUNRES",

    "ID_MUNICIP"

]

# ============================================================
# VALORES INVALIDOS
# ============================================================

VALORES_INVALIDOS = {

    "",

    "nan",

    "None",

    "NaT",

    "NULL",

    "NAN"

}

# ============================================================
# CRIAR PASTAS (apenas em ambiente local — nao no Cloud)
# ============================================================

_CLOUD = Path("/mount/src").exists()

if not _CLOUD:

    PASTAS_SISTEMA = [
        PASTA_DBF,
        PASTA_DBF_DENGUE,
        PASTA_DBF_CHIK,
        PASTA_DBF_NINDINET,
        PASTA_RELATORIOS,
        PASTA_LOGS,
        PASTA_DICIONARIOS,
    ]

    for pasta in PASTAS_SISTEMA:

        pasta.mkdir(parents=True, exist_ok=True)

# ============================================================
# FINALIZACAO
# ============================================================

print("[OK] CONFIGURACOES CENTRALIZADAS CARREGADAS")
