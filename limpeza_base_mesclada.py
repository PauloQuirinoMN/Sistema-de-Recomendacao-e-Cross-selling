import pandas as pd


class BasePreparador:
    """
    Classe responsável por mesclar e preparar a base final de dados
    a partir das notas fiscais e do estoque já limpo.
    """
    ''

    def __init__(self):
        self.df_completo = None

    def preparar_base(self, df_estoque: pd.DataFrame, df_notas: pd.DataFrame) -> pd.DataFrame:
        """
        Realiza a preparação e limpeza final da base para análises e modelos.

        Parâmetros:
            df_estoque (pd.DataFrame): DataFrame de estoque limpo.
            df_notas (pd.DataFrame): DataFrame de notas fiscais limpo.

        Retorna:
            pd.DataFrame: Base final pronta para análise/modelagem.
        """

        print("[INFO] Iniciando preparação da base completa...")

        # 🔹 Mesclar notas com estoque
        df = pd.merge(
            df_notas,
            df_estoque[[
                "Código produto", "Código da categoria", "Categoria",
                "Código da Marca", "Marca", "Quantidade estoque"
            ]],
            on="Código produto",
            how="inner"
        )

        # 🔹 Remoções de registros inválidos
        df = df[~df["Preço de custo"].isna()]           # custo nulo
        df = df[df["Preço de custo"] != 0]              # custo zero
        df = df[df["Valor unitário"] != 0]              # valor unitário zero

        # 🔹 Cálculos de métricas financeiras
        df["Margem bruta"] = (df["Valor unitário"] - df["Preço de custo"]).round(2)
        df["Margem %"] = (df["Margem bruta"] / df["Valor unitário"]).round(2)
        df["Markup"] = (df["Valor unitário"] - df["Preço de custo"]).round(2)

        # 🔹 Conversões de tipos e datas
        df["Data da venda"] = pd.to_datetime(df["Data da venda"], format="%d/%m/%Y")
        df = df.astype({
            "Quantidade do produto": "int64",
            "Código da categoria": "int64",
            "Código da Marca": "int64",
            "Quantidade estoque": "int64"
        })

        # 🔹 Recalcular valores totais
        df["Valor total produto"] = df["Quantidade do produto"] * df["Valor unitário"]
        df["Valor da nota"] = df.groupby("Numero nota fiscal")["Valor total produto"].transform("sum")

        # 🔹 Validações adicionais
        for coluna in ["Quantidade do produto", "Valor unitário", "Preço de custo"]:
            df = df[df[coluna] >= 0]

        # Custo não pode ser maior que o preço de venda
        df = df[df["Preço de custo"] <= df["Valor unitário"]]

        # Excluir registros críticos
        df = df[
            (df["Preço de custo"] > 0) &
            (df["Valor da nota"] > 0) &
            (df["Valor total produto"] > 0)
        ]

        # 🔹 Salvar cópia final
        self.df_completo = df.copy()

        print("[INFO] Base preparada com sucesso.")
        return self.df_completo
