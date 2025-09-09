# import pandas as pd
# ''

# class NotasCleaner:
#     def __init__(self):
#         # Não há atributos fixos no momento, mas mantemos para padrão
#         self.colunas_finais = [
#             "Numero nota fiscal", "Data da venda", "Código produto",
#             "Descrição do produto", "Quantidade do produto", "Valor unitário",
#             "Preço de custo", "Valor total produto", "Valor da nota"
#         ]

#     def clean(self, df: pd.DataFrame) -> pd.DataFrame:
#         print("[INFO] Iniciando limpeza da base de notas fiscais...")

#         try:
#             # 1. Remover registros com quantidades <= 0 ou valores unitários zerados
#             notas_com_problemas = set()
#             notas_com_problemas.update(df[df['Quantidade do produto'] <= 0]['Numero nota fiscal'].unique())
#             notas_com_problemas.update(df[df['Valor unitário'] == 0]['Numero nota fiscal'].unique())

#             df_limpo = df[~df['Numero nota fiscal'].isin(notas_com_problemas)].copy()
#             print(f"[INFO] Registros removidos por problemas em quantidade ou valor unitário: {len(notas_com_problemas)} notas.")

#             # 2. Remover registros com descrições ambíguas (vários códigos para mesma descrição)
#             descricoes_ambiguas = df_limpo.groupby('Descrição do produto')['Código produto'].nunique()
#             descricoes_ambiguas = descricoes_ambiguas[descricoes_ambiguas > 1].index.tolist()

#             df_limpo = df_limpo[~df_limpo['Descrição do produto'].isin(descricoes_ambiguas)]
#             print(f"[INFO] Produtos com descrições ambíguas removidos: {len(descricoes_ambiguas)} descrições.")

#             # 3. Calcular 'Valor total produto'
#             df_limpo["Valor total produto"] = (
#                 df_limpo["Quantidade do produto"] * df_limpo["Valor unitário"]
#             ).round(2)

#             # 4. Recalcular 'Valor da nota'
#             valor_por_nota = df_limpo.groupby('Numero nota fiscal')['Valor total produto'].sum().round(2)
#             df_limpo['Valor da nota'] = df_limpo['Numero nota fiscal'].map(valor_por_nota)

#             # 5. Arredondar colunas financeiras
#             df_limpo['Valor unitário'] = df_limpo['Valor unitário'].round(2)
#             df_limpo['Preço de custo'] = df_limpo['Preço de custo'].round(2)

#             # 6. Selecionar colunas finais
#             df_limpo = df_limpo[self.colunas_finais].copy()

#             print("[INFO] Limpeza de notas fiscais concluída com sucesso.")
#             return df_limpo

#         except Exception as e:
#             print(f"[ERRO] Falha durante a limpeza das notas fiscais: {e}")
#             raise

# notas_cleaner.py
import pandas as pd
from data_utils import normalize_columns, map_columns_by_candidates, ensure_required_columns

class NotasCleaner:
    def __init__(self):
        self.candidates = {
            "numero_nota_fiscal": ["numero_nota_fiscal", "numero_nota", "nota_fiscal", "n_nota", "num_nota"],
            "data_venda": ["data_da_venda", "data_venda", "data"],
            "codigo_produto": ["codigo_produto", "codigo", "cod_produto", "cod_prod"],
            "descricao_produto": ["descricao_do_produto", "descricao", "produto", "descricao_produto"],
            "quantidade_produto": ["quantidade_do_produto", "quantidade", "qtd", "qtd_produto"],
            "valor_unitario": ["valor_unitario", "valor_unit", "preco_unitario"],
            "preco_custo": ["preco_de_custo", "preco_custo", "custo"]
        }
        # colunas finais que o sistema costuma precisar
        self.final_cols = [
            "numero_nota_fiscal", "data_venda", "codigo_produto",
            "descricao_produto", "quantidade_produto", "valor_unitario",
            "preco_custo", "valor_total_produto", "valor_da_nota"
        ]
    # DEBUGG
    print("🚀 Entrou no notas!")

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        print("[INFO][NotasCleaner] Iniciando limpeza...")
        df = normalize_columns(df)
        df = map_columns_by_candidates(df, self.candidates)

        # conversões numéricas
        df["quantidade_produto"] = pd.to_numeric(df.reindex(columns=["quantidade_produto"])["quantidade_produto"], errors="coerce").fillna(0)
        df["valor_unitario"] = pd.to_numeric(df.get("valor_unitario", 0), errors="coerce").fillna(0.0)
        df["preco_custo"] = pd.to_numeric(df.get("preco_custo", 0), errors="coerce").fillna(0.0)

        # remover notas com quantidade <= 0 ou valor_unitario == 0
        if "numero_nota_fiscal" in df.columns:
            notas_problema = set()
            notas_problema.update(df[df["quantidade_produto"] <= 0]["numero_nota_fiscal"].unique())
            notas_problema.update(df[df["valor_unitario"] == 0]["numero_nota_fiscal"].unique())
            if notas_problema:
                print(f"[INFO] Removendo {len(notas_problema)} notas com problemas (quantidade/valor).")
            df = df[~df["numero_nota_fiscal"].isin(notas_problema)].copy()

        # remover descrições ambíguas (várias codigos para mesma descrição)
        if "descricao_produto" in df.columns and "codigo_produto" in df.columns:
            descricoes_amb = df.groupby("descricao_produto")["codigo_produto"].nunique()
            descricoes_amb = descricoes_amb[descricoes_amb > 1].index.tolist()
            if descricoes_amb:
                print(f"[INFO] Removendo {len(descricoes_amb)} descrições ambíguas.")
            df = df[~df["descricao_produto"].isin(descricoes_amb)].copy()

        # calcula valor_total_produto e valor_da_nota
        df["valor_total_produto"] = (df["quantidade_produto"] * df["valor_unitario"]).round(2)
        if "numero_nota_fiscal" in df.columns:
            soma_por_nota = df.groupby("numero_nota_fiscal")["valor_total_produto"].sum().round(2)
            df["valor_da_nota"] = df["numero_nota_fiscal"].map(soma_por_nota)
        else:
            df["valor_da_nota"] = df["valor_total_produto"]

        # garantir colunas finais (preenchendo com NaN se necessário)
        for c in self.final_cols:
            if c not in df.columns:
                df[c] = pd.NA

        # selecionar só as colunas finais na ordem desejada
        df = df[self.final_cols].copy()

        print("[INFO][NotasCleaner] Limpeza concluída.")
        return df

# DEBUGG
print("🚀 saiu no notas!")