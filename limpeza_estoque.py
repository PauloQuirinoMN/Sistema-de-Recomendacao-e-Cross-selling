import pandas as pd

class EstoqueCleaner:
    def __init__(self):
        self.colunas_utilizadas = [
            'Código', 'Produto', 'Código da categoria', 'Categoria',
            'Código da Marca', 'Marca', 'Preço de custo', 'Quantidade estoque'
        ]

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        print("[INFO] Iniciando limpeza da base de estoque...")

        # Tratamento de valores negativos e nulos em estoque
        df.loc[df["Quantidade estoque"] < 0, "Quantidade estoque"] = 0
        df["Quantidade estoque"] = df["Quantidade estoque"].fillna(0)

        # Selecionar colunas relevantes
        df = df[self.colunas_utilizadas].copy()

        # Remover produtos com múltiplos códigos
        produto_multiplos_codigos = df.groupby("Produto")["Código"].nunique()
        produtos_problemas = produto_multiplos_codigos[produto_multiplos_codigos > 1].index
        df = df[~df["Produto"].isin(produtos_problemas)].copy()

        # Remover categorias com múltiplos códigos
        categoria_multiplos_codigos = df.groupby("Categoria")["Código da categoria"].nunique()
        categorias_problemas = categoria_multiplos_codigos[categoria_multiplos_codigos > 1].index
        df = df[~df["Categoria"].isin(categorias_problemas)].copy()

        # Remover marcas com múltiplos códigos
        marca_multiplos_codigos = df.groupby("Marca")["Código da Marca"].nunique()
        marcas_problemas = marca_multiplos_codigos[marca_multiplos_codigos > 1].index
        df = df[~df["Marca"].isin(marcas_problemas)].copy()

        # Conversões finais
        df = df.astype({'Quantidade estoque': 'int64'})
        df["Preço de custo"] = df["Preço de custo"].round(2)
        df.rename(columns={"Código": "Código produto"}, inplace=True)

        print("[INFO] Limpeza concluída.")
        return df


