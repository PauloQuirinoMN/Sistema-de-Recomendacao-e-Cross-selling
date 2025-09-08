import flet as ft

''
class ManualSistema(ft.Container):
    def __init__(self):
        super().__init__()
        self.content = ft.Column(
            [
                ft.Text("📘 Como usar o Sistema", size=26, weight="bold"),

                ft.Text("Visão Geral", size=22, weight="bold"),
                ft.Text(
                    "O Sistema de Recomendação analisa dados de estoque e notas fiscais "
                    "para sugerir produtos durante uma venda de duas formas:\n"
                    "1. Substitutos → Sugere itens similares quando um produto não está disponível ou "
                    "para oferecer alternativas de preço e margem.\n"
                    "2. Associados → Indica produtos frequentemente comprados juntos.\n\n"
                    "O objetivo é aumentar o ticket médio com sugestões inteligentes e relevantes.",
                    text_align=ft.TextAlign.JUSTIFY,
                    size=18
                ),

                ft.Text("Como Funciona", size=22, weight="bold"),
                ft.Text(
                    "O sistema mostra automaticamente, ao pesquisar um produto:\n"
                    "- Informações do produto pesquisado\n"
                    "- Tabela de Substitutos\n"
                    "- Tabela de Associados",
                    text_align=ft.TextAlign.JUSTIFY,
                    size=18
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=10,
        )

        self.padding = 12
        self.border_radius = 30
        self.bgcolor = ft.Colors.WHITE38
        self.expand = True
