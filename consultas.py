import pandas as pd
from sqlalchemy import create_engine, text 
from sqlalchemy.exc import SQLAlchemyError   
import flet as ft

# CLASSE PARA EXIBIR DE CARACTERÍSTICAS DO PRODUTO
class PesquisaProduto:
    def __init__(self, engine=None):
        self.engine = engine or create_engine(
            "postgresql+psycopg2://postgres:recomenda@localhost:5432/bd_recomenda"
        )

    @staticmethod
    def _codigo_valido(codigo) -> bool:
        return str(codigo).strip().isdigit()

    def buscar_produto(self, codigo):
        if not self._codigo_valido(codigo):
            return {"erro": "Código do produto vazio ou inválido."}

        codigo_str = str(codigo).strip()

        query = text("""
            SELECT
                codigo_produto,
                descricao_produto,
                valor_unitario,
                margem_percent,
                quantidade_estoque
            FROM produtos_consolidados
            WHERE codigo_produto::text = :codigo
            LIMIT 1
        """)

        try:
            df = pd.read_sql_query(query, self.engine, params={"codigo": codigo_str})
        except SQLAlchemyError as e:
            print("Erro ao consultar banco:", e)
            return {"erro": "Erro ao consultar banco"}

        if df.empty:
            return {"mensagem": f"Produto {codigo_str} não foi encontrado na Base !!!"}

        row = df.iloc[0]
        return {
            "codigo_produto": row["codigo_produto"],
            "descricao_produto": row["descricao_produto"],
            "valor_unitario": row["valor_unitario"],
            "margem_percent": row["margem_percent"],
            "quantidade_estoque": row["quantidade_estoque"],
        }


# CLASSE PARA TABELA DE RECOMENDAÇÃO
class TabelaRecomendacao:
    def __init__(self, engine):
        self.engine = engine

    def buscar_recomendacoes(self, codigo: str):
        query = text("""
            SELECT 
                produto_recomendado_cod, 
                produto_recomendado_des, 
                valor_unitario, 
                margem_percentual, 
                estoque
            FROM produtos_substitutos
            WHERE produto_pesquisado_cod::text = :codigo
            LIMIT 3;
        """)
        try:
            df = pd.read_sql_query(query, self.engine, params={"codigo": str(codigo)})
            return df
        except SQLAlchemyError as e:
            print("Erro ao consultar substitutos:", e)
            return pd.DataFrame()

    def criar_tabela(self, codigo: int):
        df = self.buscar_recomendacoes(codigo)

        if df.empty:
            return ft.Text("Nenhum produto recomendado encontrado.", color=ft.Colors.RED)

        rows = []
        for _, row in df.iterrows():
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(row["produto_recomendado_cod"]))),
                        ft.DataCell(ft.Text(str(row["produto_recomendado_des"]))),
                        ft.DataCell(ft.Text(str(row["valor_unitario"]))),
                        ft.DataCell(ft.Text(str(row["margem_percentual"]))),
                        ft.DataCell(ft.Text(str(row["estoque"]))),
                    ],
                    on_select_changed=lambda e, cod=row["produto_recomendado_cod"]: 
                        print(f"Produto selecionado: {cod}")
                )
            )

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


# CLASSE PARA TABELA DE ASSOCIADOS
class TabelaAssociados:
    def __init__(self, engine):
        self.engine = engine

    def buscar_associados(self, codigo: str):
        if not codigo.strip():
            return pd.DataFrame()

        query = text("""
            SELECT DISTINCT ON (a.produto_associado_cod)
                a.produto_associado_cod,
                a.produto_associado_des,
                a.suporte AS frequencia,
                a.confianca AS conversao,
                c.valor_unitario,
                c.margem_percent AS margem_percentual,
                c.quantidade_estoque
            FROM produtos_associados a
            LEFT JOIN produtos_consolidados c
                ON a.produto_associado_cod::text = c.codigo_produto::text
            WHERE a.produto_pesquisado_cod::text = :codigo
            ORDER BY a.produto_associado_cod, a.suporte DESC
            LIMIT 4;
        """)
        try:
            df = pd.read_sql_query(query, self.engine, params={"codigo": str(codigo)})
            return df
        except SQLAlchemyError as e:
            print("Erro ao consultar associados:", e)
            return pd.DataFrame()

    def criar_tabela(self, codigo: str):
        df = self.buscar_associados(codigo)
        if df.empty:
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(f"Nenhum produto associado encontrado para o código {codigo}.",
                                color=ft.Colors.RED)
                    ]
                ),
                padding=ft.padding.symmetric(vertical=10, horizontal=15),
                margin=ft.margin.only(bottom=15),
            )

        rows = []
        for _, row in df.iterrows():
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(row["produto_associado_cod"]))),
                        ft.DataCell(ft.Text(str(row["produto_associado_des"]))),
                        ft.DataCell(ft.Text(f'R$ {row["valor_unitario"]:.2f}'.replace(".", ","))),
                        ft.DataCell(ft.Text(f'{row["margem_percentual"]:.1f}%')),
                        ft.DataCell(ft.Text(f'{row["frequencia"]:.0f}%')),
                        ft.DataCell(ft.Text(f'{row["conversao"]:.0f}%')),
                    ],
                    on_select_changed=lambda e, cod=row["produto_associado_cod"]: 
                        print(f"Produto associado selecionado: {cod}")
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(f"PRODUTOS QUE NORMALMENTE SÃO COMPRADOS JUNTOS COM {codigo}", 
                            size=16, 
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLUE_800),
                    ft.Divider(height=1, color=ft.Colors.BLUE_GREY_300),
                    ft.DataTable(
                        columns=[
                            ft.DataColumn(ft.Text("Código", weight=ft.FontWeight.BOLD)),
                            ft.DataColumn(ft.Text("Descrição", weight=ft.FontWeight.BOLD)),
                            ft.DataColumn(ft.Text("V. Unitário", weight=ft.FontWeight.BOLD), numeric=True),
                            ft.DataColumn(ft.Text("Margem %", weight=ft.FontWeight.BOLD), numeric=True),
                            ft.DataColumn(ft.Text("Aparecem Juntos", weight=ft.FontWeight.BOLD), numeric=True,
                                          tooltip="Frequência que aparecem juntos nas vendas"),
                            ft.DataColumn(ft.Text("Comprados Juntos", weight=ft.FontWeight.BOLD), numeric=True,
                                          tooltip="Taxa de conversão quando aparecem juntos"),
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
                        width=850,
                    ),
                ],
                spacing=10
            ),
            padding=ft.padding.symmetric(vertical=10, horizontal=15),
            margin=ft.margin.only(bottom=15),
        )
