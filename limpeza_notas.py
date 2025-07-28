# notas.py

import pandas as pd

class NotasCleaner:
    def __init__(self, logger=None):
        self.logger = logger

    def _log(self, message, level="info"):
        if self.logger:
            getattr(self.logger, level)(message)
        else:
            print(f"[{level.upper()}] {message}")

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        try:
            self._log("Iniciando limpeza da base de notas fiscais")

            # 1. Remover registros com quantidades <= 0 ou valores unitários zerados
            notas_com_problemas = set()

            notas_com_problemas.update(df[df['Quantidade do produto'] <= 0]['Numero nota fiscal'].unique())
            notas_com_problemas.update(df[df['Valor unitário'] == 0]['Numero nota fiscal'].unique())

            df_limpo = df[~df['Numero nota fiscal'].isin(notas_com_problemas)].copy()

            # 2. Remover registros com descrições ambíguas (vários códigos para mesma descrição)
            descricoes_ambiguas = df_limpo.groupby('Descrição do produto')['Código produto'].nunique()
            descricoes_ambiguas = descricoes_ambiguas[descricoes_ambiguas > 1].index.tolist()

            df_limpo = df_limpo[~df_limpo['Descrição do produto'].isin(descricoes_ambiguas)]

            # 3. Calcular 'Valor total produto'
            df_limpo["Valor total produto"] = (
                df_limpo["Quantidade do produto"] * df_limpo["Valor unitário"]
            ).round(2)

            # 4. Recalcular 'Valor da nota'
            valor_por_nota = df_limpo.groupby('Numero nota fiscal')['Valor total produto'].sum().round(2)
            df_limpo['Valor da nota'] = df_limpo['Numero nota fiscal'].map(valor_por_nota)

            # 5. Arredondar colunas
            df_limpo['Valor unitário'] = df_limpo['Valor unitário'].round(2)
            df_limpo['Preço de custo'] = df_limpo['Preço de custo'].round(2)

            # 6. Selecionar colunas finais
            colunas_finais = [
                "Numero nota fiscal", "Data da venda", "Código produto",
                "Descrição do produto", "Quantidade do produto", "Valor unitário",
                "Preço de custo", "Valor total produto", "Valor da nota"
            ]
            df_limpo = df_limpo[colunas_finais]

            self._log("Limpeza da base de notas concluída com sucesso")
            return df_limpo

        except Exception as e:
            self._log(f"Erro ao limpar base de notas: {str(e)}", level="error")
            raise
