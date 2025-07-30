import pandas as pd

class RecomendadorSubstituto:
    def __init__(self, df: pd.DataFrame):
        self.df = df.drop_duplicates(subset='Código produto')  # Remove duplicatas pelo código do produto.

    def recomendar(self, cod_produto_pesquisado: int, n_recomendacoes: int = 6):
        """
        Recomenda produtos substitutos mesmo quando:
        - O produto não é encontrado
        - O produto está com estoque zerado
        - Não há substitutos perfeitos na mesma categoria
        
        Retorna sempre DataFrame com recomendações ou mensagem explicativa
        """
        # 1. Verifica se o produto existe na base
        produto_base = self.df[self.df['Código produto'] == cod_produto_pesquisado]
        
        if produto_base.empty:
            # Produto não encontrado - recomenda produtos aleatórios com estoque
            print(f"⚠️ Produto {cod_produto_pesquisado} não encontrado. Recomendando alternativas:")
            return self._recomendar_alternativas(n_recomendacoes)
        
        produto_base = produto_base.iloc[0]
        
        # 2. Verifica estoque do produto pesquisado
        if produto_base['Quantidade estoque'] > 0:
            print(f"ℹ️ Produto {cod_produto_pesquisado} em estoque. Mostrando alternativas similares:")
        
        # 3. Busca substitutos na mesma categoria com estoque
        substitutos = self.df[
            (self.df['Código da categoria'] == produto_base['Código da categoria']) &
            (self.df['Código produto'] != cod_produto_pesquisado) &
            (self.df['Quantidade estoque'] > 0)
        ].copy()
        
        if not substitutos.empty:
            # 4. Calcula similaridade (70% preço, 30% margem)
            substitutos['similaridade'] = (
                0.7 * (substitutos['Valor unitário'] - produto_base['Valor unitário']).abs() +
                0.3 * (substitutos['Margem %'] - produto_base['Margem %']).abs()
            )
            return substitutos.sort_values('similaridade').head(n_recomendacoes)[[
                'Código produto', 'Descrição do produto', 'Valor unitário',
                'Margem %', 'Quantidade estoque', 'Categoria'
            ]]
        
        # 5. Se não encontrou na mesma categoria, recomenda alternativas gerais
        print("⚠️ Nenhum substituto na mesma categoria. Recomendando alternativas:")
        return self._recomendar_alternativas(n_recomendacoes)
    
    def _recomendar_alternativas(self, n: int):
        """Recomenda produtos aleatórios com estoque quando não encontra substitutos ideais"""
        alternativas = self.df[self.df['Quantidade estoque'] > 0].sample(min(n, len(self.df)))
        return alternativas[[
            'Código produto', 'Descrição do produto', 'Valor unitário',
            'Margem %', 'Quantidade estoque', 'Categoria'
        ]]