import flet as ft


class ManualSistema(ft.Container):
    def __init__(self):
        super().__init__()
        self.content = ft.Column(
            [
                ft.Text("📘 Como usar o Sistema", size=22, weight="bold"),

                ft.Text("Visão Geral", size=20, weight="bold"),
                ft.Text(
                    "O Sistema de Recomendação analisa dados de estoque e notas fiscais "
                    "para sugerir produtos durante uma venda de duas formas:\n\n"
                    "1. Substitutos → Sugere itens similares da mesma categoria quando "
                    "um produto não está disponível ou para oferecer alternativas de preço e margem.\n"
                    "2. Associados → Indica produtos frequentemente comprados juntos.\n\n"
                    "O objetivo é aumentar o ticket médio de vendas com sugestões inteligentes e relevantes.",
                    text_align=ft.TextAlign.JUSTIFY,
                    size=16
                ),

                ft.Text("🔍 Como Pesquisar", size=20, weight="bold"),
                ft.Text(
                    "- Digite um código de produto ou código de categoria no campo de pesquisa.\n"
                    "- Clique no botão pesquisar.\n"
                    "- O sistema informará os resultados.",
                    text_align=ft.TextAlign.JUSTIFY,
                    size=16
                ),

                ft.Text("📊 Resultados", size=20, weight="bold"),
                ft.Text(
                    "Caso 1: Produto Encontrado → Exibe dados completos do item, lista de substitutos e associados.\n"
                    "Caso 2: Código Inválido → Mensagem informativa será exibida.",
                    text_align=ft.TextAlign.JUSTIFY,
                    size=16
                ),

                ft.Text("⚡ Funcionalidades", size=20, weight="bold"),
                ft.Text(
                    "- Botão Limpar → Volta à página inicial com manual.\n"
                    "- Botão Atualizar Base → Recarrega dados mais recentes para alimentar o sistema.",
                    text_align=ft.TextAlign.JUSTIFY,
                    size=16
                ),

                ft.Text("💡 Dicas", size=20, weight="bold"),
                ft.Text(
                    "- Use códigos completos para maior precisão.\n"
                    "- Verifique substitutos para opções alternativas.\n"
                    "- Explore os produtos vendidos juntos para aumentar as vendas.",
                    text_align=ft.TextAlign.JUSTIFY,
                    size=16
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=10,
        )

        self.padding = 22
        self.border_radius = 30
        self.bgcolor = ft.Colors.WHITE38
        self.expand = True
