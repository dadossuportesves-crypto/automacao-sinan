# =========================================================
# PROJETO : AUTOMACAO SINAN
# ARQUIVO : FUNCOES_TRADUCAO.py
# OBJETIVO:
# Motor central epidemiologico de traducoes
# oficiais do SINAN.
# =========================================================

# =========================================================
# IMPORTACOES
# =========================================================

from pathlib import Path

import pandas as pd

# =========================================================
# IMPORTAR CONFIG
# =========================================================

from CONFIG_00 import (

    PASTA_DICIONARIOS,

    VALORES_INVALIDOS,

    ARQUIVO_DICIONARIO

)

# =========================================================
# IMPORTAR FUNCOES
# =========================================================

from FUNCOES_GERAIS import (

    escrever_log

)

# =========================================================
# MAPEAMENTO CENTRAL
# =========================================================

MAPEAMENTO_TRADUCOES = {

    "CLASSI_FIN": {

        "aba": "CLASSIFICACAO_FINAL",
        "codigo": "CODIGO",
        "descricao": "DESCRICAO"

    },

    "CRITERIO": {

        "aba": "CRITERIO_CONFIRMACAO",
        "codigo": "CODIGO",
        "descricao": "DESCRICAO"

    },

    "EVOLUCAO": {

        "aba": "EVOLUCAO",
        "codigo": "CODIGO",
        "descricao": "DESCRICAO"

    },

    "CS_SEXO": {

        "aba": "SEXO",
        "codigo": "CODIGO",
        "descricao": "DESCRICAO"

    },

    "CS_ESCOL_N": {

        "aba": "ESCOLARIDADE",
        "codigo": "CODIGO",
        "descricao": "DESCRICAO"

    },

    "CS_RACA": {

        "aba": "RACA_COR",
        "codigo": "CODIGO",
        "descricao": "DESCRICAO"

    },

    "CS_GESTANT": {

        "aba": "GESTANTE",
        "codigo": "CODIGO",
        "descricao": "DESCRICAO"

    },

    "ID_UNIDADE": {

        "aba": "UNIDADES",
        "codigo": "CODIGO",
        "descricao": "DESCRICAO"

    },

    "ID_MN_RESI": {

        "aba": "MUNICIPIO",
        "codigo": "CODIGO",
        "descricao": "DESCRICAO"

    },

    "ID_DISTRIT": {

        "aba": "DISTRITOS",
        "codigo": "CODIGO",
        "descricao": "DESCRICAO"

    },

    "TP_SISTEMA": {

        "aba": "VERSAO_SISTEMA",
        "codigo": "CODIGO",
        "descricao": "DESCRICAO"

    }

}

# =========================================================
# CACHE DICIONARIOS
# =========================================================

CACHE_DICIONARIOS = {}

# =========================================================
# VALIDAR DICIONARIO
# =========================================================

def validar_arquivo_dicionario():

    if not ARQUIVO_DICIONARIO.exists():

        raise FileNotFoundError(

            f"Dicionario nao encontrado: "
            f"{ARQUIVO_DICIONARIO}"

        )

# =========================================================
# PADRONIZAR CODIGO
# =========================================================

def padronizar_codigo(serie):

    return (

        serie
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
        .str.replace(".0", "", regex=False)

    )

# =========================================================
# LIMPAR DESCRICOES
# =========================================================

def limpar_descricao(serie):

    return (

        serie
        .fillna("NAO IDENTIFICADO")
        .astype(str)
        .str.strip()

    )

# =========================================================
# LER ABA DICIONARIO
# =========================================================

def ler_aba_dicionario(nome_aba):

    try:

        validar_arquivo_dicionario()

        # =================================================
        # CACHE
        # =================================================

        if nome_aba in CACHE_DICIONARIOS:

            return CACHE_DICIONARIOS[nome_aba]

        # =================================================
        # LEITURA
        # =================================================

        df = pd.read_excel(

            ARQUIVO_DICIONARIO,

            sheet_name=nome_aba,

            dtype=str

        )

        # =================================================
        # PADRONIZAR COLUNAS
        # =================================================

        df.columns = (

            df.columns
            .astype(str)
            .str.strip()
            .str.upper()

        )

        # =================================================
        # LIMPAR LINHAS VAZIAS
        # =================================================

        df = df.dropna(

            how="all"

        )

        # =================================================
        # CACHE
        # =================================================

        CACHE_DICIONARIOS[nome_aba] = df

        escrever_log(

            f"Dicionario carregado: {nome_aba}",

            tipo="EXECUCAO"

        )

        return df

    except Exception as erro:

        escrever_log(

            f"Erro lendo aba {nome_aba}: {erro}",

            tipo="ERROS"

        )

        return None

