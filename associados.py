import gc
from typing import Optional, Any, List
import numpy as np
import pandas as pd
import scipy.sparse as sp
from mlxtend.frequent_patterns import fpgrowth, association_rules

class CrossSellingSimples:
    """
    Gera regras de cross-selling a partir de um DataFrame de notas.
    Não salva em banco — retorna um DataFrame com as regras ordenadas por 'lift'.

    Parâmetros do construtor:
    - df_notas: DataFrame com pelo menos as colunas [codigo_nota_col, codigo_prod_col]
    - df_produtos (opcional): DataFrame com colunas [prod_code_col, prod_desc_col] para enriquecer resultados
    - codigo_nota_col, codigo_prod_col: nomes das colunas em df_notas
    - prod_code_col e prod_desc_col: nomes das colunas em df_produtos
    """

    def __init__(
        self,
        df_notas: pd.DataFrame,
        df_produtos: Optional[pd.DataFrame] = None,
        codigo_nota_col: str = "numero_nota_fiscal",
        codigo_prod_col: str = "codigo_produto",
        prod_code_col: str = "codigo_produto",
        prod_desc_col: str = "descricao_produto"
    ):
        self.df_notas = df_notas.copy()
        self.df_produtos = df_produtos.copy() if df_produtos is not None else None
        self.codigo_nota_col = codigo_nota_col
        self.codigo_prod_col = codigo_prod_col
        self.prod_code_col = prod_code_col
        self.prod_desc_col = prod_desc_col

        # Validação rápida das colunas obrigatórias
        if self.codigo_nota_col not in self.df_notas.columns or self.codigo_prod_col not in self.df_notas.columns:
            raise ValueError(
                f"df_notas precisa conter as colunas '{self.codigo_nota_col}' e '{self.codigo_prod_col}'"
            )

    # ---------------- Filtro por frequência mínima ----------------
    def _aplicar_min_freq(self, min_freq: Optional[int]) -> pd.DataFrame:
        """
        Filtra df_notas removendo produtos que aparecem menos que min_freq vezes.
        """
        if min_freq is None:
            return self.df_notas

        freq = self.df_notas[self.codigo_prod_col].value_counts()
        produtos_validos = freq[freq >= min_freq].index
        return self.df_notas[self.df_notas[self.codigo_prod_col].isin(produtos_validos)]

    # ---------------- Lista de produtos distintos ----------------
    def get_lista_produtos(self) -> List[int]:
        """
        Retorna lista de códigos de produtos distintos.
        Usa df_produtos se disponível, senão df_notas.
        """
        if self.df_produtos is not None and self.prod_code_col in self.df_produtos.columns:
            return list(self.df_produtos[self.prod_code_col].dropna().unique())
        return list(self.df_notas[self.codigo_prod_col].dropna().unique())

    # ---------------- Geração de regras ----------------
    def gerar_regras(
        self,
        min_support: float = 0.0001,
        min_confidence: float = 0.015,
        min_lift: float = 1.0,
        max_len: int = 2,
        min_freq: Optional[int] = 2,
        min_itemset_count: Optional[int] = None,
        cod_produto: Optional[Any] = None,
        top_n: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Gera regras de cross-selling e retorna DataFrame com colunas:
        ['antecedente', 'consequente', 'suporte', 'confianca', 'lift']
        """
        # 1) Filtrar por frequência mínima
        df = self._aplicar_min_freq(min_freq)
        n_transacoes = df[self.codigo_nota_col].nunique()
        produtos_distintos = df[self.codigo_prod_col].nunique()
        print(f"[CrossSelling] transações: {n_transacoes} | produtos distintos (após min_freq): {produtos_distintos}")

        if produtos_distintos == 0 or n_transacoes == 0:
            print("[CrossSelling] após filtro não há dados suficientes.")
            return pd.DataFrame(columns=['antecedente', 'consequente', 'suporte', 'confianca', 'lift'])

        # 2) Mapear produtos para colunas (one-hot)
        unique_products = df[self.codigo_prod_col].unique()
        product_to_col = {p: i for i, p in enumerate(unique_products)}
        columns = list(unique_products)
        n_products = len(columns)

        # 3) Criar matriz esparsa (nota x produtos)
        grouped = df.groupby(self.codigo_nota_col)[self.codigo_prod_col].unique()
        rows, cols = [], []
        for row_idx, prod_list in enumerate(grouped):
            for p in prod_list:
                col_idx = product_to_col.get(p)
                if col_idx is not None:
                    rows.append(row_idx)
                    cols.append(col_idx)
        data = np.ones(len(rows), dtype=np.int8)

        if len(rows) == 0:
            print("[CrossSelling] nenhuma célula ativa na matriz (após filtro).")
            return pd.DataFrame(columns=['antecedente', 'consequente', 'suporte', 'confianca', 'lift'])

        spmatrix = sp.csr_matrix((data, (rows, cols)), shape=(len(grouped), n_products))

        # 4) Criar DataFrame one-hot
        df_onehot = pd.DataFrame.sparse.from_spmatrix(spmatrix, columns=columns).astype(bool)

        del df, grouped, rows, cols, data, spmatrix
        gc.collect()

        # 5) FP-Growth
        frequent_itemsets = fpgrowth(df_onehot, min_support=min_support, use_colnames=True, max_len=max_len)
        if frequent_itemsets.empty:
            print("[CrossSelling] nenhum itemset frequente encontrado.")
            del df_onehot
            gc.collect()
            return pd.DataFrame(columns=['antecedente', 'consequente', 'suporte', 'confianca', 'lift'])

        # 6) Filtro por contagem mínima de itemset
        if min_itemset_count is not None:
            frequent_itemsets['itemset_count'] = (frequent_itemsets['support'] * len(df_onehot)).round().astype(int)
            frequent_itemsets = frequent_itemsets[frequent_itemsets['itemset_count'] >= min_itemset_count].drop(columns=['itemset_count'])
            if frequent_itemsets.empty:
                print("[CrossSelling] nenhum itemset após filtro por min_itemset_count.")
                del df_onehot
                gc.collect()
                return pd.DataFrame(columns=['antecedente', 'consequente', 'suporte', 'confianca', 'lift'])

        # 7) Regras de associação
        rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)
        if rules.empty:
            print("[CrossSelling] nenhuma regra gerada.")
            del df_onehot, frequent_itemsets
            gc.collect()
            return pd.DataFrame(columns=['antecedente', 'consequente', 'suporte', 'confianca', 'lift'])

        # 8) Filtrar por lift
        rules = rules[rules['lift'] >= min_lift]
        if rules.empty:
            print("[CrossSelling] nenhuma regra com lift >= min_lift.")
            del df_onehot, frequent_itemsets
            gc.collect()
            return pd.DataFrame(columns=['antecedente', 'consequente', 'suporte', 'confianca', 'lift'])


        # 10) Formatar resultados
        def extrair_valor(fset):
            if len(fset) == 1:
                return next(iter(fset))
            return tuple(sorted(fset))

        resultados = [
            {
                'antecedente': extrair_valor(r['antecedents']),
                'consequente': extrair_valor(r['consequents']),
                'suporte': float(r['support']),
                'confianca': float(r['confidence']),
                'lift': float(r['lift'])
            }
            for _, r in rules.iterrows()
        ]
        df_regras = pd.DataFrame(resultados)

        del df_onehot, frequent_itemsets, rules
        gc.collect()

        # 12) Retornar top_n ou todas ordenadas por lift
        if top_n is not None and top_n > 0:
            return df_regras.nlargest(top_n, 'lift').reset_index(drop=True)
        return df_regras.sort_values(by='lift', ascending=False).reset_index(drop=True)
