# data_utils.py
import re
import unicodedata
import pandas as pd
from typing import Dict, List

def slugify_col(col: str) -> str:
    s = str(col).strip()
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r'[^0-9A-Za-z]+', '_', s)
    s = s.strip('_').lower()
    return s

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [slugify_col(c) for c in df.columns]
    return df

def map_columns_by_candidates(df: pd.DataFrame, candidates: Dict[str, List[str]]) -> pd.DataFrame:
    """
    candidates: dict with canonical_name -> list of possible slugified variants
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
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"DataFrame precisa conter as colunas: {missing}")
