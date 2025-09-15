import pandas as pd
import numpy as np
from typing import Optional

class RecomendadorSubstitutoDB:
    """
    Recomendador de substitutos com lógica robusta de similaridade.

    Args:
        conn: SQLAlchemy engine / connection (aceitável por pd.read_sql).
        codigo_teste: código do produto base.
        weights: dict com pesos para 'price', 'margin', 'stock' (somam 1.0).
        epsilon: pequeno valor para evitar divisão por zero.
    """

    def __init__(self, conn, codigo_teste: int, logger: Optional[any] = None,
                 weights: dict | None = None, epsilon: float = 1e-9):
        self.conn = conn
        self.codigo_teste = codigo_teste
        self.logger = logger
        self.epsilon = epsilon
        self.weights = weights or {"price": 0.7, "margin": 0.2, "stock": 0.1}

        # Carrega produtos
        self.df_produtos = self._carregar_produtos()

        # Produto base
        self.produto_base = self._verificar_produto(codigo_teste)

        # Armazena última recomendação (opcional)
        self.last_recommendation = None

    def _log(self, *args, **kwargs):
        if self.logger:
            try:
                self.logger.log(*args, **kwargs)
                return
            except Exception:
                pass
        print(*args)

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
        df = pd.read_sql(query, self.conn)

        # Normalizações e proteções
        df['preco_venda_medio'] = pd.to_numeric(df['preco_venda_medio'], errors='coerce').fillna(0.0)
        df['preco_custo'] = pd.to_numeric(df['preco_custo'], errors='coerce').fillna(0.0)
        df['quantidade_estoque'] = pd.to_numeric(df['quantidade_estoque'], errors='coerce').fillna(0).astype(int)

        # Calcula margem apenas quando preco_venda_medio > 0 (evita divisão por zero)
        mask = df['preco_venda_medio'] > 0
        df['margem_percent'] = np.nan
        df.loc[mask, 'margem_percent'] = ((df.loc[mask, 'preco_venda_medio'] - df.loc[mask, 'preco_custo']) /
                                         df.loc[mask, 'preco_venda_medio']) * 100.0
        # Substitui inf/-inf por NaN, depois preenche NaN com 0 (opcional)
        df.loc[:, 'margem_percent'] = df['margem_percent'].replace([np.inf, -np.inf], np.nan)
        df['margem_percent'] = df['margem_percent'].fillna(0).round(2)

        return df

    def _verificar_produto(self, codigo: int) -> Optional[pd.Series]:
        produto = self.df_produtos[self.df_produtos['codigo_produto'] == codigo]
        if produto.empty:
            self._log(f"⚠️ Produto {codigo} não encontrado no banco.")
            return None
        return produto.iloc[0]

    def _relative_similarity(self, a: pd.Series | float, b: pd.Series | float) -> np.ndarray:
        """
        Calcula similaridade simétrica 1 - (2*|a-b|/(a+b+eps)), clip [0,1].
        Works vectorized: a can be scalar (base) and b an array/Series.
        """
        a_arr = np.asarray(a, dtype=float)
        b_arr = np.asarray(b, dtype=float)
        num = 2.0 * np.abs(a_arr - b_arr)
        den = (a_arr + b_arr) + self.epsilon
        rel_diff = num / den
        sim = 1.0 - rel_diff
        return np.clip(sim, 0.0, 1.0)

    def recomendar_substitutos(self, n: int = 6, preferir_mesma_categoria: bool = True,
                               min_stock: int = 1) -> pd.DataFrame:
        # Produto base inexistente
        if self.produto_base is None:
            return pd.DataFrame(columns=['codigo_produto', 'descricao_produto', 'margem_percent', 'quantidade_estoque'])

        base_price = float(self.produto_base['preco_custo'] or 0.0)
        base_margin = float(self.produto_base['margem_percent'] or 0.0)
        base_categoria = self.produto_base.get('codigo_categoria', None)

        # Filtra candidatos por estoque mínimo e exclui o próprio produto
        df_cand = self.df_produtos[
            (self.df_produtos['quantidade_estoque'] >= min_stock) &
            (self.df_produtos['codigo_produto'] != self.codigo_teste)
        ].copy()

        # Prioriza mesma categoria se desejado
        if preferir_mesma_categoria and pd.notna(base_categoria):
            df_same_cat = df_cand[df_cand['codigo_categoria'] == base_categoria].copy()
            if not df_same_cat.empty:
                df_cand = df_same_cat

        if df_cand.empty:
            self._log("Nenhum candidato disponível com estoque mínimo.")
            return pd.DataFrame(columns=['codigo_produto', 'descricao_produto', 'margem_percent', 'quantidade_estoque'])

        # Cálculo de similaridades
        price_sim = self._relative_similarity(base_price, df_cand['preco_custo'].fillna(0.0))
        margin_sim = self._relative_similarity(base_margin, df_cand['margem_percent'].fillna(0.0))

        # Stock score: normaliza stock em [0,1] (min-max)
        stock = df_cand['quantidade_estoque'].astype(float)
        stock_score = (stock - stock.min()) / (stock.max() - stock.min() + self.epsilon)
        # optional: se preferir penalizar muito baixo estoque, aplicar transformação (ex.: sqrt)

        # Score agregado
        w = self.weights
        df_cand['score'] = (w['price'] * price_sim) + (w['margin'] * margin_sim) + (w['stock'] * stock_score)

        # Explicability columns (opcionais)
        df_cand['price_sim'] = price_sim
        df_cand['margin_sim'] = margin_sim
        df_cand['stock_score'] = stock_score

        # Ordenação por score desc, margin desc, estoque desc, preco_custo asc (tie-breakers)
        df_cand = df_cand.sort_values(by=['score', 'margem_percent', 'quantidade_estoque', 'preco_custo'],
                                      ascending=[False, False, False, True])

        # Salva última recomendação (útil para auditoria)
        self.last_recommendation = df_cand

        # Retorna colunas finais — pode incluir 'score' se quiser exibir
        resultado = df_cand[['codigo_produto', 'descricao_produto', 'margem_percent', 'quantidade_estoque', 'score']].head(n).reset_index(drop=True)
        return resultado
