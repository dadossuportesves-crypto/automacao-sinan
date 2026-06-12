# =========================================================
# PROJETO : AUTOMACAO SINAN
# SCRIPT  : 24_EXPORTAR_GITHUB.py
# OBJETIVO:
# Exportar base processada (sem dados pessoais) para o
# GitHub para alimentar o dashboard online.
#
# Rodado automaticamente apos 21_AGENTE_SINAN.py (05h).
#
# USO MANUAL:
#   cd C:\AUTOMACAO_SINAN
#   .venv\Scripts\python SCRIPTS_PYTHON\24_EXPORTAR_GITHUB.py
# =========================================================

import sys
import subprocess
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd

# =========================================================
# CAMINHOS
# =========================================================

PASTA_RAIZ    = Path("C:/AUTOMACAO_SINAN")
PASTA_SCRIPTS = PASTA_RAIZ / "SCRIPTS_PYTHON"
PASTA_LOGS    = PASTA_RAIZ / "LOGS"
PASTA_DADOS   = PASTA_RAIZ / "DASHBOARD" / "data"

for p in [PASTA_LOGS, PASTA_DADOS]:
    p.mkdir(parents=True, exist_ok=True)

if str(PASTA_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PASTA_SCRIPTS))

# =========================================================
# LOG
# =========================================================

LOG_FILE = PASTA_LOGS / f"EXPORTAR_GITHUB_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("EXPORTAR_GITHUB")

# =========================================================
# IMPORTAR MODULOS DO PROJETO
# =========================================================

from CONFIG_00 import MAPA_AGRAVOS, AGRAVOS_ARBOVIROSES
from FUNCOES_GERAIS import ler_dbf, preparar_base

# =========================================================
# COLUNAS PERMITIDAS (sem dados pessoais — LGPD)
# =========================================================

COLUNAS_PERMITIDAS = [
    # Identificacao anonima
    "AGRAVO",
    # Datas e variaveis temporais (sem identificacao)
    "DT_NOTIFIC", "DT_ENCERRA", "DT_SIN_PRI",
    "SEM_NOT", "NU_ANO", "ANO_EPI", "SEMANA_EPI", "MES",
    # Demografico derivado
    "IDADE_ANOS", "FAIXA_ETARIA",
    # Geografico derivado
    "DISTRITO", "OBITO_AGRAVO",
    # Classificacao
    "CLASSI_FIN", "DESC_CLASSI_FIN",
    "CRITERIO", "DESC_CRITERIO",
    "EVOLUCAO", "DESC_EVOLUCAO",
    "STATUS_MS",
    # Demografico agregado (sem nome, CPF, endereco)
    "CS_SEXO", "DESC_CS_SEXO",
    "NU_IDADE_N",
    "CS_ESCOL_N", "DESC_CS_ESCOL_N",
    "CS_RACA", "DESC_CS_RACA",
    "CS_GESTANT", "DESC_CS_GESTANT",
    # Geografico agregado (sem endereco completo)
    "ID_DISTRIT", "DESC_ID_DISTRIT",
    "ID_MN_RESI", "DESC_ID_MN_RESI",
    # Sistema
    "TP_SISTEMA", "DESC_TP_SISTEMA",
    "ID_UNIDADE", "DESC_ID_UNIDADE",
]

# =========================================================
# PROCESSAR AGRAVO
# =========================================================

