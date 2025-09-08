import flet as ft
import psycopg2
from typing import Optional

# ------------------------
# Configurações do banco
# ------------------------
DB_CONFIG = dict(
    dbname="rec",
    user="postgres",
    password="dev2025",
    host="192.168.0.200",
    port="5432"
)


def format_pct(x: float, precision: int = 2) -> str:
    try:
        return f"{x:.{precision}f}"
    except Exception:
        return str(x)


def calcular_margem(preco_custo: Optional[float], preco_venda: Optional[float]) -> Optional[float]:
    """Calcula margem percentual.

    - Fórmula escolhida (margem bruta sobre o preço de venda):
        margem% = (preco_venda - preco_custo) / preco_venda * 100

    Observações:
    - Usei o preço de venda médio histórico (AVG(valor_unitario) em itens_notas) quando disponível.
    - Se não houver preço de venda ou custo válido, retorna None.
    """
    if preco_venda is None or preco_venda == 0:
        return None
    if preco_custo is None:
        return None
    try:
        return (preco_venda - preco_custo) / preco_venda * 100
    except Exception:
        return None


def main(page: ft.Page):
    # ---------------- CONFIGURAÇÕES DA JANELA ----------------
    page.title = "Recomenda"
    page.window_width = 700
    page.window_height = 700
    page.window_resizable = True
    page.theme_mode = ft.ThemeMode.LIGHT

    # ---------------- CONEXÃO COM BANCO ----------------
    try:
        conn = psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        page.add(ft.Text(f"Erro ao conectar ao banco: {e}", color=ft.Colors.RED))
        return

    # ---------------- VARIÁVEIS DE LOG (mantidas, mas vazias) ----------------
    log_text = ft.Text("", size=12)
    barra_progresso = ft.Text("")
    pbl = ft.Text("")

    # ---------------- CONTAINERS DINÂMICOS ----------------
    resultado_pesquisa = ft.Container()
    recomendacao_ui = ft.Container()

    # ---------------- FUNÇÕES ----------------
    def limpar_pesquisa(e: Optional[ft.ControlEvent] = None):
        campo_pesquisar.value = ""
        resultado_pesquisa.content = None
        recomendacao_ui.content = None
        page.update()

    def pesquisar(e: Optional[ft.ControlEvent] = None):
        """Executa a pesquisa por código do produto e atualiza a interface com informações do produto.

        Lógica:
        1) Busca o produto em `produtos` pelo `codigo_produto`.
        2) Obtém o preço de venda médio a partir de `itens_notas` (AVG(valor_unitario)).
        3) Calcula margem percentual usando `calcular_margem`.
        4) Mostra resultado formatado no `resultado_pesquisa`.
        """
        query_val = campo_pesquisar.value or ""
        query_val = query_val.strip()

        if not query_val:
            resultado_pesquisa.content = ft.Text("Digite o código do produto e pressione Enter ou clique em Pesquisar.")
            page.update()
            return

        # tentar interpretar como inteiro (código do ERP)
        try:
            codigo = int(query_val)
        except ValueError:
            resultado_pesquisa.content = ft.Text("Código inválido. Informe apenas números.")
            page.update()
            return

        # 1) busca o produto
        sql_prod = (
            "SELECT id, codigo_produto, descricao_produto, preco_custo, quantidade_estoque "
            "FROM produtos WHERE codigo_produto = %s LIMIT 1;"
        )

        try:
            with conn.cursor() as cur:
                cur.execute(sql_prod, (codigo,))
                prod_row = cur.fetchone()
        except Exception as ex:
            resultado_pesquisa.content = ft.Text(f"Erro ao consultar o banco: {ex}")
            page.update()
            return

        if not prod_row:
            # ---------------- CASO MENSAGEM (NÃO ENCONTRADO) ----------------
            resultado = {"mensagem": f"Produto {codigo} não encontrado."}
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

        # extrai dados do produto
        produto_id, codigo_produto, descricao_produto, preco_custo, quantidade_estoque = prod_row

        # 2) busca preço médio de venda (itens_notas)
        sql_preco_avg = (
            "SELECT AVG(valor_unitario) FROM itens_notas WHERE produto_id = %s AND valor_unitario IS NOT NULL;"
        )

        try:
            with conn.cursor() as cur:
                cur.execute(sql_preco_avg, (produto_id,))
                price_row = cur.fetchone()
                preco_venda_media = price_row[0] if price_row is not None else None
        except Exception:
            preco_venda_media = None

        margem = calcular_margem(preco_custo, preco_venda_media)
        margem_display = format_pct(margem, precision=2) + " %" if margem is not None else "N/D"

        # ---------------- PRODUTO VÁLIDO ----------------
        resultado = {
            "codigo_produto": codigo_produto,
            "descricao_produto": descricao_produto,
            "margem_percent": margem_display,
            "quantidade_estoque": quantidade_estoque,
        }

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
                        ft.TextSpan(
                            ", uma Margem de ",
                            style=ft.TextStyle(
                                size=16, color=ft.Colors.BLACK45, weight=ft.FontWeight.BOLD
                            ),
                        ),
                        ft.TextSpan(
                            f"{resultado['margem_percent']}",
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
        page.update()

    # ---------------- ELEMENTOS DA INTERFACE ----------------
    titulo = ft.Text(
        "Bem-vindo ao Sistema de Recomendações",
        size=20,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLUE_800,
    )

    campo_pesquisar = ft.TextField(
        label="Código do produto",
        prefix_icon=ft.Icons.SEARCH,
        autofocus=True,
        on_submit=pesquisar,
        content_padding=ft.padding.only(left=10),
        border_color=ft.Colors.TRANSPARENT,
        filled=True,
        bgcolor=ft.Colors.WHITE,
        height=40,
        width=260,
        text_size=14,
    )

    botao_pesquisar = ft.IconButton(icon=ft.Icons.SEARCH, tooltip="Pesquisar", on_click=pesquisar)
    botao_limpar = ft.TextButton(text="Limpar pesquisa", on_click=limpar_pesquisa)

    barra_pesquisa = ft.Row(
        [
            campo_pesquisar,
            botao_pesquisar,
            botao_limpar,
        ],
        alignment=ft.MainAxisAlignment.START,
        spacing=10,
    )

    conteudo = ft.Column(
        [
            resultado_pesquisa,
            ft.Divider(height=10),
            recomendacao_ui,
        ],
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    barra_status = ft.Text(
        "Sistema Recomenda MVP v1.0 - © 2025 - Paulo Quirino",
        size=12,
        color=ft.Colors.GREY,
    )

    layout_principal = ft.Column(
        [titulo, ft.Divider(height=8), barra_pesquisa, ft.Divider(height=8), conteudo, ft.Divider(), barra_status],
        expand=True,
        scroll=True,
        spacing=12,
    )

    page.add(layout_principal)

    # garante que a conexão seja fechada ao fechar a janela
    def on_close(e):
        try:
            conn.close()
        except Exception:
            pass

    page.on_close = on_close


if __name__ == "__main__":
    ft.app(target=main)
