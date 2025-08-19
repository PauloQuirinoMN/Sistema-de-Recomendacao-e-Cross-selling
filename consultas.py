# consultas.py
import flet as ft
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

class PesquisaProduto:
    COLUNAS_MAP = {
        "Descrição do produto": "descricao_produto",  
        "Valor unitário": "valor_unitario",
        "Margem %": "margem_percent",
        "Quantidade estoque": "quantidade_estoque"
    }

    def __init__(self, page: ft.Page, resultado_pesquisa: ft.Container):
        self.page = page
        self.resultado_pesquisa = resultado_pesquisa
        # Configurar a conexão com SQLAlchemy
        self.engine = create_engine(
            "postgresql+psycopg2://postgres:recomenda@localhost:5432/bd_recomenda"
        )

    def buscar_produto(self, codigo):
        query = f"SELECT * FROM produtos_consolidados WHERE codigo_produto = {codigo}"
        try:
            df = pd.read_sql_query(query, self.engine)
            return df
        except SQLAlchemyError as e:
            print("Erro ao consultar banco:", e)
            return pd.DataFrame()

    def atualizar_resultado(self, codigo: str):
        if not codigo:
            return

        df = self.buscar_produto(codigo)

        if df.empty:
            # Produto não encontrado
            self.resultado_pesquisa.content = ft.Column(
                [
                    ft.Text("RESULTADO DA PESQUISA:", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
                    ft.Text(f"Produto {codigo} não foi encontrado na Base !!!",
                            style=ft.TextStyle(size=18, color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD))
                ]
            )
        else:
            # Produto encontrado
            row = df.iloc[0]
            self.resultado_pesquisa.content = ft.Column(
                [
                    ft.Text("RESULTADO DA PESQUISA:", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
                    ft.Text(
                        spans=[
                            ft.TextSpan(f"Item {row['codigo_produto']} - "),
                            ft.TextSpan(f"{row[self.COLUNAS_MAP['Descrição do produto']]}",
                                        style=ft.TextStyle(size=18, weight="bold", color=ft.Colors.BLUE)),
                            ft.TextSpan(" - Valor "),
                            ft.TextSpan(f"R$ {row[self.COLUNAS_MAP['Valor unitário']]}",
                                        style=ft.TextStyle(size=18, weight="bold", color=ft.Colors.BLUE)),
                            ft.TextSpan(", tem uma Margem "),
                            ft.TextSpan(f"{row[self.COLUNAS_MAP['Margem %']]} %",
                                        style=ft.TextStyle(size=18, weight="bold", color=ft.Colors.BLUE)),
                            ft.TextSpan(f" com estoque de {row[self.COLUNAS_MAP['Quantidade estoque']]} unidades."),
                        ],
                        size=16
                    )
                ]
            )

        # Atualiza a interface
        self.page.update()
