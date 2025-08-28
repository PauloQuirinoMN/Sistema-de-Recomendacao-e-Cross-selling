import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder


class RecomendadorCrossSelling:
    """
    Classe responsável por gerar regras de associação (cross-selling)
    a partir da base de notas fiscais e produtos.
    """

    def __init__(self, df: pd.DataFrame):
        """
        Inicializa o recomendador com a base de dados.

        Parâmetros:
            df (pd.DataFrame): Base de vendas e produtos.
        """
        self.df = df

    def gerar_regras(
            self,
            cod_produto: int,
            min_support: float = 0.01,
            min_confidence: float = 0.15,
            min_lift: float = 1.1,
            max_len: int = 2
        ) -> pd.DataFrame:
        """
        Gera regras de associação para cross-selling para um produto específico.

        Parâmetros:
            cod_produto (int): Código do produto a analisar.
            min_support (float): Suporte mínimo para o Apriori.
            min_confidence (float): Confiança mínima para regras.
            min_lift (float): Lift mínimo para considerar uma associação válida.
            max_len (int): Número máximo de itens por conjunto.

        Retorna:
            pd.DataFrame: Regras de associação filtradas pelo produto.
        """
        # 🔹 Filtrar notas contendo o produto pesquisado
        notas_com_produto = self.df[self.df['Código produto'] == cod_produto]['Numero nota fiscal'].unique()
        df_filtrado = self.df[self.df['Numero nota fiscal'].isin(notas_com_produto)]

        # 🔹 Agrupar transações por nota fiscal
        transacoes = df_filtrado.groupby('Numero nota fiscal')['Código produto'].apply(list)

        # 🔹 One-hot encoding para Apriori
        te = TransactionEncoder()
        te_ary = te.fit_transform(transacoes)
        df_onehot = pd.DataFrame(te_ary, columns=te.columns_)

        # 🔹 Gerar conjuntos frequentes
        frequent_itemsets = apriori(df_onehot, min_support=min_support, use_colnames=True, max_len=max_len)
        if frequent_itemsets.empty:
            return pd.DataFrame()

        # 🔹 Gerar regras de associação usando "confidence"
        rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)

        # 🔹 Filtrar apenas regras com lift mínimo
        rules = rules[rules["lift"] >= min_lift]

        # 🔹 Filtrar regras relacionadas ao produto pesquisado
        produto_str = str(cod_produto)
        regras_produto = rules[
            rules["antecedents"].apply(lambda x: produto_str in str(x)) |
            rules["consequents"].apply(lambda x: produto_str in str(x))
        ]

        # 🔹 Ordenar para destacar as melhores regras
        regras_produto = regras_produto.sort_values(by=["confidence", "lift"], ascending=[False, False])

        return regras_produto


    def formatar_regras(self, df_regras: pd.DataFrame) -> pd.DataFrame:
        """
        Formata o DataFrame de regras para exibição amigável, incluindo
        descrição, valor, margem e estoque dos produtos.

        Parâmetros:
            df_regras (pd.DataFrame): DataFrame de regras gerado pelo Apriori.

        Retorna:
            pd.DataFrame: DataFrame formatado pronto para exibição.
        """
        # 🔹 Informações dos produtos
        produtos_info = self.df.drop_duplicates('Código produto').set_index('Código produto')[
            ['Descrição do produto', 'Valor unitário', 'Margem %', 'Quantidade estoque']
        ].to_dict('index')

        # 🔹 Funções auxiliares
        def extrair_codigo(itemset):
            return next(iter(itemset))

        def get_info(cod):
            return produtos_info.get(cod, {
                'Descrição do produto': 'PRODUTO NÃO ENCONTRADO',
                'Valor unitário': 0,
                'Margem %': 0,
                'Quantidade estoque': 0
            })

        # 🔹 Construir lista de resultados
        resultados = []
        for _, r in df_regras.iterrows():
            ant = extrair_codigo(r['antecedents'])
            cons = extrair_codigo(r['consequents'])
            info_ant = get_info(ant)
            info_cons = get_info(cons)

            resultados.append({
                'Antecedente': ant,
                'Descrição Antecedente': info_ant['Descrição do produto'],
                'Consequente': cons,
                'Descrição Consequente': info_cons['Descrição do produto'],
                'Aparece junto (%)': f"{r['support']*100:.2f}%",
                'Chance de comprar junto (%)': f"{r['confidence']*100:.2f}%",
            })

        return pd.DataFrame(resultados)
