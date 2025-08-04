import flet as ft

def main(page: ft.Page):
    # Configurações da página
    page.title = "Recomenda"
    page.window_width = 800
    page.window_height = 600
    page.window_resizable = False
    page.window_prevent_close = True
    page.theme_mode = ft.ThemeMode.LIGHT  # ou DARK para tema escuro
    
    # Elementos da interface
    titulo = ft.Text(
        "Bem-vindo ao Sistema de Recomendações",
        size=20,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLUE_800
    )

    barra_pesquisa = ft.Row(
        [
            ft.TextField(
                label="Código",
                hint_text="ex.: 32581"
            ), 

            ft.TextButton(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.SEARCH, size=20),
                        ft.Text("Pesquisar")
                    ]
                ),
                on_click=lambda e: print("Pesquisar clicado")
            ),
            ft.Row([ft.TextButton(text="Limpar pesquisa")],alignment=ft.MainAxisAlignment.END),
        ],
        alignment=ft.MainAxisAlignment.START,
    )

    produto = 32581
    descricao =' Papel A4 -Produto Exemplo Premium'
    valor = 254.25
    margem = 56
    estoque = 41

    codigo_nao_econtrado = ft.Container(
        content=ft.Column(
            [
                ft.Text(value="RESULTADO DA PESQUISA:", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
                ft.Text(value=f"Produto {produto} não foi encontrado na Base !!!", style=ft.TextStyle(size=18, color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD))
            ]
        )
    )
    codigo_foi_encontrado = ft.Container(
        content=ft.Column(
            [
                ft.Text(value="RESULTADO DA PESQUISA:", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
                ft.Text(
                    spans=[
                        ft.TextSpan(f"Item {produto} - "),
                        ft.TextSpan(f"{descricao}", style=ft.TextStyle(size=18, weight="bold", color=ft.Colors.BLUE)),
                        ft.TextSpan(" - Valor "),
                        ft.TextSpan(f"R$ {valor}", style=ft.TextStyle(size=18, weight="bold", color=ft.Colors.BLUE)),
                        ft.TextSpan(", tem uma Margem "),
                        ft.TextSpan(f"{margem} %", style=ft.TextStyle(size=18, weight="bold", color=ft.Colors.BLUE)),
                        ft.TextSpan(f" com estoque de {estoque} unidades."),
                    ],
                    size=16
                )
            ]
        )
    )
    resultado = [codigo_nao_econtrado, codigo_foi_encontrado]
    resultado_pesquisa = ft.Container(
        content=ft.Row(
            controls=[
                resultado[1],
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.START,
        )
    )

    recomendacao = ft.Container(
    content=ft.Column(
        controls=[
            ft.Text("PRODUTOS RECOMENDADOS", 
                   size=16, 
                   weight=ft.FontWeight.BOLD,
                   color=ft.Colors.BLUE_800),
            ft.Divider(height=1, color=ft.Colors.BLUE_GREY_300),
            
            # Tabela de produtos recomendados
            ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Código", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Descrição", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Valor Unitário", weight=ft.FontWeight.BOLD),
                                numeric=True),
                    ft.DataColumn(ft.Text("Margem %", weight=ft.FontWeight.BOLD),
                                numeric=True),
                    ft.DataColumn(ft.Text("Estoque", weight=ft.FontWeight.BOLD),
                                numeric=True),
                ],
                rows=[
                    # Exemplo de registro 1
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text("48721")),
                            ft.DataCell(ft.Text("Kit Upgrade Performance")),
                            ft.DataCell(ft.Text("R$ 189,90")),
                            ft.DataCell(ft.Text("32,5%")),
                            ft.DataCell(ft.Text("15")),
                        ],
                        on_select_changed=lambda e: print("Produto selecionado: 48721")
                    ),
                    # Exemplo de registro 2
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text("56233")),
                            ft.DataCell(ft.Text("Sensor de Temperatura Premium")),
                            ft.DataCell(ft.Text("R$ 79,50")),
                            ft.DataCell(ft.Text("28,0%")),
                            ft.DataCell(ft.Text("22")),
                        ],
                        on_select_changed=lambda e: print("Produto selecionado: 56233")
                    ),
                    # Exemplo de registro 3
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text("60565")),
                            ft.DataCell(ft.Text("Conector Blindado 5 polos")),
                            ft.DataCell(ft.Text("R$ 45,20")),
                            ft.DataCell(ft.Text("35,5%")),
                            ft.DataCell(ft.Text("37")),
                        ],
                        on_select_changed=lambda e: print("Produto selecionado: 60565")
                    ),
                    # Exemplo de registro 4
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text("71289")),
                            ft.DataCell(ft.Text("Filtro de Linha com Proteção")),
                            ft.DataCell(ft.Text("R$ 120,00")),
                            ft.DataCell(ft.Text("40,0%")),
                            ft.DataCell(ft.Text("8")),
                        ],
                        on_select_changed=lambda e: print("Produto selecionado: 71289")
                    ),
                ],
                # Estilização da tabela
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

    associados = ft.Container(
    content=ft.Column(
        controls=[
            ft.Text(f"PRODUTOS QUE NORMALMENTE SÃO COMPRADOS JUNTOS COM {produto} {descricao}", 
                   size=16, 
                   weight=ft.FontWeight.BOLD,
                   color=ft.Colors.BLUE_800),
            ft.Divider(height=1, color=ft.Colors.BLUE_GREY_300),
            
            # Tabela de produtos associados
            ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Código", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Descrição", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("V. Unitário", weight=ft.FontWeight.BOLD),
                                numeric=True),
                    ft.DataColumn(ft.Text("Margem %", weight=ft.FontWeight.BOLD),
                                numeric=True),
                    ft.DataColumn(ft.Text("Aparecem Juntos", weight=ft.FontWeight.BOLD),
                                numeric=True, tooltip="Frequência que aparecem juntos nas vendas"),
                    ft.DataColumn(ft.Text("Comprados Juntos", weight=ft.FontWeight.BOLD),
                                numeric=True, tooltip="Taxa de conversão quando aparecem juntos"),
                ],
                rows=[
                    # Exemplo de registro 1
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text("38914")),
                            ft.DataCell(ft.Text("Cabos de Conexão Premium")),
                            ft.DataCell(ft.Text("R$ 65,80")),
                            ft.DataCell(ft.Text("30,2%")),
                            ft.DataCell(ft.Text("78%")),
                            ft.DataCell(ft.Text("62%")),
                        ],
                        on_select_changed=lambda e: print("Produto associado selecionado: 38914")
                    ),
                    # Exemplo de registro 2
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text("45672")),
                            ft.DataCell(ft.Text("Fonte Alimentação 12V 5A")),
                            ft.DataCell(ft.Text("R$ 89,90")),
                            ft.DataCell(ft.Text("35,0%")),
                            ft.DataCell(ft.Text("65%")),
                            ft.DataCell(ft.Text("58%")),
                        ],
                        on_select_changed=lambda e: print("Produto associado selecionado: 45672")
                    ),
                    # Exemplo de registro 3
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text("52108")),
                            ft.DataCell(ft.Text("Suporte Metálico Universal")),
                            ft.DataCell(ft.Text("R$ 32,50")),
                            ft.DataCell(ft.Text("40,5%")),
                            ft.DataCell(ft.Text("72%")),
                            ft.DataCell(ft.Text("45%")),
                        ],
                        on_select_changed=lambda e: print("Produto associado selecionado: 52108")
                    ),
                ],
                # Estilização da tabela (igual ao anterior para manter consistência)
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


    # Área de conteúdo principal
    conteudo = ft.Column(
        [
            resultado_pesquisa,
            ft.Divider(height=1),
            recomendacao,
            ft.Divider(height=10),
            associados,
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=0,
        scroll=ft.ScrollMode.AUTO
    )
   
    # Layout principal
    layout_principal = ft.Column(
        [
            barra_pesquisa,
            ft.Divider(height=1),
            conteudo,
        ],
        expand=True,
        scroll=True,
        spacing=10,
    )
    
    # Barra de status (rodapé)
    barra_status = ft.Text("Sistema Recomenda mvp v1.0 - © 2025   - Paulo Quirino - ", size=12, color=ft.Colors.GREY)
    
    # Adiciona todos os elementos à página
    page.add(
        titulo,
        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
        layout_principal,
        ft.Divider(),
        barra_status
    )

# Inicia a aplicação
ft.app(target=main)