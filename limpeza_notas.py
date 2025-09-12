import pandas as pd
from data_utils import normalize_columns, map_columns_by_candidates, ensure_required_columns
from capturar_log import LogCapture

class NotasCleaner:
    """
    Classe responsável por limpar e padronizar a base de notas fiscais.

    Funcionalidades:
    - Padroniza nomes de colunas usando variantes candidatas.
    - Converte valores de quantidade, preço unitário e custo.
    - Remove notas com problemas (quantidade <= 0 ou valor unitário zerado).
    - Remove descrições ambíguas (mesma descrição com múltiplos códigos).
    - Calcula valor total por produto e valor da nota.
    - Garante que todas as colunas finais existam no DataFrame.
    """

    def __init__(self, logger: LogCapture):
        self.logger = logger
        # Dicionário de candidatos para padronização das colunas
        self.candidates = {
            "numero_nota_fiscal": ["numero_nota_fiscal", "numero_nota", "nota_fiscal", "n_nota", "num_nota"],
            "data_venda": ["data_da_venda", "data_venda", "data"],
            "codigo_produto": ["codigo_produto", "codigo", "cod_produto", "cod_prod"],
            "descricao_produto": ["descricao_do_produto", "descricao", "produto", "descricao_produto"],
            "quantidade_produto": ["quantidade_do_produto", "quantidade", "qtd", "qtd_produto"],
            "valor_unitario": ["valor_unitario", "valor_unit", "preco_unitario"],
            "preco_custo": ["preco_de_custo", "preco_custo", "custo"]
        }

        # Colunas finais que o DataFrame final deve ter
        self.final_cols = [
            "numero_nota_fiscal", "data_venda", "codigo_produto",
            "descricao_produto", "quantidade_produto", "valor_unitario",
            "preco_custo", "valor_total_produto", "valor_da_nota"
        ]

        # Debug
        self.logger.log("🚀 Inicializado limpeza das Notas .")

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpa e padroniza a base de notas fiscais.

        Args:
            df (pd.DataFrame): DataFrame original de notas fiscais.

        Returns:
            pd.DataFrame: DataFrame limpo e padronizado.
        """
        # 1️⃣ Normaliza nomes de colunas e mapeia para os padrões canônicos
        df = normalize_columns(df)
        df = map_columns_by_candidates(df, self.candidates)

        # 2️⃣ Conversões numéricas
        df["quantidade_produto"] = pd.to_numeric(df.get("quantidade_produto", 0), errors="coerce").fillna(0)
        df["valor_unitario"] = pd.to_numeric(df.get("valor_unitario", 0), errors="coerce").fillna(0)
        df["preco_custo"] = pd.to_numeric(df.get("preco_custo", 0), errors="coerce").fillna(0.0)

        # 3️⃣ Remover notas com problemas (quantidade <= 0 ou valor_unitario == 0)
        if "numero_nota_fiscal" in df.columns:
            notas_problema = set(df[df["quantidade_produto"] <= 0]["numero_nota_fiscal"].unique())
            notas_problema.update(df[df["valor_unitario"] == 0]["numero_nota_fiscal"].unique())
            if notas_problema:
                self.logger.log(f"Removendo {len(notas_problema)} notas com problemas (quantidade/valor).")
            df = df[~df["numero_nota_fiscal"].isin(notas_problema)].copy()

        # 4️⃣ Remover descrições ambíguas (várias códigos para mesma descrição)
        if "descricao_produto" in df.columns and "codigo_produto" in df.columns:
            descricoes_amb = df.groupby("descricao_produto")["codigo_produto"].nunique()
            descricoes_amb = descricoes_amb[descricoes_amb > 1].index.tolist()
            if descricoes_amb:
                self.logger.log(f"Removendo {len(descricoes_amb)} descrições ambíguas.")
            df = df[~df["descricao_produto"].isin(descricoes_amb)].copy()

        # 5️⃣ Calcular valor_total_produto e valor_da_nota
        df["valor_total_produto"] = (df["quantidade_produto"] * df["valor_unitario"]).round(2)
        if "numero_nota_fiscal" in df.columns:
            soma_por_nota = df.groupby("numero_nota_fiscal")["valor_total_produto"].sum().round(2)
            df["valor_da_nota"] = df["numero_nota_fiscal"].map(soma_por_nota)
        else:
            df["valor_da_nota"] = df["valor_total_produto"]

        # 6️⃣ Garantir colunas finais (preenchendo com NaN se necessário)
        for c in self.final_cols:
            if c not in df.columns:
                df[c] = pd.NA

        # 7️⃣ Selecionar apenas as colunas finais na ordem desejada
        df = df[self.final_cols].copy()

        self.logger.log(f"Limpeza concluída. Total de registros finais: {len(df)}")
        return df
