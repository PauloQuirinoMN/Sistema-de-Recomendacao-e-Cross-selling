import pandas as pd
import psycopg2
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder

class CrossSellingSimples:
    """
    Classe para gerar regras de cross-selling para um produto específico.
    Funciona direto com a base de notas e produtos do banco.
    """

    def __init__(self, conn):
        self.conn = conn

    # ---------------- Verifica se o produto existe ----------------
    def _verificar_produto(self, codigo: int) -> bool:
        query = "SELECT 1 FROM produtos WHERE codigo_produto = %s LIMIT 1"
        df = pd.read_sql(query, self.conn, params=(codigo,))
        return not df.empty

    # ---------------- Gera regras para um produto ----------------
    def gerar_regras(self, cod_produto: int, min_support: float = 0.0015,
                     min_confidence: float = 0.05, min_lift: float = 1.0,
                     max_len: int = 2, filtro_raros: float = 0.05) -> pd.DataFrame:

        # 🔹 Verifica se produto existe
        if not self._verificar_produto(cod_produto):
            print(f"⚠️ Produto {cod_produto} não encontrado na base.")
            return pd.DataFrame()

        # 🔹 Carrega notas e produtos
        df_notas = pd.read_sql(
            "SELECT nota_id AS numero_nota_fiscal, produto_id AS codigo_produto FROM itens_notas",
            self.conn
        )

        df_produtos = pd.read_sql(
            "SELECT codigo_produto, descricao_produto FROM produtos", self.conn
        )

        # 🔹 Filtra produtos muito raros
        freq_produtos = df_notas['codigo_produto'].value_counts()
        limite = freq_produtos.quantile(filtro_raros)  # 5% menos frequentes
        produtos_validos = freq_produtos[freq_produtos > limite].index
        df_notas_filtrado = df_notas[df_notas['codigo_produto'].isin(produtos_validos)]

        # 🔹 Agrupa transações por nota
        transacoes = df_notas_filtrado.groupby('numero_nota_fiscal')['codigo_produto'].apply(list)

        # 🔹 One-hot encoding
        te = TransactionEncoder()
        te_ary = te.fit_transform(transacoes)
        df_onehot = pd.DataFrame(te_ary, columns=te.columns_)

        # 🔹 Rodar Apriori
        frequent_itemsets = apriori(df_onehot, min_support=min_support, use_colnames=True, max_len=max_len)
        if frequent_itemsets.empty:
            print("⚠️ Nenhum itemset frequente encontrado.")
            return pd.DataFrame()

        # 🔹 Gerar regras
        rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)
        rules = rules[rules["lift"] >= min_lift]

        # 🔹 Filtra regras para o produto pesquisado
        regras_produto = rules[
            rules['antecedents'].apply(lambda x: cod_produto in x) |
            rules['consequents'].apply(lambda x: cod_produto in x)
        ]

        if regras_produto.empty:
            print(f"⚠️ Nenhuma regra encontrada para o produto {cod_produto}.")
            return pd.DataFrame()

        # 🔹 Formata resultado
        def extrair_codigo(itemset):
            return next(iter(itemset))

        resultados = []
        for _, r in regras_produto.iterrows():
            ant = extrair_codigo(r['antecedents'])
            cons = extrair_codigo(r['consequents'])
            ant_desc = df_produtos.loc[df_produtos['codigo_produto'] == ant, 'descricao_produto'].values[0]
            cons_desc = df_produtos.loc[df_produtos['codigo_produto'] == cons, 'descricao_produto'].values[0]

            resultados.append({
                'Antecedente': ant,
                'Descricao_Antecedente': ant_desc,
                'Consequente': cons,
                'Descricao_Consequente': cons_desc,
                'Suporte': r['support'],
                'Confiança (%)': r['confidence']*100,
                'Lift': r['lift']
            })

        # 🔹 Limpar memória
        del df_notas, df_produtos, df_notas_filtrado, transacoes, df_onehot, frequent_itemsets, rules, regras_produto

        return pd.DataFrame(resultados).sort_values(by='Confiança (%)', ascending=False).reset_index(drop=True)
