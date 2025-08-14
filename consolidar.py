import psycopg2
from psycopg2.extras import execute_values
import pandas as pd

def salvar_consolidado(conn, df_modelo):
    """
    Salva todo o df_modelo na tabela produtos_consolidados.
    Só insere os dados se a tabela estiver vazia.
    """
    colunas = [
        'Numero nota fiscal', 'Data da venda', 'Código produto', 'Descrição do produto',
        'Quantidade do produto', 'Valor unitário', 'Preço de custo', 'Valor total produto',
        'Valor da nota', 'Código da categoria', 'Categoria', 'Código da Marca', 'Marca',
        'Quantidade estoque', 'Margem bruta', 'Margem %', 'Markup'
    ]

    df = df_modelo[colunas].copy()
    df = df.where(pd.notnull(df), None)

    with conn.cursor() as cur:
        # Cria tabela se não existir
        cur.execute("""
            CREATE TABLE IF NOT EXISTS produtos_consolidados (
                numero_nota_fiscal INTEGER,
                data_venda DATE,
                codigo_produto INTEGER,
                descricao_produto TEXT,
                quantidade_produto INTEGER,
                valor_unitario NUMERIC,
                preco_custo NUMERIC,
                valor_total_produto NUMERIC,
                valor_nota NUMERIC,
                codigo_categoria INTEGER,
                categoria TEXT,
                codigo_marca INTEGER,
                marca TEXT,
                quantidade_estoque INTEGER,
                margem_bruta NUMERIC,
                margem_percent NUMERIC,
                markup NUMERIC,
                data_insercao TIMESTAMP DEFAULT NOW()
            );
        """)

        # Cria índices se não existirem
        cur.execute("CREATE INDEX IF NOT EXISTS idx_produto ON produtos_consolidados(codigo_produto);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_categoria ON produtos_consolidados(codigo_categoria);")

        conn.commit()

        # Verifica se a tabela já possui registros
        cur.execute("SELECT COUNT(*) FROM produtos_consolidados;")
        count = cur.fetchone()[0]

        if count > 0:
            print("⚠️ Tabela 'produtos_consolidados' já possui dados. Nenhuma inserção será feita.")
            return

        # Insere os dados se a tabela estiver vazia
        valores = [tuple(linha) for linha in df.to_numpy()]
        query = """
            INSERT INTO produtos_consolidados (
                numero_nota_fiscal, data_venda, codigo_produto, descricao_produto,
                quantidade_produto, valor_unitario, preco_custo, valor_total_produto,
                valor_nota, codigo_categoria, categoria, codigo_marca, marca,
                quantidade_estoque, margem_bruta, margem_percent, markup
            ) VALUES %s
        """
        from psycopg2.extras import execute_values
        execute_values(cur, query, valores)
        conn.commit()
        print(f"✅ {len(df)} registros inseridos em produtos_consolidados com sucesso!")

