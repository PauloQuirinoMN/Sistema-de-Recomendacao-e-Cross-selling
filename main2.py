import flet as ft
import psycopg2
import pandas as pd
from limpeza_estoque import EstoqueCleaner
from limpeza_notas import NotasCleaner
from consolidar import ConsolidadoNormalizer
from substitutos import RecomendadorSubstitutoDB
from associados import CrossSellingSimples    


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

    # ---------------- NORMALIZAÇÃO ----------------
    normalizador = ConsolidadoNormalizer(conn)
    normalizador.processar(df_estoque, df_notas)

    # ---------------- CONEXÃO COM BANCO ----------------
    conn = psycopg2.connect(
        dbname="rec",
        user="postgres",
        password="dev2025",
        host="192.168.0.200",
        port="5432"
    )

    # ---------------- INICIALIZA CLASSE ----------------
    cross = CrossSellingSimples(conn)

    # ---------------- PRODUTO A PESQUISAR ----------------
    cod_pesquisado = 16560  # substitua pelo código que deseja testar

    # ---------------- GERAR E CONSULTAR REGRAS ----------------
    df_regras = cross.gerar_regras(
        cod_produto=cod_pesquisado,
        min_support=0.0015,
        min_confidence=0.05,
        min_lift=1.0,
        max_len=2
    )

    if df_regras.empty:
        page.add(ft.Text(f"⚠️ Nenhuma regra encontrada para o produto {cod_pesquisado}"))
    else:
        page.add(ft.Text(f"🔎 Regras para o produto {cod_pesquisado}:"))
        # Exibe o DataFrame no console
        print(df_regras)
        # Para exibir na UI, você poderia iterar sobre o df
        for _, row in df_regras.iterrows():
            page.add(ft.Text(
                f"{row['Antecedente']} ({row['Descricao_Antecedente']}) → "
                f"{row['Consequente']} ({row['Descricao_Consequente']}), "
                f"Confiança: {row['Confiança (%)']:.2f}%, Suporte: {row['Suporte']:.3f}, Lift: {row['Lift']:.2f}"
            ))

    conn.close()
    
    # ---------------- INICIALIZA CLASSE DE RECOMENDAÇÃO ----------------
    # codigo_teste = 227  # substitua pelo código de produto que quer testar
    # recomendador = RecomendadorSubstitutoDB(conn, codigo_teste)

    # # ---------------- OBTER SUBSTITUTOS ----------------
    # df_substitutos = recomendador.recomendar_substitutos(n=6)
    # print(df_substitutos)

    # # ---------------- LOG NA UI ----------------
    # page.add(ft.Text("✅ Teste concluído, dados normalizados!", size=20, weight=ft.FontWeight.BOLD))

if __name__ == "__main__":
    ft.app(target=main)