# =========================================================
# CRIAR MAPA
# =========================================================

def criar_mapa_traducao(

    df_dict,

    coluna_codigo,

    coluna_descricao

):

    try:

        df_dict = df_dict.copy()

        df_dict[coluna_codigo] = (

            padronizar_codigo(

                df_dict[coluna_codigo]

            )

        )

        df_dict[coluna_descricao] = (

            limpar_descricao(

                df_dict[coluna_descricao]

            )

        )

        mapa = dict(

            zip(

                df_dict[coluna_codigo],

                df_dict[coluna_descricao]

            )

        )

        return mapa

    except Exception as erro:

        escrever_log(

            f"Erro criando mapa: {erro}",

            tipo="ERROS"

        )

        return {}

# =========================================================
# APLICAR TRADUCAO
# =========================================================

def aplicar_traducao(

    df,

    coluna,

    nome_aba,

    coluna_codigo="CODIGO",

    coluna_descricao="DESCRICAO"

):

    try:

        # =================================================
        # VALIDAR COLUNA
        # =================================================

        if coluna not in df.columns:

            escrever_log(

                f"Coluna inexistente: {coluna}",

                tipo="ALERTAS"

            )

            return df

        # =================================================
        # LER DICIONARIO
        # =================================================

        df_dict = ler_aba_dicionario(

            nome_aba

        )

        if df_dict is None:

            return df

        # =================================================
        # VALIDAR ESTRUTURA
        # =================================================

        if coluna_codigo not in df_dict.columns:

            escrever_log(

                f"Coluna codigo inexistente "
                f"em {nome_aba}",

                tipo="ERROS"

            )

            return df

        if coluna_descricao not in df_dict.columns:

            escrever_log(

                f"Coluna descricao inexistente "
                f"em {nome_aba}",

                tipo="ERROS"

            )

            return df

        # =================================================
        # PADRONIZAR BASE
        # =================================================

        df = df.copy()

        df[coluna] = (

            padronizar_codigo(

                df[coluna]

            )

        )

        # =================================================
        # MAPA
        # =================================================

        mapa = criar_mapa_traducao(

            df_dict,

            coluna_codigo,

            coluna_descricao

        )

        # =================================================
        # NOVA COLUNA
        # =================================================

        coluna_desc = (

            f"DESC_{coluna}"

        )

        # =================================================
        # TRADUCAO
        # =================================================

        df[coluna_desc] = (

            df[coluna]
            .map(mapa)

        )

        # =================================================
        # PREENCHER NAO IDENTIFICADOS
        # =================================================

        df[coluna_desc] = (

            df[coluna_desc]
            .fillna("NAO IDENTIFICADO")

        )

        # =================================================
        # CONTROLE QUALIDADE
        # =================================================

        total_nao_identificado = (

            df[coluna_desc]
            .eq("NAO IDENTIFICADO")
            .sum()

        )

        if total_nao_identificado > 0:

            escrever_log(

                f"{coluna}: "
                f"{total_nao_identificado} "
                f"codigo(s) nao identificado(s)",

                tipo="ALERTAS"

            )

        escrever_log(

            f"Traducao aplicada: {coluna}",

            tipo="EXECUCAO"

        )

        return df

    except Exception as erro:

        escrever_log(

            f"Erro traducao {coluna}: {erro}",

            tipo="ERROS"

        )

        return df

# =========================================================
# APLICAR TODAS TRADUCOES
# =========================================================

