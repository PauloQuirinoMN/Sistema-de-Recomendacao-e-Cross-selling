import pandas as pd
from sqlalchemy import create_engine, text
from psycopg2.extras import execute_values


class ConsolidadoNormalizer:
    """
    Classe responsável por normalizar os dados e inserir nas tabelas:
    - categorias
    - marcas
    - produtos
    - notas_fiscais
    - itens_notas
    """

    def __init__(self, conn_str: str):
        self.engine = create_engine(conn_str)

    # ---------------------------------------------------------
    # CRIAÇÃO DAS TABELAS
    # ---------------------------------------------------------
    def criar_tabelas(self):
        """Cria as tabelas normalizadas se não existirem"""
        ddl_statements = [
            """
            CREATE TABLE IF NOT EXISTS categorias (
                id SERIAL PRIMARY KEY,
                codigo_categoria INTEGER UNIQUE,
                nome_categoria TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS marcas (
                id SERIAL PRIMARY KEY,
                codigo_marca INTEGER UNIQUE,
                nome_marca TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS produtos (
                id SERIAL PRIMARY KEY,
                codigo_produto INTEGER UNIQUE,
                descricao_produto TEXT,
                quantidade_estoque INTEGER,
                preco_custo NUMERIC,
                categoria_id INTEGER REFERENCES categorias(id),
                marca_id INTEGER REFERENCES marcas(id),
                data_insercao TIMESTAMP DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS notas_fiscais (
                id SERIAL PRIMARY KEY,
                numero_nota_fiscal INTEGER UNIQUE,
                data_venda DATE,
                valor_nota NUMERIC,
                data_insercao TIMESTAMP DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS itens_notas (
                id SERIAL PRIMARY KEY,
                nota_id INTEGER REFERENCES notas_fiscais(id),
                produto_id INTEGER REFERENCES produtos(id),
                quantidade_produto INTEGER,
                valor_unitario NUMERIC,
                valor_total_produto NUMERIC,
                data_insercao TIMESTAMP DEFAULT NOW(),
                UNIQUE (nota_id, produto_id)
            );
            """
        ]

        with self.engine.begin() as conn:
            for ddl in ddl_statements:
                conn.execute(text(ddl))

        print("✅ Tabelas criadas com sucesso!")

    # ---------------------------------------------------------
    # INSERÇÕES
    # ---------------------------------------------------------
    def inserir_categorias(self, df: pd.DataFrame):
        df_cat = df[['Código da categoria', 'Categoria']].drop_duplicates()
        df_cat = df_cat.rename(columns={
            'Código da categoria': 'codigo_categoria',
            'Categoria': 'nome_categoria'
        })

        valores = [tuple(x) for x in df_cat.to_numpy()]
        query = """
            INSERT INTO categorias (codigo_categoria, nome_categoria)
            VALUES %s
            ON CONFLICT (codigo_categoria) DO NOTHING;
        """

        with self.engine.begin() as conn:
            with conn.connection.cursor() as cur:
                execute_values(cur, query, valores)
        print(f"✅ {len(valores)} categorias processadas.")

    def inserir_marcas(self, df: pd.DataFrame):
        df_marca = df[['Código da Marca', 'Marca']].drop_duplicates()
        df_marca = df_marca.rename(columns={
            'Código da Marca': 'codigo_marca',
            'Marca': 'nome_marca'
        })

        valores = [tuple(x) for x in df_marca.to_numpy()]
        query = """
            INSERT INTO marcas (codigo_marca, nome_marca)
            VALUES %s
            ON CONFLICT (codigo_marca) DO NOTHING;
        """

        with self.engine.begin() as conn:
            with conn.connection.cursor() as cur:
                execute_values(cur, query, valores)
        print(f"✅ {len(valores)} marcas processadas.")

    def inserir_produtos(self, df: pd.DataFrame):
        df_prod = df.rename(columns={
            'Produto': 'descricao_produto',
            'Código produto': 'codigo_produto',
            'Código da categoria': 'codigo_categoria',
            'Código da Marca': 'codigo_marca',
            'Preço de custo': 'preco_custo',
            'Quantidade estoque': 'quantidade_estoque'
        }).copy()

        with self.engine.begin() as conn:
            categorias = dict(conn.execute(text("SELECT codigo_categoria, id FROM categorias")).fetchall())
            marcas = dict(conn.execute(text("SELECT codigo_marca, id FROM marcas")).fetchall())

        df_prod['categoria_id'] = df_prod['codigo_categoria'].map(categorias)
        df_prod['marca_id'] = df_prod['codigo_marca'].map(marcas)

        df_prod = df_prod.dropna(subset=['codigo_produto'])
        df_prod['codigo_produto'] = df_prod['codigo_produto'].astype(int)
        df_prod['descricao_produto'] = df_prod['descricao_produto'].fillna("DESCONHECIDO")
        df_prod['quantidade_estoque'] = df_prod['quantidade_estoque'].fillna(0).astype(int)
        df_prod['preco_custo'] = df_prod['preco_custo'].fillna(0).astype(float)

        valores = [
            (
                int(row['codigo_produto']),
                row['descricao_produto'],
                int(row['quantidade_estoque']),
                float(row['preco_custo']),
                int(row['categoria_id']) if pd.notnull(row['categoria_id']) else None,
                int(row['marca_id']) if pd.notnull(row['marca_id']) else None
            )
            for _, row in df_prod.iterrows()
        ]

        query = """
            INSERT INTO produtos (codigo_produto, descricao_produto, quantidade_estoque,
                                  preco_custo, categoria_id, marca_id)
            VALUES %s
            ON CONFLICT (codigo_produto) DO NOTHING;
        """

        with self.engine.begin() as conn:
            with conn.connection.cursor() as cur:
                execute_values(cur, query, valores)
        print(f"✅ {len(valores)} produtos processados.")

    def inserir_notas(self, df: pd.DataFrame):
        df_notas = df.rename(columns={
            'Numero nota fiscal': 'numero_nota_fiscal',
            'Data da venda': 'data_venda',
            'Valor da nota': 'valor_nota'
        }).copy()

        valores = [tuple(x) for x in df_notas[['numero_nota_fiscal', 'data_venda', 'valor_nota']].to_numpy()]
        query = """
            INSERT INTO notas_fiscais (numero_nota_fiscal, data_venda, valor_nota)
            VALUES %s
            ON CONFLICT (numero_nota_fiscal) DO NOTHING;
        """

        with self.engine.begin() as conn:
            with conn.connection.cursor() as cur:
                execute_values(cur, query, valores)
        print(f"✅ {len(valores)} notas processadas.")

    def inserir_itens(self, df: pd.DataFrame):
        with self.engine.begin() as conn:
            notas = dict(conn.execute(text("SELECT numero_nota_fiscal, id FROM notas_fiscais")).fetchall())
            produtos = dict(conn.execute(text("SELECT codigo_produto, id FROM produtos")).fetchall())

        df_itens = df.rename(columns={
            'Numero nota fiscal': 'numero_nota_fiscal',
            'Código produto': 'codigo_produto',
            'Quantidade do produto': 'quantidade_produto',
            'Valor unitário': 'valor_unitario',
            'Valor total produto': 'valor_total_produto'
        }).copy()

        df_itens['nota_id'] = df_itens['numero_nota_fiscal'].map(notas)
        df_itens['produto_id'] = df_itens['codigo_produto'].map(produtos)
        df_itens = df_itens.dropna(subset=['nota_id', 'produto_id'])

        valores = [
            (int(n), int(p), int(q), float(vu), float(vtp))
            for n, p, q, vu, vtp in zip(
                df_itens['nota_id'],
                df_itens['produto_id'],
                df_itens['quantidade_produto'],
                df_itens['valor_unitario'],
                df_itens['valor_total_produto']
            )
        ]

        query = """
            INSERT INTO itens_notas (nota_id, produto_id, quantidade_produto, valor_unitario, valor_total_produto)
            VALUES %s
            ON CONFLICT (nota_id, produto_id) DO NOTHING;
        """

        with self.engine.begin() as conn:
            with conn.connection.cursor() as cur:
                execute_values(cur, query, valores)
        print(f"✅ {len(valores)} itens processados.")

    # ---------------------------------------------------------
    # PIPELINE
    # ---------------------------------------------------------
    def processar(self, df_estoque: pd.DataFrame, df_notas: pd.DataFrame):
        """Executa o pipeline completo com estoque e notas"""
        self.criar_tabelas()
        self.inserir_categorias(df_estoque)
        self.inserir_marcas(df_estoque)
        self.inserir_produtos(df_estoque)
        self.inserir_notas(df_notas)
        self.inserir_itens(df_notas)
        print("✅ Pipeline de normalização concluído!")
