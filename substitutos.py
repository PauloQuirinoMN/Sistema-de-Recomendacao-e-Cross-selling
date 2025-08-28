import pandas as pd

class RecomendadorSubstituto:
    """
    Classe para recomendação de produtos substitutos.

    Funcionalidades:
        - Recomenda substitutos para um produto específico ou para uma categoria.
        - Calcula similaridade baseada em preço e margem.
        - Garante consistência na formatação da saída.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.drop_duplicates(subset='Código produto')
        self.categorias_validas = df['Código da categoria'].unique()

    def recomendar(self, codigo_pesquisado: int, n_recomendacoes: int = 6) -> pd.DataFrame:
        """
        Retorna os produtos substitutos para um código pesquisado.

        Se o código for produto, chama a recomendação por produto.
        Se o código for categoria, chama a recomendação por categoria.
        Caso contrário, sugere alternativas gerais.
        """
        if codigo_pesquisado in self.df['Código produto'].values:
            return self._recomendar_por_produto(codigo_pesquisado, n_recomendacoes)
        elif codigo_pesquisado in self.categorias_validas:
            return self._recomendar_por_categoria(codigo_pesquisado, n_recomendacoes)
        else:
            print(f"⚠️ Código {codigo_pesquisado} não corresponde a produto ou categoria válida.")
            return self._formatar_resultado(None, self._recomendar_alternativas(n_recomendacoes))

    # ---------------- Recomendação por produto ----------------
    def _recomendar_por_produto(self, cod_produto: int, n: int) -> pd.DataFrame:
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

        # 🔹 Remove duplicados por código
        substitutos = substitutos.drop_duplicates(subset='Código produto')

        if not substitutos.empty:
            # Calcula similaridade ponderando preço e margem
            substitutos['similaridade'] = (
                0.7 * (1 - (substitutos['Valor unitário'] - produto_base['Valor unitário']).abs() / produto_base['Valor unitário']) +
                0.3 * (1 - (substitutos['Margem %'] - produto_base['Margem %']).abs())
            )
            return self._formatar_resultado(produto_base, substitutos.nlargest(n, 'similaridade'))

        print("⚠️ Nenhum substituto na mesma categoria.")
        return self._formatar_resultado(produto_base, self._recomendar_alternativas(n))

    # ---------------- Recomendação por categoria ----------------
    def _recomendar_por_categoria(self, cod_categoria: int, n: int) -> pd.DataFrame:
        produtos_categoria = self.df[
            (self.df['Código da categoria'] == cod_categoria) &
            (self.df['Quantidade estoque'] > 0)
        ].copy()

        # 🔹 Remove duplicados por código
        produtos_categoria = produtos_categoria.drop_duplicates(subset='Código produto')

        if not produtos_categoria.empty:
            categoria_nome = produtos_categoria.iloc[0]['Categoria']
            print(f"ℹ️ Categoria {categoria_nome} encontrada.")
            return self._formatar_resultado(
                produtos_categoria.iloc[0], 
                produtos_categoria.sample(min(n, len(produtos_categoria)))
            )

        print(f"⚠️ Categoria {cod_categoria} sem produtos em estoque.")
        return self._formatar_resultado(None, self._recomendar_alternativas(n))

    # ---------------- Alternativas gerais ----------------
    def _recomendar_alternativas(self, n: int) -> pd.DataFrame:
        """Seleciona aleatoriamente produtos disponíveis como alternativas gerais"""
        alternativas = self.df[self.df['Quantidade estoque'] > 0].copy()
        alternativas = alternativas.drop_duplicates(subset='Código produto')
        return alternativas.sample(min(n, len(alternativas)))

    # ---------------- Formatação de resultado ----------------
    def _formatar_resultado(self, produto_base, recomendacoes: pd.DataFrame) -> pd.DataFrame:
        """
        Formata o DataFrame de recomendação para exibição ou inserção.
        - Valores monetários arredondados
        - Margem percentual em %
        - Colunas padronizadas
        """
        if produto_base is not None:
            print(f"\n🔄 Produto pesquisado: {produto_base['Código produto']} ({produto_base['Descrição do produto']})")
        else:
            print("\n📦 Resultado da Recomendação de Substitutos:")

        cols = ['Código produto', 'Descrição do produto', 'Valor unitário', 
                'Margem %', 'Quantidade estoque', 'Categoria']

        recomendacoes = recomendacoes[cols].copy().reset_index(drop=True)
        recomendacoes['Valor unitário'] = recomendacoes['Valor unitário'].round(2)
        recomendacoes['Margem %'] = (recomendacoes['Margem %'] * 100).round(2)

        return recomendacoes
