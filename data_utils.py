"""
data_utils.py

Funções utilitárias para padronização e normalização de colunas de DataFrames.
Inclui slugify, mapeamento por candidatos e validação de colunas obrigatórias.
"""

import re
import unicodedata
import pandas as pd
from typing import Dict, List


def slugify_col(col: str) -> str:
    """
    Normaliza e converte o nome de uma coluna em formato 'slug'.

    Exemplo:
        "Preço de Custo" -> "preco_de_custo"

    Passos:
        1. Converte para string e remove espaços nas extremidades.
        2. Normaliza caracteres Unicode (acentos).
        3. Remove caracteres de combinação (acentos, etc.).
        4. Substitui tudo que não é alfanumérico por '_'.
        5. Remove '_' extras nas extremidades e converte para minúsculas.

    :param col: Nome da coluna
    :return: Nome da coluna slugificado
    """
    s = str(col).strip()
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r'[^0-9A-Za-z]+', '_', s)
    s = s.strip('_').lower()
    return s


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza todos os nomes de colunas de um DataFrame usando slugify_col.

    :param df: DataFrame original
    :return: Novo DataFrame com colunas normalizadas
    """
    df = df.copy()
    df.columns = [slugify_col(c) for c in df.columns]
    return df


def map_columns_by_candidates(df: pd.DataFrame, candidates: Dict[str, List[str]]) -> pd.DataFrame:
    """
    Mapeia colunas existentes para nomes canônicos usando listas de candidatos.

    Exemplo de uso:
        candidates = {
            "codigo_produto": ["cod_produto", "codigo", "id_produto"],
            "descricao_produto": ["desc_produto", "descricao"]
        }

    O primeiro candidato encontrado é renomeado para o nome canônico.

    :param df: DataFrame a ser renomeado
    :param candidates: dict com nome canônico -> lista de variações possíveis (slugified)
    :return: DataFrame renomeado
    """
    df = df.copy()
    cols_set = set(df.columns)
    rename = {}
    for canon, variants in candidates.items():
        for v in variants:
            if v in cols_set:
                rename[v] = canon
                break
    if rename:
        df = df.rename(columns=rename)
    return df


def ensure_required_columns(df: pd.DataFrame, required: List[str]):
    """
    Valida se o DataFrame contém todas as colunas obrigatórias.

    :param df: DataFrame a ser validado
    :param required: lista de nomes de colunas obrigatórias
    :raises ValueError: se alguma coluna obrigatória estiver ausente
    """
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"DataFrame precisa conter as colunas: {missing}")
