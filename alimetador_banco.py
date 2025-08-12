import pandas as pd
import time
from datetime import timedelta, datetime
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
    regras = cross.gerar_regras(cod_produto, min_support=0.0015,  max_len=2)
    df_formatado = cross.formatar_regras(regras) if not regras.empty else pd.DataFrame()
    
    return resultado_sub, df_formatado


def main():
    start_time = time.time()
    print("Iniciando processamento...")
    
    # 1. Processamento inicial das bases
    print("Carregando e limpando dados...")
    df_estoque = EstoqueCleaner().clean(pd.read_excel("bases/relatorio_produtos.xlsx"))
    df_notas = NotasCleaner().clean(pd.read_excel("bases/relatorio_notas.xlsx"))
    df_modelo = BasePreparador().preparar_base(df_estoque, df_notas)
    
    # 2. Processar produtos
    codigos_unicos = df_modelo['Código produto'].unique()[:5] 
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
            horario = datetime.now().strftime("%H:%M:%S")
            print(f"{i}/{total_produtos} | Cód: {cod_produto} | Tempo: {tempo_produto:.1f}s | Horário: {horario}")
        except Exception as e:
            print(f"{i}/{total_produtos} | Cód: {cod_produto} | Erro: {str(e)}")
            continue
    
    # 3. Relatório final
    total_time = time.time() - start_time
    print(f"\nProcesso concluído!")
    print(f"Tempo total: {format_time(total_time)}")
    print(f"Média por produto: {total_time/total_produtos:.1f}s")


if __name__ == "__main__":
    main()
