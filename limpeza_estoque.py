import pandas as pd
from data_utils import normalize_columns, map_columns_by_candidates
from typing import List
from capturar_log import LogCapture

class EstoqueCleaner:
    """
    Classe responsável por limpar e padronizar a base de dados de estoque.

    Funcionalidades:
    - Padroniza nomes de colunas usando variantes candidatas.
    - Converte valores de estoque e preço de custo.
    - Remove produtos com múltiplos códigos.
    - Garante que colunas mínimas existam, preenchendo NaN quando necessário.
    """
        

    def __init__(self, logger: LogCapture):
        # Dicionário de candidatos para padronização das colunas
        self.logger = logger
        self.candidates = {
            "codigo_produto": ["codigo_produto", "codigo", "cod_produto", "cod_prod"],
            "descricao_produto": ["produto", "descricao", "nome_produto"],
            "codigo_categoria": ["codigo_da_categoria", "codigo_categoria", "categoria_codigo", "cod_categoria"],
            "categoria": ["categoria", "nome_categoria"],
            "codigo_marca": ["codigo_da_marca", "codigo_marca", "marca_codigo", "cod_marca"],
            "marca": ["marca", "nome_marca"],
            "preco_custo": ["preco_de_custo", "preco_custo", "custo"],
            "quantidade_estoque": ["quantidade_estoque", "quantidade", "qtd", "qtd_estoque"]
        }

        # Colunas mínimas que o DataFrame final deve ter
        self.required = ["codigo_produto", "descricao_produto", "preco_custo", "quantidade_estoque"]

        # Debug
        self.logger.log("🚀 Inicializado limpeza do estoque .")

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpa e padroniza a base de estoque.

        Args:
            df (pd.DataFrame): DataFrame original de estoque.

        Returns:
            pd.DataFrame: DataFrame limpo e padronizado.
        """

        # 1️⃣ Normaliza nomes de colunas e mapeia para os padrões canônicos
        df = normalize_columns(df)
        df = map_columns_by_candidates(df, self.candidates)

        # 2️⃣ Conversões básicas e preenchimento de valores nulos
        df["quantidade_estoque"] = pd.to_numeric(df.get("quantidade_estoque", 0), errors="coerce").fillna(0).astype(int)
        df["preco_custo"] = pd.to_numeric(df.get("preco_custo", 0.0), errors="coerce").fillna(0.0).round(2)

        # 3️⃣ Remover espaços em branco nos nomes das colunas
        df.columns = df.columns.str.strip()

        # 4️⃣ Remover produtos com múltiplos códigos
        if "descricao_produto" in df.columns and "codigo_produto" in df.columns:
            produto_multiplos = df.groupby("descricao_produto")["codigo_produto"].nunique()
            problemas = produto_multiplos[produto_multiplos > 1].index
            if len(problemas) > 0:
                self.logger.log(f"Produtos removidos por múltiplos códigos: {len(problemas)}")
                df = df[~df["descricao_produto"].isin(problemas)].copy()

        # 5️⃣ Garantir colunas mínimas
        for c in self.required:
            if c not in df.columns:
                df[c] = pd.NA

        self.logger.log(f"Limpeza concluída. Total de registros finais: {len(df)}")
        return df
