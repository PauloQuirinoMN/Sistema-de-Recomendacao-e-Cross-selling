import flet as ft
import psycopg2
import pandas as pd
from limpeza_estoque import EstoqueCleaner
from limpeza_notas import NotasCleaner
from consolidar import ConsolidadoNormalizer

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

    # ---------------- CARREGAR E LIMPAR BASES ----------------
    df_estoque = EstoqueCleaner().clean(pd.read_excel("bases/relatorio_produtos.xlsx"))
    df_notas = NotasCleaner().clean(pd.read_excel("bases/relatorio_notas.xlsx"))
    print("Colunas do df_estoque:", df_estoque.columns.tolist())


    # ---------------- NORMALIZAÇÃO ----------------
    normalizador = ConsolidadoNormalizer(conn)
    normalizador.criar_tabelas()
    normalizador.inserir_produtos(df_estoque)
    normalizador.inserir_notas(df_notas)
    normalizador.inserir_itens(df_notas)



    # ---------------- LOG NA UI ----------------
    page.add(ft.Text("✅ Teste concluído, dados normalizados!", size=20, weight=ft.FontWeight.BOLD))

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.FLET_APP)