def aplicar_traducoes(df):

    df = df.copy()

    print("\n===================================")
    print(" APLICANDO TRADUCOES ")
    print("===================================\n")

    for coluna, config in MAPEAMENTO_TRADUCOES.items():

        try:

            if coluna not in df.columns:

                continue

            print(

                f"[INFO] Traduzindo: {coluna}"

            )

            df = aplicar_traducao(

                df=df,

                coluna=coluna,

                nome_aba=config["aba"],

                coluna_codigo=config["codigo"],

                coluna_descricao=config["descricao"]

            )

            print(

                f"[OK] DESC_{coluna}"

            )

        except Exception as erro:

            print(

                f"[ERRO] {coluna}: {erro}"

            )

            escrever_log(

                f"Erro traducao {coluna}: {erro}",

                tipo="ERROS"

            )

    print("\n===================================")
    print(" TRADUCOES FINALIZADAS ")
    print("===================================\n")

    return df

# =========================================================
# CLASSIFICACAO FINAL PADRONIZADA (CACHE)
# =========================================================

def _classificacao_padronizada():

    # Le a aba CLASSIFICACAO_FINAL uma unica vez e devolve uma
    # copia com a coluna CODIGO ja padronizada, reaproveitando o
    # resultado via CACHE_DICIONARIOS para evitar repadronizar o
    # dicionario a cada chamada de obter_status_ms / obter_usar_indicador.

    chave = "CLASSIFICACAO_FINAL__PADRONIZADA"

    if chave in CACHE_DICIONARIOS:

        return CACHE_DICIONARIOS[chave]

    df_dict = ler_aba_dicionario(

        "CLASSIFICACAO_FINAL"

    )

    if df_dict is None:

        return None

    df_dict = df_dict.copy()

    df_dict["CODIGO"] = (

        padronizar_codigo(

            df_dict["CODIGO"]

        )

    )

    CACHE_DICIONARIOS[chave] = df_dict

    return df_dict

# =========================================================
# OBTER STATUS MS
# =========================================================

def obter_status_ms(df):

    """
    Extrai STATUS_MS da aba CLASSIFICACAO_FINAL.
    """

    try:

        if "CLASSI_FIN" not in df.columns:

            return df

        df_dict = _classificacao_padronizada()

        if df_dict is None:

            return df

        if "STATUS_MS" not in df_dict.columns:

            escrever_log(

                "STATUS_MS inexistente "
                "na CLASSIFICACAO_FINAL",

                tipo="ALERTAS"

            )

            return df

        # ================================================
        # PADRONIZAR
        # ================================================

        df["CLASSI_FIN"] = (

            padronizar_codigo(

                df["CLASSI_FIN"]

            )

        )

        # ================================================
        # MAPA
        # ================================================

        mapa = dict(

            zip(

                df_dict["CODIGO"],

                df_dict["STATUS_MS"]

            )

        )

        # ================================================
        # STATUS
        # ================================================

        df["STATUS_MS"] = (

            df["CLASSI_FIN"]
            .map(mapa)
            .fillna("NAO_CLASSIFICADO")

        )

        escrever_log(

            "STATUS_MS aplicado.",

            tipo="EXECUCAO"

        )

        return df

    except Exception as erro:

        escrever_log(

            f"Erro STATUS_MS: {erro}",

            tipo="ERROS"

        )

        return df

# =========================================================
# OBTER USAR_INDICADOR
# =========================================================

def obter_usar_indicador(df):

    """
    Define se o caso entra nos indicadores MS.
    """

    try:

        if "CLASSI_FIN" not in df.columns:

            return df

        df_dict = _classificacao_padronizada()

        if df_dict is None:

            return df

        if "USAR_INDICADOR" not in df_dict.columns:

            escrever_log(

                "USAR_INDICADOR inexistente.",

                tipo="ALERTAS"

            )

            return df

        # ================================================
        # PADRONIZAR
        # ================================================

        df["CLASSI_FIN"] = (

            padronizar_codigo(

                df["CLASSI_FIN"]

            )

        )

        # ================================================
        # MAPA
        # ================================================

        mapa = dict(

            zip(

                df_dict["CODIGO"],

                df_dict["USAR_INDICADOR"]

            )

        )

        # ================================================
        # APLICAR
        # ================================================

        df["USAR_INDICADOR"] = (

            df["CLASSI_FIN"]
            .map(mapa)
            .fillna("NAO")

        )

        escrever_log(

            "USAR_INDICADOR aplicado.",

            tipo="EXECUCAO"

        )

        return df

    except Exception as erro:

        escrever_log(

            f"Erro USAR_INDICADOR: {erro}",

            tipo="ERROS"

        )

        return df
