# atualizar.py
import os
import pandas as pd
import shutil
import threading
import flet as ft
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from atualizador_regras import AtualizarRegras
from associados import CrossSellingSimples  # sua classe


class AtualizacaoComponent(ft.Column):
    """
    Componente para controlar atualização (upload .xlsx + executar AtualizarRegras).
    Uso:
        comp = AtualizacaoComponent(conn_str, page)
        page.add(comp)
    """

    def __init__(self, conn_str: str, page: Optional[ft.Page] = None):
        super().__init__()
        self.conn_str = conn_str
        self.page: Optional[ft.Page] = page

        # engine SQLAlchemy para consultas de stats
        try:
            self.engine = create_engine(conn_str)
        except Exception:
            self.engine = None

        # estado
        self.arquivo_estoque: Optional[str] = None
        self.arquivo_notas: Optional[str] = None
        self.senha_ok: bool = False
        self._filepickers_attached = False

        # labels e elementos UI
        self.txt_ultima = ft.Text("Última atualização: —", size=12)
        self.txt_produtos = ft.Text("0", size=18, weight=ft.FontWeight.BOLD)
        self.txt_associados = ft.Text("0", size=18, weight=ft.FontWeight.BOLD)

        self.label_arquivo_estoque = ft.Text("Nenhum arquivo", size=12)
        self.label_arquivo_notas = ft.Text("Nenhum arquivo", size=12)

        # botões principais
        self.btn_liberar = ft.TextButton("Liberar", on_click=lambda e: self._toggle_password_row())
        self.btn_upload_estoque = ft.IconButton(
            icon=ft.Icons.UPLOAD_FILE,  # corrigido
            tooltip="Carregar .xlsx (estoque)",
            disabled=True,
            on_click=lambda e: self.pick_estoque(e),
        )
        self.btn_upload_notas = ft.IconButton(
            icon=ft.Icons.UPLOAD_FILE,  # corrigido
            tooltip="Carregar .xlsx (notas)",
            disabled=True,
            on_click=lambda e: self.pick_notas(e),
        )
        self.btn_atualizar = ft.TextButton("Atualizar", disabled=True, on_click=lambda e: self.on_click_atualizar(e))

        # campo de senha inline (inicialmente escondido)
        self.pwd_field = ft.TextField(password=True, width=260, visible=False, on_submit=lambda ev: self._confirm_password(ev))
        self.btn_confirm_pwd = ft.TextButton("Confirmar", visible=False, on_click=lambda e: self._confirm_password(e))
        self.btn_cancel_pwd = ft.TextButton("Cancelar", visible=False, on_click=lambda e: self._cancel_password(e))
        self.password_row = ft.Row([self.pwd_field, self.btn_confirm_pwd, self.btn_cancel_pwd], spacing=6, visible=False)

        # FilePickers (anexar depois via attach_to_page)
        self.file_picker_estoque = ft.FilePicker(on_result=self._on_estoque_result)
        self.file_picker_notas = ft.FilePicker(on_result=self._on_notas_result)

        # monta layout
        self.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row([ft.Text("Última atualização", weight=ft.FontWeight.BOLD), self.txt_ultima],
                               alignment=ft.MainAxisAlignment.CENTER),
                        ft.Divider(height=10, color=ft.Colors.BLACK12),
                        self.password_row,
                        ft.Row(
                            controls=[
                                ft.Column([self.btn_liberar, self.btn_atualizar],
                                          alignment=ft.MainAxisAlignment.CENTER, spacing=2),
                                ft.VerticalDivider(width=6),
                                ft.Column(
                                    controls=[
                                        ft.Row([self.btn_upload_estoque, self.label_arquivo_estoque], alignment=ft.MainAxisAlignment.CENTER),
                                        ft.Row([self.btn_upload_notas, self.label_arquivo_notas], alignment=ft.MainAxisAlignment.CENTER),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                                    spacing=2,
                                ),
                                ft.VerticalDivider(width=6),
                                ft.Column([self.txt_produtos, ft.Text("Produtos")], alignment=ft.MainAxisAlignment.CENTER, spacing=1),
                                ft.VerticalDivider(width=6),
                                ft.Column([self.txt_associados, ft.Text("Associados")], alignment=ft.MainAxisAlignment.CENTER, spacing=1),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                        ),
                        ft.Divider(height=6),
                    ],
                    spacing=6,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=10,
                bgcolor=ft.Colors.WHITE,
                border=ft.border.all(1, ft.Colors.BLACK12),
                border_radius=8,
                expand=True,
                height=140,
                width=600,
            )
        ]

        # tenta buscar stats já (se engine ok)
        try:
            self.refresh_stats()
        except Exception:
            pass

        # se page fornecida, anexa filepickers e atualiza UI
        if self.page is not None:
            try:
                self.attach_to_page(self.page)
            except Exception:
                pass

    # ---------------- integração com page ----------------
    def attach_to_page(self, page: ft.Page):
        """Anexa filepickers ao page.overlay e guarda referência de page."""
        self.page = page
        if not self._filepickers_attached:
            try:
                if self.file_picker_estoque not in page.overlay:
                    page.overlay.append(self.file_picker_estoque)
                if self.file_picker_notas not in page.overlay:
                    page.overlay.append(self.file_picker_notas)
                self._filepickers_attached = True
            except Exception:
                pass
        # atualiza indicadores
        try:
            self.refresh_stats()
        finally:
            self.update()

    def _get_page(self, e: Optional[ft.ControlEvent]) -> Optional[ft.Page]:
        if e is not None:
            try:
                p = getattr(e, "page", None)
                if p is not None:
                    return p
            except Exception:
                pass
        return self.page

    # ---------------- DB / stats ----------------
    def refresh_stats(self):
        """Consulta o banco e atualiza indicadores (última, contagens)."""
        if not self.engine:
            self.txt_ultima.value = "Sem engine"
            self.txt_produtos.value = "0"
            self.txt_associados.value = "0"
            self.update()
            return

        ultima_sql = text(
            """
            SELECT GREATEST(
                COALESCE((SELECT MAX(data_insercao) FROM produtos), '1970-01-01'::timestamp),
                COALESCE((SELECT MAX(data_insercao) FROM itens_notas), '1970-01-01'::timestamp),
                COALESCE((SELECT MAX(data_atualizacao) FROM metricas), '1970-01-01'::timestamp)
            ) AS ultima;
            """
        )
        cnt_produtos_sql = text("SELECT COUNT(DISTINCT antecedente_id) FROM metricas;")
        cnt_associados_sql = text("SELECT COUNT(consequente_id) FROM metricas;")

        try:
            with self.engine.connect() as conn:
                r = conn.execute(ultima_sql).scalar()
                if r is not None:
                    try:
                        ts = r.strftime("%d/%m/%Y -> %H:%M:%S")
                    except Exception:
                        ts = str(r)
                    self.txt_ultima.value = ts
                else:
                    self.txt_ultima.value = "Sem registros"

                cnt_p = conn.execute(cnt_produtos_sql).scalar() or 0
                cnt_a = conn.execute(cnt_associados_sql).scalar() or 0
                self.txt_produtos.value = str(int(cnt_p))
                self.txt_associados.value = str(int(cnt_a))
        except SQLAlchemyError:
            self.txt_ultima.value = "Erro ao ler DB"
        except Exception:
            self.txt_ultima.value = "Erro"
        finally:
            self.update()

    # ---------------- password inline ----------------
    def _toggle_password_row(self):
        """Mostra/oculta o campo de senha inline."""
        show = not self.password_row.visible
        self.password_row.visible = show
        self.pwd_field.visible = show
        self.btn_confirm_pwd.visible = show
        self.btn_cancel_pwd.visible = show
        if show:
            # limpa campo
            self.pwd_field.value = ""
            self.pwd_field.error_text = None
        self.update()

    def _confirm_password(self, e=None):
        val = (self.pwd_field.value or "").strip()
        if val == "1234":
            self.senha_ok = True
            self.btn_upload_estoque.disabled = False
            self.btn_upload_notas.disabled = False
            # esconde a senha
            self.password_row.visible = False
            self.pwd_field.visible = False
            self.btn_confirm_pwd.visible = False
            self.btn_cancel_pwd.visible = False
            self._verificar_pronto()
        else:
            self.pwd_field.error_text = "Senha incorreta"
        self.update()

    def _cancel_password(self, e=None):
        self.password_row.visible = False
        self.pwd_field.visible = False
        self.btn_confirm_pwd.visible = False
        self.btn_cancel_pwd.visible = False
        self.pwd_field.value = ""
        self.pwd_field.error_text = None
        self.update()

    # ---------------- file pickers ----------------
    def pick_estoque(self, e: Optional[ft.ControlEvent] = None):
        page = self._get_page(e)
        if not self.senha_ok:
            self._toggle_password_row()
            return
        if page and not self._filepickers_attached:
            self.attach_to_page(page)
        try:
            self.file_picker_estoque.pick_files(allow_multiple=False)
        except Exception:
            if page:
                page.pick_files(allow_multiple=False, on_result=self._on_estoque_result)

    def pick_notas(self, e: Optional[ft.ControlEvent] = None):
        page = self._get_page(e)
        if not self.senha_ok:
            self._toggle_password_row()
            return
        if page and not self._filepickers_attached:
            self.attach_to_page(page)
        try:
            self.file_picker_notas.pick_files(allow_multiple=False)
        except Exception:
            if page:
                page.pick_files(allow_multiple=False, on_result=self._on_notas_result)

    def _on_estoque_result(self, ev: ft.FilePickerResultEvent):
        if ev.files and len(ev.files) > 0:
            f = ev.files[0]
            path = getattr(f, "path", None) or getattr(f, "name", None)
            self.arquivo_estoque = path
            self.label_arquivo_estoque.value = getattr(f, "name", path)
        else:
            self.arquivo_estoque = None
            self.label_arquivo_estoque.value = "Nenhum arquivo"
        self._verificar_pronto()
        self.update()

    def _on_notas_result(self, ev: ft.FilePickerResultEvent):
        if ev.files and len(ev.files) > 0:
            f = ev.files[0]
            path = getattr(f, "path", None) or getattr(f, "name", None)
            self.arquivo_notas = path
            self.label_arquivo_notas.value = getattr(f, "name", path)
        else:
            self.arquivo_notas = None
            self.label_arquivo_notas.value = "Nenhum arquivo"
        self._verificar_pronto()
        self.update()

    def _verificar_pronto(self):
        self.btn_atualizar.disabled = not (self.senha_ok and self.arquivo_estoque and self.arquivo_notas)
        self.update()

    # ---------------- executar atualização ----------------
    # ---------------- executar atualização ----------------
    def on_click_atualizar(self, e: Optional[ft.ControlEvent] = None):
        print("🚀 Entrou no on_click!")

        page = self._get_page(e)
        if not self.senha_ok:
            self._toggle_password_row()
            return

        if not (self.arquivo_estoque and self.arquivo_notas):
            if page:
                page.snack_bar = ft.SnackBar(ft.Text("Selecione estoque e notas antes de atualizar."))
                page.snack_bar.open = True
                page.update()
            return

        bases = os.path.join(os.getcwd(), "bases")
        os.makedirs(bases, exist_ok=True)
        dst_estoque = os.path.join(bases, "relatorio_produtos.xlsx")
        dst_notas = os.path.join(bases, "relatorio_notas.xlsx")

        try:
            shutil.copy2(self.arquivo_estoque, dst_estoque)
            shutil.copy2(self.arquivo_notas, dst_notas)
        except Exception as ex:
            if page:
                page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao copiar arquivos: {ex}"))
                page.snack_bar.open = True
                page.update()
            return

        # desabilita botão até terminar
        self.btn_atualizar.disabled = True
        self.update()

        # executa em thread separada para não travar UI
        senha = "dev2025"  # 🔑 aqui você pode parametrizar, hoje está fixo
        threading.Thread(
            target=self._worker, 
            args=(senha, dst_estoque, dst_notas),
            daemon=True
        ).start()

    def _worker(self, senha: str, dst_estoque: str, dst_notas: str):
        print("🚀 Entrou no _worker!")

        try:
            import pandas as pd
            import traceback
            from limpeza_estoque import EstoqueCleaner
            from limpeza_notas import NotasCleaner
            from associados import CrossSellingSimples
            from atualizador_regras import AtualizarRegras

            # --- 1) Lendo arquivos
            print("📂 Lendo arquivos Excel...")
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text("📂 Lendo arquivos Excel..."))
                self.page.snack_bar.open = True
                self.page.update()

            df_produtos_raw = pd.read_excel(dst_estoque, engine="openpyxl")
            df_notas_raw = pd.read_excel(dst_notas, engine="openpyxl")

            # --- 2) Limpeza / Normalização
            print("🧹 Chamando cleaners...")
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text("🧹 Limpando e preparando dados..."))
                self.page.snack_bar.open = True
                self.page.update()

            # CORREÇÃO AQUI: instanciar sem passar o DataFrame
            estoque_cleaner = EstoqueCleaner()
            df_produtos = estoque_cleaner.clean(df_produtos_raw)
            print("🚀 saiu no estoque!")

            notas_cleaner = NotasCleaner()
            df_notas = notas_cleaner.clean(df_notas_raw)
            print("🚀 saiu no notas!")

            # --- utilitário robusto para obter lista de códigos de produto
            def _extrair_lista_produtos(df):
                candidatos = [
                    "codigo_produto", "codigo produto", "codigo", "Código produto",
                    "Codigo produto", "Codigo", "cod_produto", "cod_prod"
                ]
                for c in candidatos:
                    if c in df.columns:
                        return list(df[c].dropna().unique())
                # fallback: pegar todas as colunas numéricas inteiras que parecem códigos
                for c in df.columns:
                    if df[c].dtype.kind in ("i", "u") and df[c].nunique() > 0:
                        return list(df[c].dropna().unique())
                raise KeyError(f"Nenhuma coluna de código produto encontrada. Colunas: {df.columns.tolist()}")

            # --- 3) Gerar cross-selling
            print("🔗 Gerando CrossSellingSimples...")
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text("🔗 Gerando regras de associação..."))
                self.page.snack_bar.open = True
                self.page.update()

            cross_obj = CrossSellingSimples(df_notas=df_notas, df_produtos=df_produtos)

            produtos = _extrair_lista_produtos(df_produtos)
            print(f"Produtos a processar (exemplo 10): {produtos[:10]} (total {len(produtos)})")

            # --- 4) Atualizar no banco
            print("💾 Salvando regras no banco...")
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text("💾 Salvando regras no banco de dados..."))
                self.page.snack_bar.open = True
                self.page.update()

            conn_str = f"postgresql+psycopg2://postgres:{senha}@192.168.0.200:5432/rec"
            atualizador = AtualizarRegras(conn_str=conn_str)

            atualizador.gerar_e_salvar(
                cross_obj=cross_obj,
                produtos=produtos,
                per_product_top_n=5,
                min_support=0.0001,
                min_confidence=0.015,
                min_lift=1.0,
                min_freq=2,
                replace_existing=True
            )

            # --- 5) Finalização
            print("✅ Atualização concluída com sucesso!")
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text("✅ Atualização concluída com sucesso!"))
                self.page.snack_bar.open = True
                self.page.update()

        except Exception as e:
            print("Erro durante atualização:", e)
            traceback.print_exc()
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"❌ Erro: {str(e)}"))
                self.page.snack_bar.open = True
                self.page.update()
        finally:
            # sempre reativa o botão correto e atualiza stats
            try:
                self.btn_atualizar.disabled = False
            except Exception:
                try:
                    self.atualizar_btn.disabled = False  # fallback antigo
                except Exception:
                    pass
            try:
                self.update()
            except Exception:
                pass
            try:
                self.refresh_stats()
            except Exception:
                pass

    # ---------------- utilitários ----------------
    def get_selected_files(self):
        return self.arquivo_estoque, self.arquivo_notas

    def liberar_controles(self):
        """
        Método adicionado para permitir a chamada externa sem gerar AttributeError.
        Habilita uploads e verifica botão de atualização.
        """
        self.senha_ok = True
        self.btn_upload_estoque.disabled = True
        self.btn_upload_notas.disabled = True
        self._verificar_pronto()
# DEBUGG
print("🚀 passou aqui!")