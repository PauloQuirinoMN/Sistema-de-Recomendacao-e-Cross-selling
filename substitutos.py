
import pandas as pd

class RecomendadorSubstituto:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def recomendar(self, cod_produto_pesquisado: int, n_recomendacoes: int = 5):
        produto_base = self.df[self.df['Código produto'] == cod_produto_pesquisado]

        if produto_base.empty:
            return "❌ Produto não encontrado na base."

        produto_base = produto_base.iloc[0]

        if produto_base['Quantidade estoque'] > 0:
            return "✅ Produto está disponível em estoque. Recomendação não necessária."

        candidatos = self.df[
            (self.df['Código da categoria'] == produto_base['Código da categoria']) &
            (self.df['Código produto'] != cod_produto_pesquisado) &
            (self.df['Quantidade estoque'] > 0)
        ].copy()

        if candidatos.empty:
            return "⚠️ Nenhum substituto disponível no momento."

        candidatos = candidatos.drop_duplicates(subset='Código produto')
        candidatos['dist_preco'] = (candidatos['Valor unitário'] - produto_base['Valor unitário']).abs()
        candidatos['dist_margem'] = (candidatos['Margem %'] - produto_base['Margem %']).abs()

        recomendados = candidatos.sort_values(by=['dist_preco', 'dist_margem']).head(n_recomendacoes)

        return recomendados[[
            'Código produto', 'Descrição do produto', 'Valor unitário',
            'Margem %', 'Marca', 'Quantidade estoque'
        ]]
