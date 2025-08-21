import pandas as pd


class NotasCleaner:
    def __init__(self):
        # Não há atributos fixos no momento, mas mantemos para padrão
        self.colunas_finais = [
            "Numero nota fiscal", "Data da venda", "Código produto",
            "Descrição do produto", "Quantidade do produto", "Valor unitário",
            "Preço de custo", "Valor total produto", "Valor da nota"
        ]

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        print("[INFO] Iniciando limpeza da base de notas fiscais...")

        try:
            # 1. Remover registros com quantidades <= 0 ou valores unitários zerados
            notas_com_problemas = set()
            notas_com_problemas.update(df[df['Quantidade do produto'] <= 0]['Numero nota fiscal'].unique())
            notas_com_problemas.update(df[df['Valor unitário'] == 0]['Numero nota fiscal'].unique())

            df_limpo = df[~df['Numero nota fiscal'].isin(notas_com_problemas)].copy()
            print(f"[INFO] Registros removidos por problemas em quantidade ou valor unitário: {len(notas_com_problemas)} notas.")

            # 2. Remover registros com descrições ambíguas (vários códigos para mesma descrição)
            descricoes_ambiguas = df_limpo.groupby('Descrição do produto')['Código produto'].nunique()
            descricoes_ambiguas = descricoes_ambiguas[descricoes_ambiguas > 1].index.tolist()

            df_limpo = df_limpo[~df_limpo['Descrição do produto'].isin(descricoes_ambiguas)]
            print(f"[INFO] Produtos com descrições ambíguas removidos: {len(descricoes_ambiguas)} descrições.")

            # 3. Calcular 'Valor total produto'
            df_limpo["Valor total produto"] = (
                df_limpo["Quantidade do produto"] * df_limpo["Valor unitário"]
            ).round(2)

            # 4. Recalcular 'Valor da nota'
            valor_por_nota = df_limpo.groupby('Numero nota fiscal')['Valor total produto'].sum().round(2)
            df_limpo['Valor da nota'] = df_limpo['Numero nota fiscal'].map(valor_por_nota)

            # 5. Arredondar colunas financeiras
            df_limpo['Valor unitário'] = df_limpo['Valor unitário'].round(2)
            df_limpo['Preço de custo'] = df_limpo['Preço de custo'].round(2)

            # 6. Selecionar colunas finais
            df_limpo = df_limpo[self.colunas_finais].copy()

            print("[INFO] Limpeza de notas fiscais concluída com sucesso.")
            return df_limpo

        except Exception as e:
            print(f"[ERRO] Falha durante a limpeza das notas fiscais: {e}")
            raise
