import pandas as pd
from sqlalchemy import create_engine, text 
from sqlalchemy.exc import SQLAlchemyError   
import flet as ft


# CLASSE PARA TABELA DE RECOMENDAÇÃO
class TabelaRecomendacao:
    def __init__(self):
        pass

    def criar_tabela(self, df: pd.DataFrame):
        if df.empty:
            return ft.Text("Nenhum produto recomendado encontrado.", color=ft.Colors.RED)

        # 🔹 Remove duplicados para evitar repetição
        df = df.drop_duplicates(subset='codigo_produto').reset_index(drop=True)

        rows = []
        for _, row in df.iterrows():
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(row["codigo_produto"]))),
                        ft.DataCell(ft.Text(str(row["descricao_produto"]))),
                        ft.DataCell(ft.Text(f"{row['margem_percent']:.1f}%")),
                        ft.DataCell(ft.Text(str(row["quantidade_estoque"]))),
                    ],
                    on_select_changed=lambda e, cod=row["codigo_produto"]: 
                        print(f"Produto substituto selecionado: {cod}")
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("POSSÍVEIS PRODUTOS SUBSTITUTOS", 
                            size=16, 
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLUE_800),
                    ft.Divider(height=1, color=ft.Colors.BLUE_GREY_300),
                    ft.DataTable(
                        columns=[
                            ft.DataColumn(ft.Text("Código", weight=ft.FontWeight.BOLD)),
                            ft.DataColumn(ft.Text("Descrição", weight=ft.FontWeight.BOLD)),
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
                        expand=True
                    ),
                ],
                spacing=10
            ),
            padding=ft.padding.symmetric(vertical=10, horizontal=15),
            margin=ft.margin.only(bottom=15),
        )


# ------------------- CLASSE PARA TABELA DE ASSOCIADOS -------------------
class TabelaAssociados:
    def __init__(self, engine):
        self.engine = engine

    def buscar_associados(self, codigo: str):
        if not codigo or not str(codigo).strip():
            return pd.DataFrame()

        # Consulta principal: produtos associados
        query = text("""
            SELECT 
                m.consequente_id AS produto_associado_cod,
                m.suporte AS frequencia,
                m.confianca AS conversao
            FROM metricas m
            WHERE m.antecedente_id = :codigo
            ORDER BY m.consequente_id, m.suporte DESC
            LIMIT 5;
        """)

        try:
            df_assoc = pd.read_sql_query(query, self.engine, params={"codigo": str(codigo)})
        except SQLAlchemyError as e:
            print("Erro ao consultar associados:", e)
            return pd.DataFrame()

        if df_assoc.empty:
            return df_assoc

        # Busca informações adicionais dos produtos (descrição, estoque, preco_custo)
        codigos = df_assoc['produto_associado_cod'].tolist()
        codigos_str = ",".join(str(c) for c in codigos)

        query_prod = f"""
            SELECT 
                codigo_produto,
                descricao_produto,
                preco_custo,
                quantidade_estoque
            FROM produtos
            WHERE codigo_produto IN ({codigos_str})
        """

        try:
            df_prod = pd.read_sql_query(query_prod, self.engine)
        except SQLAlchemyError as e:
            print("Erro ao consultar produtos:", e)
            return pd.DataFrame()

        # Calcula preço médio de venda a partir da tabela itens_notas
        query_avg = f"""
            SELECT 
                produto_id,
                AVG(valor_unitario) AS preco_venda_medio
            FROM itens_notas
            WHERE produto_id IN ({codigos_str})
            GROUP BY produto_id
        """
        try:
            df_avg = pd.read_sql_query(query_avg, self.engine)
        except SQLAlchemyError as e:
            print("Erro ao consultar preço médio:", e)
            df_avg = pd.DataFrame(columns=['produto_id', 'preco_venda_medio'])

        # Converte para numérico
        df_prod['preco_custo'] = pd.to_numeric(df_prod['preco_custo'], errors='coerce')
        df_assoc['conversao'] = pd.to_numeric(df_assoc['conversao'], errors='coerce')
        df_avg['preco_venda_medio'] = pd.to_numeric(df_avg['preco_venda_medio'], errors='coerce')

        # Junta informações associadas
        df = df_assoc.merge(df_prod, left_on='produto_associado_cod', right_on='codigo_produto', how='left')
        df = df.merge(df_avg, left_on='produto_associado_cod', right_on='produto_id', how='left')

        # Calcula margem corretamente
        df['margem_percent'] = ((df['preco_venda_medio'] - df['preco_custo']) / df['preco_venda_medio'] * 100)
        df['margem_percent'] = df['margem_percent'].fillna(0).round(2)

        # Corrige estoque e conversão
        df['quantidade_estoque'] = pd.to_numeric(df['quantidade_estoque'], errors='coerce').fillna(0).astype(int)
        df['conversao_percent'] = (df['conversao'] * 100).round(2)

        return df

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

        # Remove duplicados por segurança
        df = df.drop_duplicates(subset='produto_associado_cod').reset_index(drop=True)

        # Monta linhas da tabela
        rows = []
        for _, row in df.iterrows():
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(row["produto_associado_cod"]))),
                        ft.DataCell(ft.Text(str(row["descricao_produto"]))),
                        ft.DataCell(ft.Text(f'{row["margem_percent"]:.1f}%')),
                        ft.DataCell(ft.Text(str(row["quantidade_estoque"]))),
                        ft.DataCell(ft.Text(f'{row["conversao_percent"]:.2f}%')),
                    ],
                    on_select_changed=lambda e, cod=row["produto_associado_cod"]:
                        print(f"Produto associado selecionado: {cod}")
                )
            )

        # Cria DataTable
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("PRODUTOS QUE NORMALMENTE SÃO COMPRADOS JUNTOS",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLUE_800),
                    ft.Divider(height=1, color=ft.Colors.BLUE_GREY_300),
                    ft.DataTable(
                        columns=[
                            ft.DataColumn(ft.Text("Código", weight=ft.FontWeight.BOLD)),
                            ft.DataColumn(ft.Text("Descrição", weight=ft.FontWeight.BOLD)),
                            ft.DataColumn(ft.Text("Margem %", weight=ft.FontWeight.BOLD), numeric=True),
                            ft.DataColumn(ft.Text("Estoque", weight=ft.FontWeight.BOLD), numeric=True),
                            ft.DataColumn(ft.Text("Taxa de Conversão", weight=ft.FontWeight.BOLD), numeric=True),
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
                        expand=True
                    ),
                ],
                spacing=10
            ),
            padding=ft.padding.symmetric(vertical=10, horizontal=15),
            margin=ft.margin.only(bottom=15),
        )
