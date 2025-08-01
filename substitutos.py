import pandas as pd

class RecomendadorSubstituto:
    def __init__(self, df: pd.DataFrame):
        self.df = df.drop_duplicates(subset='Código produto')
        self.categorias_validas = df['Código da categoria'].unique()

    def recomendar(self, codigo_pesquisado: int, n_recomendacoes: int = 6):
        if codigo_pesquisado in self.df['Código produto'].values:
            return self._recomendar_por_produto(codigo_pesquisado, n_recomendacoes)
        elif codigo_pesquisado in self.categorias_validas:
            return self._recomendar_por_categoria(codigo_pesquisado, n_recomendacoes)
        else:
            print(f"⚠️ Código {codigo_pesquisado} não corresponde a produto ou categoria válida.")
            return self._recomendar_alternativas(n_recomendacoes)
    
    def _recomendar_por_produto(self, cod_produto: int, n: int):
        produto_base = self.df[self.df['Código produto'] == cod_produto].iloc[0]
        
        if produto_base['Quantidade estoque'] > 0:
            print(f"ℹ️ Produto {cod_produto} em estoque. Mostrando alternativas similares:")
        else:
            print(f"⚠️ Produto {cod_produto} sem estoque. Mostrando alternativas:")
        
        substitutos = self.df[
            (self.df['Código da categoria'] == produto_base['Código da categoria']) &
            (self.df['Código produto'] != cod_produto) &
            (self.df['Quantidade estoque'] > 0)
        ].copy()
        
        if not substitutos.empty:
            substitutos['similaridade'] = (
                0.7 * (1 - (substitutos['Valor unitário'] - produto_base['Valor unitário']).abs() / produto_base['Valor unitário']) +
                0.3 * (1 - (substitutos['Margem %'] - produto_base['Margem %']).abs())
            )
            return self._formatar_resultado(produto_base, substitutos.nsmallest(n, 'similaridade'))
        
        print("⚠️ Nenhum substituto na mesma categoria.")
        return self._formatar_resultado(produto_base, self._recomendar_alternativas(n))
    
    def _recomendar_por_categoria(self, cod_categoria: int, n: int):
        produtos_categoria = self.df[
            (self.df['Código da categoria'] == cod_categoria) &
            (self.df['Quantidade estoque'] > 0)
        ]
        
        if not produtos_categoria.empty:
            categoria_nome = produtos_categoria.iloc[0]['Categoria']
            print(f"ℹ️ Categoria {categoria_nome} encontrada.")
            return self._formatar_resultado(produtos_categoria.iloc[0], produtos_categoria.sample(min(n, len(produtos_categoria))))
        
        print(f"⚠️ Categoria {cod_categoria} sem produtos em estoque.")
        return self._formatar_resultado(None, self._recomendar_alternativas(n))
    
    def _recomendar_alternativas(self, n: int):
        alternativas = self.df[self.df['Quantidade estoque'] > 0].sample(min(n, len(self.df)))
        return alternativas
    
    def _formatar_resultado(self, produto_base, recomendacoes):
        """Formata a saída no padrão consistente"""
        if produto_base is not None:
            print(f"\n🔄 Produto pesquisado: {produto_base['Código produto']} ({produto_base['Descrição do produto']})")
        
        print("\n📦 Resultado da Recomendação de Substitutos:")
        
        cols = ['Código produto', 'Descrição do produto', 'Valor unitário', 
                'Margem %', 'Quantidade estoque', 'Categoria']
        
        recomendacoes = recomendacoes[cols].copy()
        recomendacoes['Valor unitário'] = recomendacoes['Valor unitário'].round(2)
        recomendacoes['Margem %'] = (recomendacoes['Margem %'] * 100).round(2)
        
        return recomendacoes