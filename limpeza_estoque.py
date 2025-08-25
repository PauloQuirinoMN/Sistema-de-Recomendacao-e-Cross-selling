import pandas as pd

class EstoqueCleaner:
    """
    Classe responsável por realizar a limpeza e padronização da base de dados de estoque.

    Funcionalidades:
    - Tratar valores negativos e nulos em estoque.
    - Selecionar apenas colunas relevantes.
    - Remover produtos, categorias e marcas com múltiplos códigos inconsistentes.
    - Ajustar tipos de dados e renomear colunas finais.
    """
    ''

    def __init__(self):
        # Colunas utilizadas no processo de limpeza
        self.colunas_utilizadas = [
            'Código', 'Produto', 'Código da categoria', 'Categoria',
            'Código da Marca', 'Marca', 'Preço de custo', 'Quantidade estoque'
        ]

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Realiza a limpeza e padronização da base de estoque.

        Args:
            df (pd.DataFrame): DataFrame original de estoque.

        Returns:
            pd.DataFrame: DataFrame limpo e padronizado.
        """
        print("[INFO][EstoqueCleaner] Iniciando limpeza da base de estoque...")

        # 🔹 1. Tratamento de valores inválidos em estoque
        df.loc[df["Quantidade estoque"] < 0, "Quantidade estoque"] = 0
        df["Quantidade estoque"] = df["Quantidade estoque"].fillna(0)

        # 🔹 2. Selecionar colunas relevantes
        df = df[self.colunas_utilizadas].copy()

        # 🔹 3. Remover produtos com múltiplos códigos
        produto_multiplos_codigos = df.groupby("Produto")["Código"].nunique()
        produtos_problemas = produto_multiplos_codigos[produto_multiplos_codigos > 1].index
        if not produtos_problemas.empty:
            print(f"[WARN][EstoqueCleaner] Produtos removidos por múltiplos códigos: {len(produtos_problemas)}")
        df = df[~df["Produto"].isin(produtos_problemas)].copy()

        # 🔹 4. Remover categorias com múltiplos códigos
        categoria_multiplos_codigos = df.groupby("Categoria")["Código da categoria"].nunique()
        categorias_problemas = categoria_multiplos_codigos[categoria_multiplos_codigos > 1].index
        if not categorias_problemas.empty:
            print(f"[WARN][EstoqueCleaner] Categorias removidas por múltiplos códigos: {len(categorias_problemas)}")
        df = df[~df["Categoria"].isin(categorias_problemas)].copy()

        # 🔹 5. Remover marcas com múltiplos códigos
        marca_multiplos_codigos = df.groupby("Marca")["Código da Marca"].nunique()
        marcas_problemas = marca_multiplos_codigos[marca_multiplos_codigos > 1].index
        if not marcas_problemas.empty:
            print(f"[WARN][EstoqueCleaner] Marcas removidas por múltiplos códigos: {len(marcas_problemas)}")
        df = df[~df["Marca"].isin(marcas_problemas)].copy()

        # 🔹 6. Conversões finais
        df = df.astype({'Quantidade estoque': 'int64'})
        df["Preço de custo"] = df["Preço de custo"].round(2)
        df.rename(columns={"Código": "Código produto"}, inplace=True)

        print(f"[INFO][EstoqueCleaner] Limpeza concluída. Total de registros finais: {len(df)}")
        return df
