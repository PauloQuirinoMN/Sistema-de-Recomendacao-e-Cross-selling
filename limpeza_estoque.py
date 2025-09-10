# import pandas as pd

# class EstoqueCleaner:
#     """
#     Classe responsável por realizar a limpeza e padronização da base de dados de estoque.

#     Funcionalidades:
#     - Tratar valores negativos e nulos em estoque.
#     - Selecionar apenas colunas relevantes.
#     - Remover produtos, categorias e marcas com múltiplos códigos inconsistentes.
#     - Ajustar tipos de dados e renomear colunas finais.
#     """
#     ''

#     def __init__(self):
#         # Colunas utilizadas no processo de limpeza
#         self.colunas_utilizadas = [
#             'Código', 'Produto', 'Código da categoria', 'Categoria',
#             'Código da Marca', 'Marca', 'Preço de custo', 'Quantidade estoque'
#         ]

#     def clean(self, df: pd.DataFrame) -> pd.DataFrame:
#         """
#         Realiza a limpeza e padronização da base de estoque.

#         Args:
#             df (pd.DataFrame): DataFrame original de estoque.

#         Returns:
#             pd.DataFrame: DataFrame limpo e padronizado.
#         """
#         print("[INFO][EstoqueCleaner] Iniciando limpeza da base de estoque...")

#         # 🔹 1. Tratamento de valores inválidos em estoque
#         df.loc[df["Quantidade estoque"] < 0, "Quantidade estoque"] = 0
#         df["Quantidade estoque"] = df["Quantidade estoque"].fillna(0)

#         # 🔹 2. Selecionar colunas relevantes
#         df = df[self.colunas_utilizadas].copy()

#         # 🔹 3. Remover produtos com múltiplos códigos
#         produto_multiplos_codigos = df.groupby("Produto")["Código"].nunique()
#         produtos_problemas = produto_multiplos_codigos[produto_multiplos_codigos > 1].index
#         if not produtos_problemas.empty:
#             print(f"[WARN][EstoqueCleaner] Produtos removidos por múltiplos códigos: {len(produtos_problemas)}")
#         df = df[~df["Produto"].isin(produtos_problemas)].copy()

#         # 🔹 4. Remover categorias com múltiplos códigos
#         categoria_multiplos_codigos = df.groupby("Categoria")["Código da categoria"].nunique()
#         categorias_problemas = categoria_multiplos_codigos[categoria_multiplos_codigos > 1].index
#         if not categorias_problemas.empty:
#             print(f"[WARN][EstoqueCleaner] Categorias removidas por múltiplos códigos: {len(categorias_problemas)}")
#         df = df[~df["Categoria"].isin(categorias_problemas)].copy()

#         # 🔹 5. Remover marcas com múltiplos códigos
#         marca_multiplos_codigos = df.groupby("Marca")["Código da Marca"].nunique()
#         marcas_problemas = marca_multiplos_codigos[marca_multiplos_codigos > 1].index
#         if not marcas_problemas.empty:
#             print(f"[WARN][EstoqueCleaner] Marcas removidas por múltiplos códigos: {len(marcas_problemas)}")
#         df = df[~df["Marca"].isin(marcas_problemas)].copy()

#         # 🔹 6. Conversões finais
#         df = df.astype({'Quantidade estoque': 'int64'})
#         df["Preço de custo"] = df["Preço de custo"].round(2)
#         df.rename(columns={"Código": "Código produto"}, inplace=True)

#         print(f"[INFO][EstoqueCleaner] Limpeza concluída. Total de registros finais: {len(df)}")
#         return df
# estoque_cleaner.py

import pandas as pd
from data_utils import normalize_columns, map_columns_by_candidates
from typing import List

class EstoqueCleaner:
    def __init__(self):
        # candidates -> variantes slugificadas possíveis
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
        # colunas que vamos garantir no final (mínimo)
        self.required = ["codigo_produto", "descricao_produto", "preco_custo", "quantidade_estoque"]
    # DEBUGG
    print("🚀 Entrou no estoque!")

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        print("[INFO][EstoqueCleaner] Iniciando limpeza...")
        df = normalize_columns(df)
        df = map_columns_by_candidates(df, self.candidates)

        # garantias básicas / conversões
        if "quantidade_estoque" in df.columns:
            df["quantidade_estoque"] = pd.to_numeric(df["quantidade_estoque"], errors="coerce").fillna(0).astype(int)
        else:
            df["quantidade_estoque"] = 0

        if "preco_custo" in df.columns:
            df["preco_custo"] = pd.to_numeric(df["preco_custo"], errors="coerce").fillna(0.0).round(2)
        else:
            df["preco_custo"] = 0.0

        # remover produtos com múltiplos códigos (usa as colunas canônicas)
        if "produto" in df.columns and "codigo_produto" in df.columns:
            produto_multiplos = df.groupby("produto")["codigo_produto"].nunique()
            problemas = produto_multiplos[produto_multiplos > 1].index
            if len(problemas) > 0:
                print(f"[WARN] Produtos removidos por múltiplos códigos: {len(problemas)}")
                df = df[~df["produto"].isin(problemas)].copy()

        # outras validações opcionais: categoria/marca inconsistentes
        # ... (similar ao que você já fazia, usando os nomes canônicos)

        # garantir colunas mínimas (se desejar, pode lançar exceção)
        # aqui optamos por preencher colunas faltantes com NaNs / defaults
        for c in self.required:
            if c not in df.columns:
                df[c] = pd.NA

        print(f"[INFO][EstoqueCleaner] Limpeza concluída. Registros finais: {len(df)}")
        return df
# DEBUGG
    print("🚀 saiu no estoque!")