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
    # Datas (sem identificacao)
    "DT_NOTIFIC", "DT_ENCERRA", "DT_SIN_PRI",
    "SEM_NOT", "NU_ANO",
    # Classificacao
    "CLASSI_FIN", "DESC_CLASSI_FIN",
    "CRITERIO", "DESC_CRITERIO",
    "EVOLUCAO", "DESC_EVOLUCAO",
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
