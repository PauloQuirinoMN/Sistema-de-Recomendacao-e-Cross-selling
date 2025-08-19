# consultas.py
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
import flet as ft


class PesquisaProduto:
    COLUNAS_MAP = {
        "descricao_produto": "descricao_produto",  
        "valor_unitario": "valor_unitario",
        "margem_percent": "margem_percent",
        "quantidade_estoque": "quantidade_estoque"
    }

    def __init__(self):
        # Configurar a conexão com SQLAlchemy
        self.engine = create_engine(
            "postgresql+psycopg2://postgres:recomenda@localhost:5432/bd_recomenda"
        )

    def buscar_produto(self, codigo: int):
        query = f"SELECT * FROM produtos_consolidados WHERE codigo_produto = {codigo}"
        try:
            df = pd.read_sql_query(query, self.engine)
        except SQLAlchemyError as e:
            print("Erro ao consultar banco:", e)
            return {"erro": "Erro ao consultar banco"}

        if df.empty:
            return {"mensagem": f"Produto {codigo} não foi encontrado na Base !!!"}
        else:
            row = df.iloc[0]
            return {
                "codigo_produto": row["codigo_produto"],
                "descricao_produto": row["descricao_produto"],
                "valor_unitario": row["valor_unitario"],
                "margem_percent": row["margem_percent"],
                "quantidade_estoque": row["quantidade_estoque"]
            }


# NOVA CLASSE PARA TABELA DE RECOMENDAÇÃO
class TabelaRecomendacao:
    def __init__(self, engine):
        self.engine = engine

    def buscar_recomendacoes(self, codigo: str):
        """
        Busca os 3 primeiros produtos substitutos no banco
        """
        query = f"""
        SELECT 
        produto_recomendado_cod, 
        produto_recomendado_des, 
        valor_unitario, 
        margem_percentual, 
        estoque
        FROM produtos_substitutos
        WHERE produto_pesquisado_cod = %s
        LIMIT 3;
            """
        try:
            df = pd.read_sql_query(query, self.engine, params=(str(codigo),))
            return df
        except SQLAlchemyError as e:
            print("Erro ao consultar substitutos:", e)
            return pd.DataFrame()

    def criar_tabela(self, codigo: int):
        df = self.buscar_recomendacoes(codigo)

        if df.empty:
            return ft.Text("Nenhum produto recomendado encontrado.", color=ft.Colors.RED)

        # Montar linhas da tabela dinamicamente
        rows = []
        for _, row in df.iterrows():
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(row["produto_recomendado_cod"]))),
                        ft.DataCell(ft.Text(str(row["produto_recomendado_des"]))),
                        ft.DataCell(ft.Text(str(row["valor_unitario"]))),
                        ft.DataCell(ft.Text(str(row["margem_percentual"]))),
                        ft.DataCell(ft.Text(str(row["estoque"])))
                    ],
                    on_select_changed=lambda e, cod=row["produto_recomendado_cod"]: print(f"Produto selecionado: {cod}")
                )
            )

        # Retornar o container pronto
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("PRODUTOS RECOMENDADOS", 
                            size=16, 
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLUE_800),
                    ft.Divider(height=1, color=ft.Colors.BLUE_GREY_300),
                    ft.DataTable(
                        columns=[
                            ft.DataColumn(ft.Text("Código", weight=ft.FontWeight.BOLD)),
                            ft.DataColumn(ft.Text("Descrição", weight=ft.FontWeight.BOLD)),
                            ft.DataColumn(ft.Text("Valor Unitário", weight=ft.FontWeight.BOLD), numeric=True),
                            ft.DataColumn(ft.Text("Margem %", weight=ft.FontWeight.BOLD), numeric=True),
                            ft.DataColumn(ft.Text("Estoque", weight=ft.FontWeight.BOLD), numeric=True),
                        ],
                        rows=rows,
                        border=ft.border.all(1, ft.Colors.BLUE_GREY_200),
                        border_radius=8,
                        vertical_lines=ft.border.BorderSide(1, ft.Colors.BLUE_GREY_100),
                        horizontal_lines=ft.border.BorderSide(1, ft.Colors.BLUE_GREY_100),
                        heading_row_color=ft.Colors.BLUE_GREY_50,
                        heading_row_height=40,
                        data_row_color={"hovered": ft.Colors.BLUE_GREY_100},
                        show_checkbox_column=False,
                        width=750,
                    ),
                ],
                spacing=10
            ),
            padding=ft.padding.symmetric(vertical=10, horizontal=15),
            margin=ft.margin.only(bottom=15),
        )