def processar_agravo(agravo):

    cfg = MAPA_AGRAVOS.get(agravo)
    if not cfg:
        return None

    pasta = cfg["pasta"]
    arquivos = sorted(
        list(pasta.glob("*.dbf")) + list(pasta.glob("*.DBF"))
    )

    if not arquivos:
        log.warning(f"Nenhum DBF: {agravo}")
        return None

    log.info(f"Lendo: {arquivos[0].name}")
    df = ler_dbf(arquivos[0])

    if df is None or df.empty:
        return None

    df = preparar_base(df, aplicar_filtro_municipio=True)

    if df is None or df.empty:
        return None

    df["AGRAVO"] = agravo

    # Calcular colunas temporais derivadas
    if "DT_NOTIFIC" in df.columns:
        df["DT_NOTIFIC"] = pd.to_datetime(df["DT_NOTIFIC"], errors="coerce")
        iso = df["DT_NOTIFIC"].dt.isocalendar()
        df["ANO_EPI"]    = iso.year.astype("Int64")
        df["SEMANA_EPI"] = iso.week.astype("Int64")
        df["MES"]        = df["DT_NOTIFIC"].dt.month.astype("Int64")

    # Calcular faixa etaria
    if "NU_IDADE_N" in df.columns:

        def _idade_em_anos(v):
            try:
                v = int(v)
                tp = v // 1000
                vl = v % 1000
                if tp == 4: return vl
                if tp == 3: return 0
                return 0
            except Exception:
                return None

        ORDEM_FAIXAS = [
            "< 1 ano","1-4","5-9","10-14","15-19","20-29",
            "30-39","40-49","50-59","60-69","70-79","80+"
        ]

        def _faixa_etaria(anos):
            try:
                a = int(anos)
                if a < 1:   return "< 1 ano"
                if a <= 4:  return "1-4"
                if a <= 9:  return "5-9"
                if a <= 14: return "10-14"
                if a <= 19: return "15-19"
                if a <= 29: return "20-29"
                if a <= 39: return "30-39"
                if a <= 49: return "40-49"
                if a <= 59: return "50-59"
                if a <= 69: return "60-69"
                if a <= 79: return "70-79"
                return "80+"
            except Exception:
                return None

        df["IDADE_ANOS"]   = df["NU_IDADE_N"].map(_idade_em_anos)
        df["FAIXA_ETARIA"] = df["IDADE_ANOS"].map(_faixa_etaria)

    # Manter apenas colunas permitidas que existem no df
    colunas_ok = [c for c in COLUNAS_PERMITIDAS if c in df.columns]
    df = df[colunas_ok].copy()

    log.info(f"[OK] {agravo}: {len(df)} registros, {len(df.columns)} colunas")
    return df

# =========================================================
# PUSH PARA GITHUB
# =========================================================

def push_github(arquivo):

    log.info("Enviando para GitHub ...")

    try:
        caminho_relativo = str(arquivo.relative_to(PASTA_RAIZ)).replace("\\", "/")

        cmds = [
            ["git", "-C", str(PASTA_RAIZ), "add", caminho_relativo],
            ["git", "-C", str(PASTA_RAIZ), "commit", "-m",
             f"Dados atualizados {datetime.now().strftime('%d/%m/%Y %H:%M')}"],
            ["git", "-C", str(PASTA_RAIZ), "push"],
        ]

        for cmd in cmds:
            resultado = subprocess.run(cmd, capture_output=True, text=True)
            if resultado.returncode != 0:
                if "nothing to commit" in resultado.stdout + resultado.stderr:
                    log.info("Sem mudancas — push nao necessario.")
                    return True
                log.warning(f"Git: {resultado.stderr.strip()}")

        log.info("[OK] Dados enviados para GitHub")
        return True

    except Exception as e:
        log.error(f"Erro no push: {e}")
        return False

# =========================================================
# MAIN
# =========================================================

def main():

    log.info("\n" + "="*50)
    log.info("  EXPORTAR GITHUB — INICIO")
    log.info(f"  {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    log.info("="*50)

    quadros = []

    for agravo in AGRAVOS_ARBOVIROSES:
        df = processar_agravo(agravo)
        if df is not None:
            quadros.append(df)

    if not quadros:
        log.error("Nenhum dado para exportar.")
        sys.exit(1)

    base = pd.concat(quadros, ignore_index=True)

    # Exportar parquet (leve e rapido)
    arquivo = PASTA_DADOS / "BASE_DASHBOARD.parquet"
    base.to_parquet(arquivo, index=False)
    log.info(f"[OK] Parquet exportado: {arquivo} ({arquivo.stat().st_size // 1024} KB)")

    push_github(arquivo)

    log.info("\n" + "="*50)
    log.info("  EXPORTAR GITHUB — CONCLUIDO")
    log.info("="*50)


if __name__ == "__main__":
    main()
