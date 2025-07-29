# cross_selling.py

import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder

class RecomendadorCrossSelling:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def gerar_regras(self, cod_produto: int, min_support=0.01, min_threshold=1.0, max_len=3):
        notas_com_produto = self.df[self.df['Código produto'] == cod_produto]['Numero nota fiscal'].unique()
        df_filtrado = self.df[self.df['Numero nota fiscal'].isin(notas_com_produto)]
        transacoes = df_filtrado.groupby('Numero nota fiscal')['Código produto'].apply(list)

        te = TransactionEncoder()
        te_ary = te.fit_transform(transacoes)
        df_onehot = pd.DataFrame(te_ary, columns=te.columns_)

        frequent_itemsets = apriori(df_onehot, min_support=min_support, use_colnames=True, max_len=max_len)
        if frequent_itemsets.empty:
            return pd.DataFrame()


        rules = association_rules(frequent_itemsets, metric='lift', min_threshold=min_threshold)
        produto_str = str(cod_produto)

        regras_produto = rules[
            rules['antecedents'].apply(lambda x: produto_str in str(x)) |
            rules['consequents'].apply(lambda x: produto_str in str(x))
        ]
        return regras_produto

    def formatar_regras(self, df_regras):
        produtos_info = self.df.drop_duplicates('Código produto').set_index('Código produto')[
            ['Descrição do produto', 'Valor unitário', 'Margem %', 'Quantidade estoque']
        ].to_dict('index')

        def extrair_codigo(itemset):
            return next(iter(itemset))

        def get_info(cod):
            return produtos_info.get(cod, {
                'Descrição do produto': 'PRODUTO NÃO ENCONTRADO',
                'Valor unitário': 0,
                'Margem %': 0,
                'Quantidade estoque': 0
            })

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
                '% de Vendas com os Dois Produtos': f"{r['support']*100:.2f}%",
                'Chance de Compra Junto (%)': f"{r['confidence']*100:.2f}%",
            })

        return pd.DataFrame(resultados)
