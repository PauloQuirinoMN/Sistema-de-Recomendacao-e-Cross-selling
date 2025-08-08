import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

def salvar_no_banco(df_substitutos, df_associados, df_modelo, limite=6):
    # Obter código pesquisado
    if df_substitutos.empty:
        print("[INFO] DataFrame de substitutos vazio. Nenhum registro será inserido.")
        return

    codigo_pesquisado = str(df_substitutos.iloc[0]["Código pesquisado"])

    # Verificar se código está no df_modelo (produtos ou categorias)
    codigo_no_produto = codigo_pesquisado in df_modelo["Código produto"].astype(str).values
    codigo_na_categoria = codigo_pesquisado in df_modelo["Categoria"].astype(str).values

    if not (codigo_no_produto or codigo_na_categoria):
        print(f"[INFO] Código '{codigo_pesquisado}' não encontrado em produtos nem categorias no df_modelo. Nenhum registro será inserido.")
        return

    # Conexão e criação das tabelas (igual antes)
    conn = psycopg2.connect(
        host="localhost",
        dbname="bd_recomenda",
        user="postgres",
        password="recomenda",
        port=5432
    )
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS produtos_substitutos (
        id SERIAL PRIMARY KEY,
        produto_pesquisado_cod VARCHAR,
        produto_pesquisado_des VARCHAR,
        produto_recomendado_cod VARCHAR,
        produto_recomendado_des VARCHAR,
        valor_unitario NUMERIC,
        margem_percentual NUMERIC,
        estoque INTEGER,
        categoria VARCHAR,
        data_insersao TIMESTAMP
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS produtos_associados (
        id SERIAL PRIMARY KEY,
        produto_pesquisado_cod VARCHAR,
        produto_pesquisado_des VARCHAR,
        produto_associado_cod VARCHAR,
        produto_associado_des VARCHAR,
        suporte NUMERIC,
        confianca NUMERIC,
        data_insersao TIMESTAMP
    );
    """)

    agora = datetime.now()

    df_sub_limited = df_substitutos.head(limite)

    substitutos_values = [
        (
            str(row["Código pesquisado"]),
            str(row["Descrição pesquisada"]),
            str(row["Código produto"]),
            str(row["Descrição do produto"]),
            float(row["Valor unitário"]),
            float(row["Margem %"]),
            int(row["Quantidade estoque"]),
            str(row["Categoria"]),
            agora
        )
        for _, row in df_sub_limited.iterrows()
    ]

    insert_substitutos = """
        INSERT INTO produtos_substitutos (
            produto_pesquisado_cod,
            produto_pesquisado_des,
            produto_recomendado_cod,
            produto_recomendado_des,
            valor_unitario,
            margem_percentual,
            estoque,
            categoria,
            data_insersao
        ) VALUES %s
    """

    execute_values(cur, insert_substitutos, substitutos_values)
    print(f"[INFO] {len(substitutos_values)} registros inseridos em 'produtos_substitutos'.")

    df_assoc_filtrado = df_associados[
        df_associados["Antecedente"].astype(str) == codigo_pesquisado
    ].head(limite)

    associados_values = [
        (
            str(row["Antecedente"]),
            str(row["Descrição Antecedente"]),
            str(row["Consequente"]),
            str(row["Descrição Consequente"]),
            float(str(row["Aparece junto (%)"]).replace("%", "").strip()),
            float(str(row["Chance de comprar junto (%)"]).replace("%", "").strip()),
            agora
        )
        for _, row in df_assoc_filtrado.iterrows()
    ]

    insert_associados = """
        INSERT INTO produtos_associados (
            produto_pesquisado_cod,
            produto_pesquisado_des,
            produto_associado_cod,
            produto_associado_des,
            suporte,
            confianca,
            data_insersao
        ) VALUES %s
    """

    execute_values(cur, insert_associados, associados_values)
    print(f"[INFO] {len(associados_values)} registros inseridos em 'produtos_associados'.")

    conn.commit()
    cur.close()
    conn.close()
    print("[INFO] Inserção concluída com sucesso.")

