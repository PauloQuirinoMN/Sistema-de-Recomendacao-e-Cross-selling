import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
import numpy as np
from consolidar import salvar_consolidado

''
def salvar_no_banco(df_substitutos: pd.DataFrame, df_associados: pd.DataFrame, df_modelo: pd.DataFrame, limite: int = 6):
    """
    Insere os produtos substitutos e associados no banco PostgreSQL.

    Parâmetros:
        df_substitutos (pd.DataFrame): DataFrame de produtos substitutos.
        df_associados (pd.DataFrame): DataFrame de produtos associados (cross-selling).
        df_modelo (pd.DataFrame): DataFrame principal contendo produtos e categorias.
        limite (int): Número máximo de registros a inserir por consulta.

    Observações:
        - Cria as tabelas se não existirem.
        - Trata valores nulos e inválidos antes da inserção.
        - Limita o número de registros inseridos.
    """
    # 🔹 Obter código pesquisado
    if df_substitutos.empty:
        print("[INFO] DataFrame de substitutos vazio. Nenhum registro será inserido.")
        return

    codigo_pesquisado = str(df_substitutos.iloc[0]["Código pesquisado"])

    # 🔹 Verifica se o código existe no modelo
    codigo_no_produto = codigo_pesquisado in df_modelo["Código produto"].astype(str).values
    codigo_na_categoria = codigo_pesquisado in df_modelo["Categoria"].astype(str).values

    if not (codigo_no_produto or codigo_na_categoria):
        print(f"[INFO] Código '{codigo_pesquisado}' não encontrado em produtos nem categorias. Nenhum registro será inserido.")
        return

    # 🔹 Conexão com o banco e tratamento de erro
    try:
        conn = psycopg2.connect(
            host="localhost",
            dbname="bd_recomenda",
            user="postgres",
            password="recomenda",
            port=5432
        )
        cur = conn.cursor()
    except Exception as e:
        print(f"[ERRO] Falha ao conectar ao banco: {e}")
        return

    # 🔹 Cria tabela de produtos consolidados
    salvar_consolidado(conn, df_modelo)

    # 🔹 Cria tabelas substitutos e associados se não existirem
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

    # 🔹 Limpeza de NaN
    df_substitutos = df_substitutos.replace({np.nan: None})
    df_associados = df_associados.replace({np.nan: None})

    # 🔹 Preparar valores de substitutos limitados
    df_sub_limited = df_substitutos.head(limite)
    substitutos_values = []

    for _, row in df_sub_limited.iterrows():
        try:
            substitutos_values.append((
                str(row["Código pesquisado"]),
                str(row["Descrição pesquisada"]),
                str(row["Código produto"]),
                str(row["Descrição do produto"]),
                float(row["Valor unitário"]) if row["Valor unitário"] is not None else None,
                float(row["Margem %"]) if row["Margem %"] is not None else None,
                int(row["Quantidade estoque"]) if row["Quantidade estoque"] is not None else None,
                str(row["Categoria"])
            ))
        except Exception as e:
            print(f"[AVISO] Registro de substituto ignorado por erro: {e}")

    insert_substitutos = """
        INSERT INTO produtos_substitutos (
            produto_pesquisado_cod,
            produto_pesquisado_des,
            produto_recomendado_cod,
            produto_recomendado_des,
            valor_unitario,
            margem_percentual,
            estoque,
            categoria
        ) VALUES %s
    """

    if substitutos_values:
        execute_values(cur, insert_substitutos, substitutos_values)
        print(f"[INFO] {len(substitutos_values)} registros inseridos em 'produtos_substitutos'.")
    else:
        print("[INFO] Nenhum substituto válido para inserção.")

    # 🔹 Preparar valores de associados
    if df_associados.empty or "Antecedente" not in df_associados.columns:
        print(f"[INFO] Nenhuma associação encontrada para o código {codigo_pesquisado}.")
        df_assoc_filtrado = pd.DataFrame()
    else:
        df_assoc_filtrado = df_associados[
            df_associados["Antecedente"].astype(str) == codigo_pesquisado
        ].head(limite)

    associados_values = []
    for _, row in df_assoc_filtrado.iterrows():
        try:
            suporte = str(row["Aparece junto (%)"]).replace("%", "").strip()
            confianca = str(row["Chance de comprar junto (%)"]).replace("%", "").strip()
            associados_values.append((
                str(row["Antecedente"]),
                str(row["Descrição Antecedente"]),
                str(row["Consequente"]),
                str(row["Descrição Consequente"]),
                float(suporte) if suporte else None,
                float(confianca) if confianca else None
            ))
        except Exception as e:
            print(f"[AVISO] Registro associado ignorado por erro: {e}")

    insert_associados = """
        INSERT INTO produtos_associados (
            produto_pesquisado_cod,
            produto_pesquisado_des,
            produto_associado_cod,
            produto_associado_des,
            suporte,
            confianca
        ) VALUES %s
    """

    if associados_values:
        execute_values(cur, insert_associados, associados_values)
        print(f"[INFO] {len(associados_values)} registros inseridos em 'produtos_associados'.")
    else:
        print("[INFO] Nenhum associado válido para inserção.")

    # 🔹 Commit e fechamento da conexão
    conn.commit()
    cur.close()
    conn.close()
    print("[INFO] Inserção concluída com sucesso.")
