"""
UI helpers para exibição de recomendações e associados usando Flet.

Mantive a lógica e assinaturas originais; organizei e documentei blocos
(declarações, consultas, merges, formatação e renderização).
"""

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import flet as ft


class TabelaRecomendacao:
    """
    Gera um componente Flet (Container) contendo uma DataTable com
    produtos substitutos (código, descrição, margem %, estoque).

    Método principal:
        - criar_tabela(df: pd.DataFrame) -> ft.Control
    """

    def __init__(self):
        # Classe sem estado além do método de renderização.
        pass

    def criar_tabela(self, df: pd.DataFrame):
        """
        Recebe um DataFrame esperado com colunas:
            ['codigo_produto', 'descricao_produto', 'margem_percent', 'quantidade_estoque']

        Retorna:
            - ft.Text(...) se df vazio
            - ft.Container(...) com DataTable caso contrário
        """
        if df.empty:
            return ft.Text("Nenhum produto recomendado encontrado.", color=ft.Colors.RED)

        # Remove duplicados por codigo_produto e reindexa
        df = df.drop_duplicates(subset="codigo_produto").reset_index(drop=True)

        # Construção das linhas da DataTable
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
                    # captura segura do código com default arg para evitar problema de late-binding
                    on_select_changed=lambda e, cod=row["codigo_produto"]:
                        print(f"Produto substituto selecionado: {cod}"),
                )
            )

        # Retorna o container com título e a DataTable estilizada
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "POSSÍVEIS PRODUTOS SUBSTITUTOS",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_800,
                    ),
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
                        expand=True,
                    ),
                ],
                spacing=10,
            ),
            padding=ft.padding.symmetric(vertical=10, horizontal=15),
            margin=ft.margin.only(bottom=15),
        )


class TabelaAssociados:
    """
    Consulta a tabela `metricas` (antecedente -> consequente) e monta
    um DataFrame enriquecido com descrição, estoque, preço de custo e
    preço de venda médio. Fornece também o método para renderizar a
    tabela em Flet (criar_tabela).
    """

    def __init__(self, engine):
        """
        :param engine: SQLAlchemy engine (ou compatível) para executar queries.
        """
        self.engine = engine

    def buscar_associados(self, codigo: str) -> pd.DataFrame:
        """
        Retorna um DataFrame com produtos associados (até 5) ao `codigo` informado.
        Colunas resultantes incluem: produto_associado_cod, frequencia (suporte),
        conversao (confianca), codigo_produto, descricao_produto, preco_custo,
        quantidade_estoque, produto_id, preco_venda_medio, margem_percent, conversao_percent.
        """
        # valida entrada
        if not codigo or not str(codigo).strip():
            return pd.DataFrame()

        # Consulta principal: pega consequentes (produtos associados)
        query = text(
            """
            SELECT 
                m.consequente_id AS produto_associado_cod,
                m.suporte AS frequencia,
                m.confianca AS conversao
            FROM metricas m
            WHERE m.antecedente_id = :codigo
            ORDER BY m.consequente_id, m.suporte DESC
            LIMIT 5;
            """
        )

        try:
            df_assoc = pd.read_sql_query(query, self.engine, params={"codigo": str(codigo)})
        except SQLAlchemyError as e:
            print("Erro ao consultar associados:", e)
            return pd.DataFrame()

        if df_assoc.empty:
            return df_assoc

        # Lista de códigos encontrados (usada para consultas seguintes)
        codigos = df_assoc["produto_associado_cod"].tolist()
        codigos_str = ",".join(str(c) for c in codigos)

        # Busca dados dos produtos (descrição, custo, estoque)
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

        # Calcula preço médio de venda por produto a partir de itens_notas
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
            # mantém df_avg com colunas esperadas para merges posteriores
            df_avg = pd.DataFrame(columns=["produto_id", "preco_venda_medio"])

        # Conversões numéricas seguras
        df_prod["preco_custo"] = pd.to_numeric(df_prod.get("preco_custo", pd.Series()), errors="coerce")
        df_assoc["conversao"] = pd.to_numeric(df_assoc.get("conversao", pd.Series()), errors="coerce")
        df_avg["preco_venda_medio"] = pd.to_numeric(df_avg.get("preco_venda_medio", pd.Series()), errors="coerce")

        # Merge das informações: assoc <- produtos <- avg(preco venda)
        df = df_assoc.merge(
            df_prod,
            left_on="produto_associado_cod",
            right_on="codigo_produto",
            how="left",
        )
        df = df.merge(df_avg, left_on="produto_associado_cod", right_on="produto_id", how="left")

        # Cálculo da margem percentual (proteção básica via fillna depois)
        df["margem_percent"] = ((df["preco_venda_medio"] - df["preco_custo"]) / df["preco_venda_medio"] * 100)
        df["margem_percent"] = df["margem_percent"].fillna(0).round(2)

        # Normaliza estoque e conversão
        df["quantidade_estoque"] = pd.to_numeric(df.get("quantidade_estoque", pd.Series()), errors="coerce").fillna(0).astype(int)
        df["conversao_percent"] = (df["conversao"] * 100).round(2)

        return df

    def criar_tabela(self, codigo: str):
        """
        Monta e retorna um componente Flet (Container) com a tabela de
        produtos associados ao `codigo` informado. Se não houver resultados,
        retorna um Container com mensagem informativa.
        """
        df = self.buscar_associados(codigo)
        if df.empty:
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            f"Nenhum produto associado encontrado para o código {codigo}.",
                            color=ft.Colors.RED,
                        )
                    ]
                ),
                padding=ft.padding.symmetric(vertical=10, horizontal=15),
                margin=ft.margin.only(bottom=15),
            )

        # Remove duplicados por segurança e reindexa
        df = df.drop_duplicates(subset="produto_associado_cod").reset_index(drop=True)

        # Monta linhas da DataTable
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
                        print(f"Produto associado selecionado: {cod}"),
                )
            )

        # Retorna container com DataTable estilizada
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "PRODUTOS QUE NORMALMENTE SÃO COMPRADOS JUNTOS",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_800,
                    ),
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
                        expand=True,
                    ),
                ],
                spacing=10,
            ),
            padding=ft.padding.symmetric(vertical=10, horizontal=15),
            margin=ft.margin.only(bottom=15),
        )
