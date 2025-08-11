import pandas as pd
import time
from datetime import timedelta
from limpeza_estoque import EstoqueCleaner
from limpeza_notas import NotasCleaner
from limpeza_base_mesclada import BasePreparador
from substitutos import RecomendadorSubstituto
from recomendador import RecomendadorCrossSelling
from salva_banco import salvar_no_banco
import psycopg2

def format_time(seconds):
    """Formata segundos em HH:MM:SS"""
    return str(timedelta(seconds=seconds))

def processar_produto(cod_produto, df_modelo):
    """Processa um único produto e retorna os DataFrames de resultados"""
    try:
        desc_produto = df_modelo.loc[
            df_modelo['Código produto'] == cod_produto, 'Descrição do produto'
        ].values[0]
    except IndexError:
        desc_produto = 'Descrição não encontrada'

    # Recomendação de Substitutos
    recomendador = RecomendadorSubstituto(df_modelo)
    resultado_sub = recomendador.recomendar(cod_produto)
    resultado_sub.insert(0, "Código pesquisado", cod_produto)
    resultado_sub.insert(1, "Descrição pesquisada", desc_produto)

    # Recomendação por Cross-Selling
    cross = RecomendadorCrossSelling(df_modelo)
    regras = cross.gerar_regras(cod_produto, min_support=0.0015, min_threshold=1.0, max_len=2)
    df_formatado = cross.formatar_regras(regras) if not regras.empty else pd.DataFrame()
    
    return resultado_sub, df_formatado

def contar_codigos_banco():
    """Conta códigos distintos no banco"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            dbname="bd_recomenda",
            user="postgres",
            password="recomenda",
            port=5432
        )
        cur = conn.cursor()
        cur.execute("SELECT COUNT(DISTINCT produto_pesquisado_cod) FROM produtos_substitutos;")
        total_substitutos = cur.fetchone()[0]

        cur.execute("SELECT COUNT(DISTINCT produto_pesquisado_cod) FROM produtos_associados;")
        total_associados = cur.fetchone()[0]

        cur.close()
        conn.close()
        return total_substitutos, total_associados
    except Exception as e:
        print(f"[ERRO] Não foi possível consultar o banco: {e}")
        return None, None

def main():
    start_time = time.time()
    print("Iniciando processamento...")
    
    # 1. Processamento inicial das bases
    print("Carregando e limpando dados...")
    df_estoque = EstoqueCleaner().clean(pd.read_excel("bases/relatorio_produtos.xlsx"))
    df_notas = NotasCleaner().clean(pd.read_excel("bases/relatorio_notas.xlsx"))
    df_modelo = BasePreparador().preparar_base(df_estoque, df_notas)
    
    # 2. Processar produtos
    codigos_unicos = df_modelo['Código produto'].unique()[:80]  # Primeiros 10 para teste
    total_produtos = len(codigos_unicos)
    produtos_processados = 0
    print(f"\nProcessando {total_produtos} produtos...")
    
    for i, cod_produto in enumerate(codigos_unicos, 1):
        produto_start = time.time()
        try:
            resultado_sub, df_formatado = processar_produto(cod_produto, df_modelo)
            salvar_no_banco(resultado_sub, df_formatado, df_modelo)
            produtos_processados += 1
            tempo_produto = time.time() - produto_start
            print(f"{i}/{total_produtos} | Cód: {cod_produto} | Tempo: {tempo_produto:.1f}s")
        except Exception as e:
            print(f"{i}/{total_produtos} | Cód: {cod_produto} | Erro: {str(e)}")
            continue
    
    # 3. Relatório final
    total_time = time.time() - start_time
    print(f"\nProcesso concluído!")
    print(f"Tempo total: {format_time(total_time)}")
    print(f"Média por produto: {total_time/total_produtos:.1f}s")

    # 4. Conferência com o banco
    total_substitutos, total_associados = contar_codigos_banco()
    if total_substitutos is not None:
        print(f"\n--- Conferência Banco ---")
        print(f"Produtos processados no Python: {produtos_processados}")
        print(f"Códigos distintos no banco (substitutos): {total_substitutos}")
        print(f"Códigos distintos no banco (associados): {total_associados}")

        if produtos_processados == total_substitutos == total_associados:
            print("[OK] Todos os produtos processados estão no banco.")
        else:
            print("[ALERTA] Diferença encontrada! Verifique se houve falhas na inserção.")

if __name__ == "__main__":
    main()
