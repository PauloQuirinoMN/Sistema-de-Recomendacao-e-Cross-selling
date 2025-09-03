import pandas as pd
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

    def __init__(self, conn):
        self.conn = conn

    def criar_tabelas(self):
        """Cria as tabelas normalizadas se não existirem"""
        with self.conn.cursor() as cur:

            # Tabela categorias
            cur.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id SERIAL PRIMARY KEY,
                codigo_categoria INTEGER UNIQUE,
                nome_categoria TEXT
            );
            """)

            # Tabela marcas
            cur.execute("""
            CREATE TABLE IF NOT EXISTS marcas (
                id SERIAL PRIMARY KEY,
                codigo_marca INTEGER UNIQUE,
                nome_marca TEXT
            );
            """)

            # Tabela produtos
            cur.execute("""
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
            """)

            # Tabela notas_fiscais
            cur.execute("""
            CREATE TABLE IF NOT EXISTS notas_fiscais (
                id SERIAL PRIMARY KEY,
                numero_nota_fiscal INTEGER UNIQUE,
                data_venda DATE,
                valor_nota NUMERIC,
                data_insercao TIMESTAMP DEFAULT NOW()
            );
            """)

            # Tabela itens_notas
            cur.execute("""
            CREATE TABLE IF NOT EXISTS itens_notas (
                id SERIAL PRIMARY KEY,
                nota_id INTEGER REFERENCES notas_fiscais(id),
                produto_id INTEGER REFERENCES produtos(id),
                quantidade_produto INTEGER,
                valor_unitario NUMERIC,
                valor_total_produto NUMERIC,
                data_insercao TIMESTAMP DEFAULT NOW()
            );
            """)

            self.conn.commit()
            print("✅ Tabelas criadas com sucesso!")

    def inserir_categorias(self, df: pd.DataFrame):
        """Insere categorias únicas na tabela categorias"""
        df_cat = df[['Código da categoria', 'Categoria']].drop_duplicates().copy()
        df_cat.rename(columns={
            'Código da categoria': 'codigo_categoria',
            'Categoria': 'nome_categoria'
        }, inplace=True)

        #E verificando valores nulos
        print(df_cat.isnull().sum())


        valores = [tuple(x) for x in df_cat[['codigo_categoria', 'nome_categoria']].to_numpy()]


        query = """
        INSERT INTO categorias (codigo_categoria, nome_categoria)
        VALUES %s
        ON CONFLICT (codigo_categoria) DO NOTHING;
        """

        with self.conn.cursor() as cur:
            execute_values(cur, query, valores)
            self.conn.commit()
            print(f"✅ {len(valores)} categorias inseridas com sucesso!")

    def inserir_marcas(self, df: pd.DataFrame):
        """Insere marcas únicas na tabela marcas"""
        df_marca = df[['Código da Marca', 'Marca']].drop_duplicates().copy()
        df_marca.rename(columns={
            'Código da Marca': 'codigo_marca',
            'Marca': 'nome_marca'
        }, inplace=True)

        #E verificando valores nulos
        print(df_marca.isnull().sum())

        valores = [tuple(x) for x in df_marca[['codigo_marca', 'nome_marca']].to_numpy()]

        print("Valores Marcas:", valores)

        query = """
        INSERT INTO marcas (codigo_marca, nome_marca)
        VALUES %s
        ON CONFLICT (codigo_marca) DO NOTHING;
        """

        with self.conn.cursor() as cur:
            execute_values(cur, query, valores)
            self.conn.commit()
            print(f"✅ {len(valores)} marcas inseridas com sucesso!")

    def inserir_produtos(self, df: pd.DataFrame):
        """Insere produtos vinculando às tabelas categorias e marcas"""
        df_prod = df.rename(columns={
            'Produto': 'descricao_produto',
            'Código produto': 'codigo_produto',
            'Código da categoria': 'codigo_categoria',
            'Código da Marca': 'codigo_marca',
            'Preço de custo': 'preco_custo',
            'Quantidade estoque': 'quantidade_estoque'
        }).copy()

        # Mapear IDs de categorias e marcas do banco
        with self.conn.cursor() as cur:
            cur.execute("SELECT codigo_categoria, id FROM categorias;")
            categorias = {row[0]: row[1] for row in cur.fetchall()}

            cur.execute("SELECT codigo_marca, id FROM marcas;")
            marcas = {row[0]: row[1] for row in cur.fetchall()}

        df_prod['categoria_id'] = df_prod['codigo_categoria'].map(categorias)
        df_prod['marca_id'] = df_prod['codigo_marca'].map(marcas)

        # 🚨 Remover registros sem código de produto (NaN ou inválido)
        df_prod = df_prod.dropna(subset=['codigo_produto'])

        # Tratamento de colunas numéricas
        df_prod['codigo_produto'] = df_prod['codigo_produto'].astype(int)
        df_prod['descricao_produto'] = df_prod['descricao_produto'].fillna("DESCONHECIDO")
        df_prod['quantidade_estoque'] = df_prod['quantidade_estoque'].fillna(0).astype(int)
        df_prod['preco_custo'] = df_prod['preco_custo'].fillna(0).astype(float)

        # Categoria/marca podem ser nulas → tratamos como None e ajustamos o tipo corretamente

        df_prod['categoria_id'] = df_prod['categoria_id'].astype('Int64')
        df_prod['marca_id'] = df_prod['marca_id'].astype('Int64')

        df_prod['categoria_id'] = df_prod['categoria_id'].where(df_prod['categoria_id'].notnull(), None)
        df_prod['marca_id'] = df_prod['marca_id'].where(df_prod['marca_id'].notnull(), None)

        print(df[['Código da categoria', 'Categoria']].drop_duplicates())
        print(df[['Código da Marca', 'Marca']].drop_duplicates())


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

        with self.conn.cursor() as cur:
            execute_values(cur, query, valores)
            self.conn.commit()
            print(f"✅ {len(valores)} produtos inseridos com sucesso!")


    def inserir_notas(self, df: pd.DataFrame):
        """Insere as notas na tabela notas_fiscais"""
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

        with self.conn.cursor() as cur:
            execute_values(cur, query, valores)
            self.conn.commit()
            print(f"✅ {len(valores)} notas inseridas com sucesso!")

    def inserir_itens(self, df: pd.DataFrame):
        """Insere os itens vinculados a notas e produtos"""
        with self.conn.cursor() as cur:
            cur.execute("SELECT numero_nota_fiscal, id FROM notas_fiscais;")
            notas = {row[0]: row[1] for row in cur.fetchall()}

            cur.execute("SELECT codigo_produto, id FROM produtos;")
            produtos = {row[0]: row[1] for row in cur.fetchall()}

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
        VALUES %s;
        """

        with self.conn.cursor() as cur:
            execute_values(cur, query, valores)
            self.conn.commit()
            print(f"✅ {len(valores)} itens inseridos com sucesso!")

    def processar(self, df: pd.DataFrame):
        """Executa o pipeline completo"""
        self.criar_tabelas()
        self.inserir_categorias(df)
        self.inserir_marcas(df)
        self.inserir_produtos(df)
        self.inserir_notas(df)
        self.inserir_itens(df)
