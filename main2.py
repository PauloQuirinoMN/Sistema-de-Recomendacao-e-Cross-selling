import flet as ft
import psycopg2
import pandas as pd
from limpeza_estoque import EstoqueCleaner
from limpeza_notas import NotasCleaner
from consolidar import ConsolidadoNormalizer
from substitutos import RecomendadorSubstitutoDB
from associados import CrossSellingSimples
from atualizador_regras import AtualizarRegras   # a classe revisada que retorna DF


def main(page: ft.Page):
    page.title = "Teste Normalização"
    page.window_width = 600
    page.window_height = 400

    # ---------------- CONEXÃO COM BANCO ----------------
    conn = psycopg2.connect(
        dbname="rec",
        user="postgres",
        password="dev2025",
        host="192.168.0.200",
        port="5432"
    )
    # String de conexão SQLAlchemy
    conn_str = "postgresql+psycopg2://postgres:dev2025@192.168.0.200:5432/rec"

    # ---------------- CARREGAR E LIMPAR BASES ----------------
    df_estoque = EstoqueCleaner().clean(pd.read_excel("bases/relatorio_produtos.xlsx"))
    df_notas = NotasCleaner().clean(pd.read_excel("bases/relatorio_notas.xlsx"))

    # ---------------- NORMALIZAÇÃO ----------------
    normalizador = ConsolidadoNormalizer(conn_str)
    normalizador.processar(df_estoque, df_notas)

    

    # ---------------- PADRONIZAR COLUNAS ----------------
    # df_notas já padronizado
    df_notas = df_notas.rename(columns={
        "Numero nota fiscal": "numero_nota_fiscal",
        "Código produto": "codigo_produto"
    })

    # df_estoque padronizado
    df_estoque = df_estoque.rename(columns={
        "Código produto": "codigo_produto",
        "Produto": "descricao_produto"
    })

    
    # ---------------- INICIALIZA CLASSE DE ASSOCIADOS testes----------------
    # passa df_notas e (opcional) df_estoque para ter descrições
    cross = CrossSellingSimples(
        df_notas, 
        df_produtos=df_estoque,
        codigo_nota_col="numero_nota_fiscal",
        codigo_prod_col="codigo_produto",
        prod_code_col="codigo_produto",
        prod_desc_col="descricao_produto"
    )
   
    # 2️⃣ Salva as regras no banco

    # Inicializa atualizador
    produtos_distintos = df_notas['codigo_produto'].unique()
    atualizador = AtualizarRegras(conn_str, top_n=10)

    # Gera e salva
    atualizador.gerar_e_salvar(
        cross, 
        produtos_distintos,)
    
    conn.close()

    # # ---------------- TESTE DE SUBSTITUTOS ----------------
    # codigo_teste = 227  # substitua pelo código de produto que quer testar
    # recomendador = RecomendadorSubstitutoDB(conn, codigo_teste)
    # df_substitutos = recomendador.recomendar_substitutos(n=6)
    # print(df_substitutos)



    page.add(ft.Text("✅ Teste concluído, dados normalizados!", size=20, weight=ft.FontWeight.BOLD))


if __name__ == "__main__":
    ft.app(target=main)
