# =========================================================
# PROJETO : AUTOMACAO SINAN
# ARQUIVO : DEBUG_UTILS.py
# OBJETIVO:
# Motor central de debug epidemiologico
# e rastreamento inteligente de erros.
# =========================================================

# =========================================================
# IMPORTACOES
# =========================================================

from pathlib import Path

from datetime import datetime

import traceback

# =========================================================
# IMPORTAR CONFIGURACOES
# =========================================================

from CONFIG_00 import PASTA_LOGS

# =========================================================
# PASTA DEBUG
# =========================================================

PASTA_DEBUG = (

    PASTA_LOGS /
    "DEBUG"

)

PASTA_DEBUG.mkdir(

    parents=True,
    exist_ok=True

)

# =========================================================
# FUNCAO ESCREVER DEBUG
# =========================================================

def escrever_debug(

    mensagem,
    tipo="DEBUG"

):

    try:

        data_hoje = datetime.now().strftime(
            "%Y_%m_%d"
        )

        arquivo_log = (

            PASTA_DEBUG /
            f"{tipo.lower()}_{data_hoje}.txt"

        )

        horario = datetime.now().strftime(
            "%H:%M:%S"
        )

        with open(

            arquivo_log,
            "a",
            encoding="utf-8"

        ) as log:

            log.write(
                f"[{horario}] {mensagem}\n"
            )

    except Exception as erro:

        print(
            f"[ERRO DEBUG] {erro}"
        )

# =========================================================
# CAPTURAR ERRO COMPLETO
# =========================================================

def capturar_erro(

    erro,
    script=None,
    funcao=None,
    tipo="ERRO_CRITICO"

):

    try:

        # =================================================
        # TRACEBACK COMPLETO
        # =================================================

        tb = traceback.extract_tb(
            erro.__traceback__
        )

        # =================================================
        # ULTIMA LINHA DO ERRO
        # =================================================

        ultima_linha = tb[-1]

        arquivo = ultima_linha.filename

        linha = ultima_linha.lineno

        funcao_erro = ultima_linha.name

        codigo = ultima_linha.line

        # =================================================
        # MENSAGEM FORMATADA
        # =================================================

        mensagem = f"""

=========================================================
TIPO:
{tipo}

SCRIPT:
{script if script else arquivo}

FUNCAO:
{funcao if funcao else funcao_erro}

LINHA:
{linha}

CODIGO:
{codigo}

ERRO:
{type(erro).__name__}

DETALHE:
{str(erro)}
=========================================================

"""

        # =================================================
        # PRINT TERMINAL
        # =================================================

        print(mensagem)

        # =================================================
        # SALVAR LOG
        # =================================================

        escrever_debug(

            mensagem,
            tipo=tipo

        )

    except Exception as erro_debug:

        print(
            f"[ERRO DEBUG INTERNO] {erro_debug}"
        )

# =========================================================
# ALERTA
# =========================================================

def alerta(

    mensagem,
    script=None

):

    texto = f"""

[ALERTA]

SCRIPT:
{script}

DETALHE:
{mensagem}

"""

    print(texto)

    escrever_debug(

        texto,
        tipo="ALERTA"

    )

# =========================================================
# QUALIDADE
# =========================================================

def qualidade(

    mensagem,
    script=None

):

    texto = f"""

[QUALIDADE]

SCRIPT:
{script}

DETALHE:
{mensagem}

"""

    print(texto)

    escrever_debug(

        texto,
        tipo="QUALIDADE"

    )

# =========================================================
# INCONSISTENCIA
# =========================================================

def inconsistencia(

    mensagem,
    script=None

):

    texto = f"""

[INCONSISTENCIA]

SCRIPT:
{script}

DETALHE:
{mensagem}

"""

    print(texto)

    escrever_debug(

        texto,
        tipo="INCONSISTENCIA"

    )

# =========================================================
# EXECUCAO
# =========================================================

def execucao(

    mensagem,
    script=None

):

    texto = f"""

[EXECUCAO]

SCRIPT:
{script}

DETALHE:
{mensagem}

"""

    print(texto)

    escrever_debug(

        texto,
        tipo="EXECUCAO"

    )