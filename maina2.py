import flet as ft
from alimentador_banco2 import AtualizadorBase
# import pandas as pd
# from limpeza_base_mesclada import BasePreparador
import asyncio
import threading
import consultas 
from consultas import TabelaRecomendacao



def main(page: ft.Page):
    page.title = "Recomenda"
    page.window_width = 800
    page.window_height = 600
    page.window_resizable = False
    page.window_prevent_close = True
    page.theme_mode = ft.ThemeMode.LIGHT

    # logs e barra de progresso
    barra_progresso = ft.ProgressBar(value=0.0, width=250)
    pbl = ft.Text("0%", size=14, weight=ft.FontWeight.BOLD)
    log_text = ft.Text("", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)

    atualizador = AtualizadorBase()

    # -------- FUNÇÕES DE ATUALIZAÇÃO --------
      # Função para atualizar progresso
    def mostrar_progresso(atual: int, total: int):

    # Atualiza a cada 2% ou a cada 5 produtos
        if total > 50 and atual % max(5, total // 50) != 0:
            return
        
        progresso = atual / total
        async def _update():
            barra_progresso.value = progresso
            pbl.value = f"{int(progresso*100)}%"
            page.update()
        
        loop = asyncio.get_running_loop()
        asyncio.run_coroutine_threadsafe(_update(), loop)

    logs_buffer = []

    def mostrar_log(mensagem: str):
        logs_buffer.append(mensagem)

        async def _update():
            log_text.value = mensagem
            page.update()

        loop = asyncio.get_running_loop()  # pega o loop que o Flet está rodando
        asyncio.run_coroutine_threadsafe(_update(), loop)

   # ----------------- THREAD DE ATUALIZAÇÃO -----------------
    def rodar_atualizacao(e):
        threading.Thread(
            target=lambda: asyncio.run(atualizador.atualizar_base(
                intervalo_codigos=(0, 1000),
                progresso_callback=mostrar_progresso,
                log_callback=mostrar_log
            )),
            daemon=True
        ).start()
        
    botao_atualizar = ft.IconButton(
        icon=ft.Icons.UPDATE_SHARP,
        tooltip="Atualizar bases de dados",
        on_click=rodar_atualizacao
    )

    # Elementos da interface
    titulo = ft.Text(
        "Bem-vindo ao Sistema de Recomendações",
        size=20,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLUE_800
    )
    
    # Resultado do código pesquisado 

    # Container dinâmico para resultado da pesquisa
    resultado_pesquisa = ft.Container()
    recomendacao_ui = ft.Container()

    # Campo de código do produto
    campo_codigo = ft.TextField(label="Código", hint_text="ex.: 32581")
   
   
    # Função para atualizar o resultado da pesquisa dinamicamente
    def atualizar_resultado_ui(codigo):
        pesquisa_produto = consultas.PesquisaProduto()
        resultado = pesquisa_produto.buscar_produto(codigo)

        if "mensagem" in resultado:
            resultado_pesquisa.content = ft.Column(
                [
                    ft.Text("RESULTADO DA PESQUISA:", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
                    ft.Text(resultado["mensagem"],
                            style=ft.TextStyle(size=18, color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD))
                ]
            )
            recomendacao_ui.content = None  # não mostra recomendação
        else:
            resultado_pesquisa.content = ft.Column(
                [
                    ft.Text("RESULTADO DA PESQUISA:", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
                    ft.Text(
                        spans=[
                            ft.TextSpan(f"Item {resultado['codigo_produto']} - "),
                            ft.TextSpan(f"{resultado['descricao_produto']}", style=ft.TextStyle(size=18, weight="bold", color=ft.Colors.BLUE)),
                            ft.TextSpan(" - Valor "),
                            ft.TextSpan(f"R$ {resultado['valor_unitario']}", style=ft.TextStyle(size=18, weight="bold", color=ft.Colors.BLUE)),
                            ft.TextSpan(", tem uma Margem "),
                            ft.TextSpan(f"{resultado['margem_percent']} %", style=ft.TextStyle(size=18, weight="bold", color=ft.Colors.BLUE)),
                            ft.TextSpan(f" com estoque de {resultado['quantidade_estoque']} unidades."),
                        ],
                        size=16
                    )
                ]
            )

            # Cria a tabela de recomendação
            tabela = consultas.TabelaRecomendacao(pesquisa_produto.engine)
            recomendacao_ui.content = tabela.criar_tabela(resultado['codigo_produto'])

        page.update()


        # Botão de pesquisa
    botao_pesquisar = ft.TextButton(
        content=ft.Row([ft.Icon(ft.Icons.SEARCH, size=20), ft.Text("Pesquisar")]),
        on_click=lambda e: atualizar_resultado_ui(campo_codigo.value)
    )

    barra_pesquisa = ft.Row(
        [
            campo_codigo, 
            botao_pesquisar,
            ft.Row([ft.TextButton(text="Limpar pesquisa")],alignment=ft.MainAxisAlignment.END),
            ft.Row(
                [
                    botao_atualizar,
                    ft.Column(controls=[log_text,
                    ft.Row(controls=[barra_progresso, pbl], alignment=ft.MainAxisAlignment.SPACE_EVENLY)])
                ],alignment=ft.MainAxisAlignment.CENTER),
        ],
        alignment=ft.MainAxisAlignment.START,
    )
 
    associados = ft.Container(
    content=ft.Column(
        controls=[
            ft.Text(f"PRODUTOS QUE NORMALMENTE SÃO COMPRADOS JUNTOS COM {campo_codigo} - {campo_codigo.value}", 
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
            recomendacao_ui,
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