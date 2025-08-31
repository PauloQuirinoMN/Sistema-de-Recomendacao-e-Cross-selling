import flet as ft
import asyncio
import threading
from sqlalchemy import create_engine

from alimentador_banco2 import AtualizadorBase
import consultas
from consultas import TabelaAssociados
from manual import ManualSistema


def main(page: ft.Page):
    
    # ---------------- CONFIGURAÇÕES DA JANELA ----------------
    page.title = "Recomenda"
    page.window_width = 200
    page.window_height = 600
    page.window_resizable = True
    page.window_prevent_close = True
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_maximized = True

    # ---------------- CONEXÃO COM BANCO ----------------
    engine = create_engine(
        f"postgresql+psycopg2://postgres:dev2025@192.168.0.200:5432/rec",
    )

    # ---------------- INSTÂNCIAS PRINCIPAIS ----------------
    atualizador = AtualizadorBase()
    tabela_associados = TabelaAssociados(engine)

    # ---------------- ELEMENTOS DE UI FIXOS ----------------
    try:
        with open("ultima_atualizacao.txt", "r", encoding="utf-8") as f:
            ultima_msg = f.read().strip()
            if not ultima_msg:
                ultima_msg = "Nenhuma atualização registrada ainda."
    except FileNotFoundError:
        ultima_msg = "Nenhuma atualização registrada ainda."

    titulo = ft.Text(
        "Bem-vindo ao Sistema de Recomendações",
        size=20,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLUE_800,
    )

    barra_progresso = ft.ProgressBar(value=0.0, width=350)
    pbl = ft.Text("0%", size=14, weight=ft.FontWeight.BOLD)
    log_text = ft.Text("", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)
    log_atualizacao = ft.Text(value=ultima_msg, size=14, color=ft.Colors.BLACK)

    # 🔹 Sincroniza log_text com a última atualização
    log_text = ft.Text(ultima_msg, size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)
    log_atualizacao = ft.Text(value=ultima_msg, size=14, color=ft.Colors.BLACK)

    campo_codigo = ft.TextField(label="Código", hint_text="ex.: 32581")
    resultado_pesquisa = ft.Container()
    container_associados = ft.Container()
    recomendacao_ui = ft.Container(content=ManualSistema())

    # ---------------- FUNÇÕES DE APOIO ----------------
    def atualizar_log(data, qtd_itens):
        """Atualiza log de última atualização"""
        log_atualizacao.value = f"Última Atualização em {data} - {qtd_itens} itens"
        log_text.value = log_atualizacao.value
        page.update()

    # 🔹 Reinstancia o atualizador com callback
    atualizador = AtualizadorBase(log_callback=atualizar_log)

    def mostrar_progresso(atual: int, total: int):
        """Atualiza a barra de progresso durante atualização da base"""
        if total > 50 and atual % max(5, total // 50) != 0:
            return

        progresso = atual / total

        async def _update():
            barra_progresso.value = progresso
            pbl.value = f"{int(progresso * 100)}%"
            page.update()

        loop = asyncio.get_running_loop()
        asyncio.run_coroutine_threadsafe(_update(), loop)

    def mostrar_log(mensagem: str):
        """Atualiza log de processamento"""
        async def _update():
            log_text.value = mensagem
            page.update()

        loop = asyncio.get_running_loop()
        asyncio.run_coroutine_threadsafe(_update(), loop)

    def rodar_atualizacao(e):
        """Thread para atualizar a base e interface"""
        threading.Thread(
            target=lambda: asyncio.run(
                atualizador.atualizar_base(
                    intervalo_codigos=(0, 10000000),
                    progresso_callback=mostrar_progresso,
                    log_callback=mostrar_log,
                    fim_callback=atualizar_log,
                )
            ),
            daemon=True,
        ).start()

    # ---------------- FUNÇÕES DE PESQUISA ----------------
    def limpar_pesquisa(e):
        campo_codigo.value = ""
        resultado_pesquisa.content = None
        container_associados.content = None
        recomendacao_ui.content = ManualSistema()
        page.update()

    def atualizar_resultado_ui(codigo: str):
        pesquisa_produto = consultas.PesquisaProduto(engine=engine)
        resultado = pesquisa_produto.buscar_produto(codigo)

        # ---------------- CASO ERRO ----------------
        if isinstance(resultado, dict) and "erro" in resultado:
            resultado_pesquisa.content = ft.Column(
                [
                    ft.Text(
                        "RESULTADO DA PESQUISA:",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_800,
                    ),
                    ft.Text(
                        resultado["erro"],
                        style=ft.TextStyle(
                            size=18, color=ft.Colors.RED, weight=ft.FontWeight.BOLD
                        ),
                    ),
                ]
            )
            recomendacao_ui.content = ManualSistema()
            page.update()
            return

        # ---------------- CASO MENSAGEM (NÃO ENCONTRADO) ----------------
        if isinstance(resultado, dict) and "mensagem" in resultado:
            resultado_pesquisa.content = ft.Column(
                [
                    ft.Text(
                        "RESULTADO DA PESQUISA:",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_800,
                    ),
                    ft.Text(
                        resultado["mensagem"],
                        style=ft.TextStyle(
                            size=18, color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD
                        ),
                    ),
                ]
            )
            recomendacao_ui.content = None
            page.update()
            return

        # ---------------- PRODUTO VÁLIDO ----------------
        resultado_pesquisa.content = ft.Column(
            [
                ft.Text(
                    "RESULTADO DA PESQUISA:",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_800,
                ),
                ft.Text(
                    spans=[
                        ft.TextSpan(
                            f"Item {resultado['codigo_produto']} - ",
                            style=ft.TextStyle(
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.BLACK45,
                            ),
                        ),
                        ft.TextSpan(
                            f"{resultado['descricao_produto']}",
                            style=ft.TextStyle(
                                size=18, weight="bold", color=ft.Colors.BLACK87
                            ),
                        ),
                        # ft.TextSpan(
                        #     " - Valor ",
                        #     style=ft.TextStyle(
                        #         size=16, color=ft.Colors.BLACK45, weight=ft.FontWeight.BOLD
                        #     ),
                        # ),
                        # ft.TextSpan(
                        #     f"R$ {resultado['valor_unitario']}",
                        #     style=ft.TextStyle(
                        #         size=18, weight="bold", color=ft.Colors.BLACK87
                        #     ),
                        # ),
                        ft.TextSpan(
                            ", uma Margem de ",
                            style=ft.TextStyle(
                                size=16, color=ft.Colors.BLACK45, weight=ft.FontWeight.BOLD
                            ),
                        ),
                        ft.TextSpan(
                            f"{resultado['margem_percent']} %",
                            style=ft.TextStyle(
                                size=18, weight="bold", color=ft.Colors.BLACK87
                            ),
                        ),
                        ft.TextSpan(
                            " com estoque de - ",
                            style=ft.TextStyle(
                                size=16, weight="bold", color=ft.Colors.BLACK45
                            ),
                        ),
                        ft.TextSpan(
                            f"{resultado['quantidade_estoque']}",
                            style=ft.TextStyle(
                                size=18, weight="bold", color=ft.Colors.BLACK87
                            ),
                        ),
                        ft.TextSpan(
                            " unidades.",
                            style=ft.TextStyle(
                                size=16, weight="bold", color=ft.Colors.BLACK45
                            ),
                        ),
                    ],
                    size=16,
                ),
            ]
        )

        tabela = consultas.TabelaRecomendacao(pesquisa_produto.engine)
        recomendacao_ui.content = tabela.criar_tabela(resultado["codigo_produto"])
        page.update()

    def atualizar_tabelas(e):
        codigo = (campo_pesquisar.value or "").strip()
        atualizar_resultado_ui(codigo)
        container_associados.content = tabela_associados.criar_tabela(codigo)
        container_associados.update()

    # ---------------- BARRA DE AÇÕES ----------------
    botao_atualizar = ft.IconButton(
        icon=ft.Icons.UPDATE_SHARP, tooltip="Atualizar bases de dados", on_click=rodar_atualizacao, disabled=True
    )

    campo_pesquisar = ft.TextField(
        label="Código",
        prefix_icon=ft.Icons.SEARCH,
        autofocus=True,
        on_submit=atualizar_tabelas,
        content_padding=ft.padding.only(left=10),
        border_color=ft.Colors.TRANSPARENT,
        filled=True,
        bgcolor=ft.Colors.WHITE,
        height=40,
        width=200,
        text_size=14,
    )

    barra_pesquisa = ft.Row(
        [
            # campo_codigo,
            campo_pesquisar,
            ft.TextButton(text="Limpar pesquisa", on_click=limpar_pesquisa),
            ft.Row(
                [
                    botao_atualizar,
                    ft.Column(
                        controls=[
                            log_text,
                            ft.Row(
                                controls=[barra_progresso, pbl],
                                alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                            ),
                        ]
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        ],
        alignment=ft.MainAxisAlignment.START,
    )

    # ---------------- LAYOUT PRINCIPAL ----------------
    conteudo = ft.Column(
        [
            resultado_pesquisa,
            ft.Divider(height=1),
            recomendacao_ui,
            ft.Divider(height=10),
            container_associados,
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=0,
        scroll=ft.ScrollMode.AUTO,
    )

    layout_principal = ft.Column(
        [barra_pesquisa, ft.Divider(height=1), conteudo],
        expand=True,
        scroll=True,
        spacing=10,
    )

    barra_status = ft.Text(
        "Sistema Recomenda mvp v1.0 - © 2025 - Paulo Quirino",
        size=12,
        color=ft.Colors.GREY,
    )

    # ---------------- LÊ ÚLTIMA ATUALIZAÇÃO ----------------
    container_logs = ft.Column()

    def _log(msg):
        container_logs.controls.append(ft.Text(msg))
        page.update()

    try:
        with open("ultima_atualizacao.txt", "r", encoding="utf-8") as f:
            ultima_msg = f.read().strip()
            _log(ultima_msg if ultima_msg else "Nenhuma atualização registrada ainda.")
    except FileNotFoundError:
        _log("Nenhuma atualização registrada ainda.")
    
    # ---------------- MONTA PÁGINA ----------------
    page.add(
        titulo,
        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
        layout_principal,
        ft.Divider(),
        barra_status
    )
   

# ---------------- INÍCIO APP ----------------
if __name__ == '__main__':
    ft.app(target=main, view=ft.AppView.FLET_APP)
