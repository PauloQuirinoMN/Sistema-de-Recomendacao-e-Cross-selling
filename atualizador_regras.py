import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
from typing import List, Optional
from psycopg2.extras import execute_values

class AtualizarRegras:
    """
    Classe para criar a tabela de métricas e salvar regras de cross-selling
    geradas pela classe CrossSellingSimples.
    """

    def __init__(self, conn_str: str, tabela: str = "metricas", top_n: Optional[int] = None):
        self.tabela = tabela
        self.top_n = top_n
        self.engine = create_engine(conn_str)
        self._criar_tabela()

    def _criar_tabela(self):
        """Cria a tabela de métricas com colunas de suporte, confiança, lift e data de atualização."""
        with self.engine.begin() as conn:
            conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {self.tabela} (
                id SERIAL PRIMARY KEY,
                antecedente_id INT NOT NULL,
                consequente_id INT NOT NULL,
                suporte FLOAT,
                confianca FLOAT,
                lift FLOAT,
                data_atualizacao TIMESTAMP NOT NULL
            );
            """))
            # Cria índices para consultas rápidas
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_antecedente ON {self.tabela}(antecedente_id);"))
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_consequente ON {self.tabela}(consequente_id);"))

    def gerar_e_salvar(
            self,
            cross_obj,
            produtos: List[int],
            chunk_size: int = 1000,
            per_product_top_n: int = 5,
            min_support: float = 0.0001,
            min_confidence: float = 0.015,
            min_lift: float = 1.0,
            min_freq: Optional[int] = 2,
            replace_existing: bool = True
        ):
        """
        Gera todas as regras **uma vez** e salva top N por produto (antecedente).
        - per_product_top_n: quantas regras por antecedente salvar
        - replace_existing: se True, remove regras antigas do antecedente antes de inserir
        """

        # 1) gerar todas as regras (uma execução custosa, mas única)
        print("[AtualizarRegras] Gerando conjunto completo de regras (uma execução)...")
        full_rules = cross_obj.gerar_regras(
            min_support=min_support,
            min_confidence=min_confidence,
            min_lift=min_lift,
            max_len=2,
            min_freq=min_freq,
            cod_produto=None,
            top_n=None
        )

        if full_rules.empty:
            print("[AtualizarRegras] Nenhuma regra gerada para os parâmetros fornecidos. Abortando.")
            return

        # garantir colunas esperadas
        full_rules = full_rules[['antecedente','consequente','suporte','confianca','lift']]

        # 2) organizar por antecedente para pegar top_n por antecedente
        # convert types for safety
        full_rules['antecedente'] = full_rules['antecedente'].astype(int)
        full_rules['consequente'] = full_rules['consequente'].astype(int)

        # 🔎 só manter os produtos que de fato aparecem como antecedente
        produtos_com_regras = set(full_rules['antecedente'].unique())

        print(f"[AtualizarRegras] Regras geradas para {len(produtos_com_regras)} produtos distintos.")

        now = datetime.now()

        # iterar em chunks de produtos (aqueles que você quer atualizar)
        produtos = list(produtos)
        for i in range(0, len(produtos), chunk_size):
            chunk = produtos[i:i+chunk_size]
            print(f"[AtualizarRegras] Processando chunk {i+1}-{i+len(chunk)} / {len(produtos)}")

            rows_to_insert = []

            # para cada produto do chunk, pegar top per_product_top_n regras onde ele é antecedente
            for prod in chunk:
                if prod not in produtos_com_regras:
                    # produto nunca aparece como antecedente → skip sem filtro pesado
                    continue

                subset = full_rules[full_rules['antecedente'] == prod]
                if subset.empty:
                    # não precisa logar sempre → já sabemos que pode não ter
                    continue

                top = subset.nlargest(per_product_top_n, 'lift')
                # coletar linhas p/ insert
                for _, r in top.iterrows():
                    rows_to_insert.append((
                        int(r['antecedente']),
                        int(r['consequente']),
                        float(r['suporte']),
                        float(r['confianca']),
                        float(r['lift']),
                        now
                    ))

            if not rows_to_insert:
                continue

            with self.engine.begin() as conn:
                # usar cursor psycopg2 para execute_values (mais rápido)
                cur = conn.connection.cursor()

                if replace_existing:
                    # deletar regras antigas com antecedente no chunk
                    chunk_python = [int(x) for x in chunk]
                    cur.execute(
                        f"DELETE FROM {self.tabela} WHERE antecedente_id = ANY(%s);",
                        (chunk_python,)
                    )

                insert_sql = f"""
                    INSERT INTO {self.tabela}
                    (antecedente_id, consequente_id, suporte, confianca, lift, data_atualizacao)
                    VALUES %s
                """
                execute_values(cur, insert_sql, rows_to_insert)
                conn.connection.commit()

            print(f"[AtualizarRegras] Inseridas {len(rows_to_insert)} linhas para esse chunk.")
