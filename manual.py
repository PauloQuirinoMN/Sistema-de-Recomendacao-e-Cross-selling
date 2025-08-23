import flet as ft


class ManualSistema(ft.Container):
    def __init__(self):
        super().__init__()
        self.content = ft.Column(
            [
                ft.Text("📘 Como usar o Sistema", size=20, weight="bold"),

                ft.Text("Visão Geral", size=18, weight="bold"),
                ft.Text(
                    "O Sistema de Recomendação analisa dados de estoque e notas fiscais "
                    "para sugerir produtos durante uma venda de duas formas:\n"
                    "1. Substitutos → Sugere itens similares da mesma categoria quando "
                    "um produto não está disponível ou para oferecer alternativas de preço e margem.\n"
                    "2. Associados → Indica produtos frequentemente comprados juntos.\n"
                    "O objetivo é aumentar o ticket médio de vendas com sugestões inteligentes e relevantes.",
                    text_align=ft.TextAlign.JUSTIFY,
                    size=14
                ),

                ft.Text("🔍 Como Funciona", size=18, weight="bold"),
                ft.Text(
                    "- Digite um código de produto no campo de pesquisa.\n"
                    "- Clique no botão pesquisar.\n"
                    "- O sistema irá mostrar as informações do produto pesquisado\n." \
                    "  Se o código for inválido, uma mensagem de erro será exibida.\n" \
                    "- Caso o produto seja encontrado, serão exibidos:\n    " \
                    "- duas tabelas:\n" \
                    "      1. Substitutos → Itens similares com informações de preço e margem.\n"
                    '      2. Associados → Produtos frequentemente comprados juntos.\n',
                    text_align=ft.TextAlign.JUSTIFY,
                    size=14
                ),

                ft.Text("💡 Dicas", size=18, weight="bold"),
                ft.Text(
                    "- Use códigos completos para maior precisão.\n"
                    "- Verifique substitutos para opções alternativas.\n"
                    "- Explore os produtos vendidos juntos para aumentar as vendas.",
                    text_align=ft.TextAlign.JUSTIFY,
                    size=14
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=10,
        )

        self.padding = 12
        self.border_radius = 30
        self.bgcolor = ft.Colors.WHITE38
        self.expand = True
