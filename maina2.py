import flet as ft
from alimentador_banco2 import AtualizadorBase
# import pandas as pd
# from limpeza_base_mesclada import BasePreparador
import asyncio
import threading
import consultas 
from consultas import TabelaAssociados
from sqlalchemy import create_engine

# Cria conexão com o banco
# engine = create_engine("postgresql+psycopg2://postgres:recomenda@localhost:5432/bd_recomenda")



def main(page: ft.Page):
    page.title = "Recomenda"
    page.window_width = 800
    page.window_height = 600
    page.window_resizable = True
    page.window_prevent_close = True
    page.theme_mode = ft.ThemeMode.LIGHT

    engine = create_engine("postgresql+psycopg2://postgres:recomenda@localhost:5432/bd_recomenda")


    # logs e barra de progresso
    barra_progresso = ft.ProgressBar(value=0.0, width=250)
    pbl = ft.Text("0%", size=14, weight=ft.FontWeight.BOLD)
    log_text = ft.Text("", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)

    atualizador = AtualizadorBase()

    # -------- FUNÇÕES DE ATUALIZAÇÃO --------
      # Função para atualizar progresso
    def mostrar_progresso(atual: int, total: int):

    # Atualiza a cada 2% ou a cada 50 produtos
        if total > 50 and atual % max(5, total // 50) != 0:
            return
        
        progresso = atual / total
        async def _update():
            barra_progresso.value = progresso
            pbl.value = f"{int(progresso*100)}%"
            page.update()
        
        loop = asyncio.get_running_loop()
        asyncio.run_coroutine_threadsafe(_update(), loop)


    # Função para atualizar log(mensagens)
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
                intervalo_codigos=(0, 2500),
                progresso_callback=mostrar_progresso,
                log_callback=mostrar_log
            )),
            daemon=True
        ).start()

    # Botão de atualização da base de dados    
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

    # Instancia a classe de associados
    tabela_associados = TabelaAssociados(engine)

    # Container vazio para resultados de associados (será atualizado dinamicamente)
    container_associados = ft.Container()

    # Containers de resultados da pesquisa e recomendação
    resultado_pesquisa = ft.Container()
    recomendacao_ui = ft.Container()

    # Função para atualizar tabela de associados
    def atualizar_associados(e):
        codigo = campo_codigo.value.strip()
        container_associados.content = tabela_associados.criar_tabela(codigo)
        container_associados.update()

    # Função para atualizar a pesquisa e recomendação
    def atualizar_resultado_ui(codigo):
        pesquisa_produto = consultas.PesquisaProduto()
        resultado = pesquisa_produto.buscar_produto(codigo)

        if "mensagem" in resultado:
            resultado_pesquisa.content = ft.Column(
                [
                    ft.Text("RESULTADO DA PESQUISA:", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
                    ft.Text(resultado["mensagem"], style=ft.TextStyle(size=18, color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD))
                ]
            )
            recomendacao_ui.content = None
        else:
            resultado_pesquisa.content = ft.Column(
                [
                    ft.Text("RESULTADO DA PESQUISA:", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
                    ft.Text(
                        spans=[
                            ft.TextSpan(f"Item {resultado['codigo_produto']} - "),
                            ft.TextSpan(f"{resultado['descricao_produto']}", style=ft.TextStyle(size=18, weight='bold', color=ft.Colors.BLUE)),
                            ft.TextSpan(" - Valor "),
                            ft.TextSpan(f"R$ {resultado['valor_unitario']}", style=ft.TextStyle(size=18, weight='bold', color=ft.Colors.BLUE)),
                            ft.TextSpan(", tem uma Margem "),
                            ft.TextSpan(f"{resultado['margem_percent']} %", style=ft.TextStyle(size=18, weight='bold', color=ft.Colors.BLUE)),
                            ft.TextSpan(f" com estoque de {resultado['quantidade_estoque']} unidades.", style=ft.TextStyle(size=18, weight='bold', color=ft.Colors.BLUE)),
                        ],
                        size=16
                    )
                ]
            )
            # Atualiza a tabela de substitutos
            tabela = consultas.TabelaRecomendacao(pesquisa_produto.engine)
            recomendacao_ui.content = tabela.criar_tabela(resultado['codigo_produto'])
        page.update()

    # Função que atualiza **substitutos + associados** ao clicar no botão
    def atualizar_tabelas(e):
        codigo = campo_codigo.value.strip()
        atualizar_resultado_ui(codigo)
        atualizar_associados(e)

    # Botão de pesquisa
    botao_pesquisar = ft.TextButton(
        content=ft.Row([ft.Icon(ft.Icons.SEARCH, size=20), ft.Text("Pesquisar")]),
        on_click=atualizar_tabelas  # chama a função completa
    )

    # Barra de pesquisa e botões
    barra_pesquisa = ft.Row(
        [
            campo_codigo,
            botao_pesquisar,
            ft.Row([ft.TextButton(text="Limpar pesquisa")], alignment=ft.MainAxisAlignment.END),
            ft.Row(
                [
                    botao_atualizar,
                    ft.Column(
                        controls=[
                            log_text,
                            ft.Row(controls=[barra_progresso, pbl], alignment=ft.MainAxisAlignment.SPACE_EVENLY)
                        ]
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER
            ),
        ],
        alignment=ft.MainAxisAlignment.START,
    )

    # Área de conteúdo principal
    conteudo = ft.Column(
        [
            resultado_pesquisa,
            ft.Divider(height=1),
            recomendacao_ui,
            ft.Divider(height=10),
            container_associados,  # <- Container já adicionado aqui
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
    barra_status = ft.Text("Sistema Recomenda mvp v1.0 - © 2025 - Paulo Quirino", size=12, color=ft.Colors.GREY)

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