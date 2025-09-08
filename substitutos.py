import pandas as pd

class RecomendadorSubstitutoDB:
    """
    Classe para recomendação de produtos substitutos diretamente do banco de dados.

    Funcionalidades:
        - Recebe um código de produto para teste.
        - Verifica se o produto existe na tabela produtos.
        - Gera um DataFrame com:
            - Código do produto
            - Descrição do produto
            - Margem %
            - Estoque
        - Retorna substitutos ranqueados por similaridade de preço de custo.
    """

    def __init__(self, conn, codigo_teste: int):
        """
        :param conn: Conexão SQLAlchemy engine com o banco.
        :param codigo_teste: Código do produto que será usado como referência.
        """
        self.conn = conn  # aqui é o engine
        self.codigo_teste = codigo_teste
        self.df_produtos = self._carregar_produtos()
        self.produto_base = self._verificar_produto(codigo_teste)

    # ---------------- Carrega produtos e calcula margem ----------------
    def _carregar_produtos(self) -> pd.DataFrame:
        query = """
        SELECT 
            p.codigo_produto,
            p.descricao_produto,
            p.preco_custo,
            p.quantidade_estoque,
            c.codigo_categoria,
            AVG(i.valor_unitario) AS preco_venda_medio
        FROM produtos p
        LEFT JOIN itens_notas i ON i.produto_id = p.id
        LEFT JOIN categorias c ON c.id = p.categoria_id
        GROUP BY p.codigo_produto, p.descricao_produto, p.preco_custo, p.quantidade_estoque, c.codigo_categoria
        """
        # agora usamos engine (SQLAlchemy)
        df = pd.read_sql(query, self.conn)

        # Calcula margem
        df['margem_percent'] = ((df['preco_venda_medio'] - df['preco_custo']) / df['preco_venda_medio']) * 100
        df['margem_percent'] = (df['margem_percent'].fillna(0)).round(2)
        df['quantidade_estoque'] = df['quantidade_estoque'].fillna(0).astype(int)
        return df

    # ---------------- Verifica produto base ----------------
    def _verificar_produto(self, codigo: int) -> pd.Series | None:
        """
        Verifica se o produto existe e retorna suas informações.
        """
        produto = self.df_produtos[self.df_produtos['codigo_produto'] == codigo]
        if produto.empty:
            print(f"⚠️ Produto {codigo} não encontrado no banco.")
            return None
        return produto.iloc[0]

    # ---------------- Gera recomendação ----------------
    def recomendar_substitutos(self, n: int = 6) -> pd.DataFrame:
        if self.produto_base is None:
            return pd.DataFrame(columns=['codigo_produto', 'descricao_produto', 'margem_percent', 'quantidade_estoque'])

        # Tenta filtrar produtos da mesma categoria
        categoria_base = self.produto_base['codigo_categoria']
        df_substitutos = self.df_produtos[
            (self.df_produtos['quantidade_estoque'] > 0) &
            (self.df_produtos['codigo_produto'] != self.codigo_teste) &
            (self.df_produtos['codigo_categoria'] == categoria_base)
        ].copy()

        # Se não houver produtos na mesma categoria, usar todos disponíveis
        if df_substitutos.empty:
            df_substitutos = self.df_produtos[
                (self.df_produtos['quantidade_estoque'] > 0) &
                (self.df_produtos['codigo_produto'] != self.codigo_teste)
            ].copy()

        # Calcula similaridade baseada em preço de custo
        df_substitutos['similaridade'] = 1 - (
            abs(df_substitutos['preco_custo'] - self.produto_base['preco_custo']) / self.produto_base['preco_custo']
        )

        df_substitutos = df_substitutos.sort_values(
            by=['similaridade', 'preco_custo'],
            ascending=[False, False]
        )

        # Seleciona colunas finais e limita o número de recomendações
        resultado = df_substitutos[['codigo_produto', 'descricao_produto', 'margem_percent', 'quantidade_estoque']].head(n).reset_index(drop=True)
        return resultado
