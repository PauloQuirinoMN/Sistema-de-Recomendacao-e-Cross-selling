# base_preparador.py

import pandas as pd

class BasePreparador:
    def __init__(self):
        self.df_completo = None

    def preparar_base(self, df_estoque: pd.DataFrame, df_notas: pd.DataFrame) -> pd.DataFrame:
        df = pd.merge(
            df_notas,
            df_estoque[["Código produto", "Código da categoria", "Categoria", "Código da Marca", "Marca", "Quantidade estoque"]],
            on='Código produto',
            how='inner'
        )

        # Remover notas com preço de custo nulo e removendo os valores zerados
        df = df[~df["Preço de custo"].isna()]
        df = df[df["Preço de custo"] != 0]

        # Remover notas com valor unitário zerado
        df = df[df["Valor unitário"] != 0]

        # Cálculo de margem e markup
        df["Margem bruta"] = (df["Valor unitário"] - df["Preço de custo"]).round(2)
        df["Margem %"] = (df["Margem bruta"] / df["Valor unitário"]).round(2)
        df["Markup"] = (df["Valor unitário"] - df["Preço de custo"]).round(2)

        # Tipos e datas
        df["Data da venda"] = pd.to_datetime(df["Data da venda"], format="%d/%m/%Y")
        df["Quantidade do produto"] = df["Quantidade do produto"].astype(int)
        df["Código da categoria"] = df["Código da categoria"].astype(int)
        df["Código da Marca"] = df["Código da Marca"].astype(int)
        df["Quantidade estoque"] = df["Quantidade estoque"].astype(int)

        # Recalcular valores
        df["Valor total produto"] = df["Quantidade do produto"] * df["Valor unitário"]
        df["Valor da nota"] = df.groupby("Numero nota fiscal")["Valor total produto"].transform("sum")

        # Remover notas com valores negativos
        colunas_verificar = ["Quantidade do produto", "Valor unitário", "Preço de custo"]
        for coluna in colunas_verificar:
            df = df[df[coluna] >= 0]

        # Remover notas com custo maior que o valor unitário
        df = df[df["Preço de custo"] <= df["Valor unitário"]]

        # Remover notas com valores críticos
        df = df[
            (df["Preço de custo"] > 0) &
            (df["Valor da nota"] > 0) &
            (df["Valor total produto"] > 0)
        ]

        self.df_completo = df.copy()
        return self.df_completo
