# atualizar.py
import os
import shutil
import threading
import flet as ft
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from atualizador_regras import AtualizarRegras  # sua classe


class AtualizacaoComponent(ft.Column):
    """
    Componente Flet que mostra última atualização, contadores e controles
    para carregar arquivos (.xlsx) de estoque e notas e executar AtualizarRegras.
    """

    def __init__(self, conn_str: str):
        super().__init__()
        self.conn_str = conn_str
        try:
            self.engine = create_engine(conn_str)
        except Exception:
            self.engine = None

        self.arquivo_estoque: Optional[str] = None
        self.arquivo_notas: Optional[str] = None
        self.senha_ok = False

        self.txt_ultima = ft.Text("Última atualização: —", size=12)
        self.txt_produtos = ft.Text("0", size=18, weight=ft.FontWeight.BOLD)
        self.txt_associados = ft.Text("0", size=18, weight=ft.FontWeight.BOLD)

        self.label_arquivo_estoque = ft.Text("Nenhum arquivo", size=12)
        self.label_arquivo_notas = ft.Text("Nenhum arquivo", size=12)

        self.btn_liberar = ft.TextButton("Liberar", on_click=self.liberar_controles)
        self.btn_upload_estoque = ft.IconButton(
            icon=ft.icons.UPLOAD_FILE,
            tooltip="Carregar .xlsx (estoque)",
            disabled=True,
            on_click=self.pick_estoque
        )
        self.btn_upload_notas = ft.IconButton(
            icon=ft.icons.UPLOAD_FILE,
            tooltip="Carregar .xlsx (notas)",
            disabled=True,
            on_click=self.pick_notas
        )
        self.btn_atualizar = ft.TextButton("Atualizar", disabled=True, on_click=self.on_click_atualizar)

        self.file_picker_estoque = ft.FilePicker(on_result=self._on_estoque_result)
        self.file_picker_notas = ft.FilePicker(on_result=self._on_notas_result)

        controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Última atualização", weight=ft.FontWeight.BOLD),
                        ft.Row([self.txt_ultima], alignment=ft.MainAxisAlignment.CENTER),
                        ft.Divider(height=6),
                        ft.Row(
                            controls=[
                                ft.Column([self.txt_produtos, ft.Text("Produtos")], alignment=ft.MainAxisAlignment.CENTER),
                                ft.Column([self.txt_associados, ft.Text("Produtos associados")], alignment=ft.MainAxisAlignment.CENTER),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Divider(height=8),
                        ft.Row(
                            controls=[
                                ft.Column([self.btn_upload_estoque, self.label_arquivo_estoque], alignment=ft.MainAxisAlignment.CENTER),
                                ft.Column([self.btn_upload_notas, self.label_arquivo_notas], alignment=ft.MainAxisAlignment.CENTER),
                                ft.Column([self.btn_liberar, self.btn_atualizar], alignment=ft.MainAxisAlignment.CENTER)
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                            spacing=12,
                        ),
                    ],
                    spacing=8,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.padding.symmetric(vertical=12, horizontal=12),
                bgcolor=ft.Colors.WHITE,
                border=ft.border.all(1, ft.Colors.BLACK12),
                border_radius=8,
                width=460
            )
        ]

        self.controls = controls

        try:
            self.refresh_stats()
        except Exception:
            pass

    # ---------------- DB / stats ----------------
    def refresh_stats(self):
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
        cnt_produtos_sql = text("SELECT COUNT(*) FROM produtos;")
        cnt_associados_sql = text("SELECT COUNT(DISTINCT consequente_id) FROM metricas;")

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

    # ---------------- password / unlock ----------------
    def liberar_controles(self, e=None):
        """Abre diálogo de senha; se correta (1234) libera uploads."""
        pwd = ft.TextField(password=True, autofocus=True, width=240)

        def submit_pwd(evt=None):
            val = (pwd.value or "").strip()
            if val == "1234":
                self.senha_ok = True
                self.btn_upload_estoque.disabled = False
                self.btn_upload_notas.disabled = False
                dlg.open = False
                self.page.update()
                self.update()
            else:
                pwd.error_text = "Senha incorreta"
                self.page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Autenticação"),
            content=ft.Column([ft.Text("Informe a senha para habilitar os controles:"), pwd]),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._close_dialog(e, None)),
                ft.TextButton("OK", on_click=submit_pwd),
            ],
            modal=True
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def _close_dialog(self, e, dlg):
        try:
            dlg.open = False
        except Exception:
            pass
        self.page.update()

    # ---------------- file pickers ----------------
    def pick_estoque(self, e):
        if not self.senha_ok:
            self.liberar_controles()
            return
        self.file_picker_estoque.pick_files(allow_multiple=False)

    def pick_notas(self, e):
        if not self.senha_ok:
            self.liberar_controles()
            return
        self.file_picker_notas.pick_files(allow_multiple=False)

    def _on_estoque_result(self, ev: ft.FilePickerResultEvent):
        if ev.files and len(ev.files) > 0:
            f = ev.files[0]
            path = getattr(f, "path", None) or getattr(f, "name", None)
            self.arquivo_estoque = path
            self.label_arquivo_estoque.value = getattr(f, "name", path)
        else:
            self.arquivo_estoque = None
            self.label_arquivo_estoque.value = "Nenhum arquivo"
        self.update()
        self._verificar_pronto()

    def _on_notas_result(self, ev: ft.FilePickerResultEvent):
        if ev.files and len(ev.files) > 0:
            f = ev.files[0]
            path = getattr(f, "path", None) or getattr(f, "name", None)
            self.arquivo_notas = path
            self.label_arquivo_notas.value = getattr(f, "name", path)
        else:
            self.arquivo_notas = None
            self.label_arquivo_notas.value = "Nenhum arquivo"
        self.update()
        self._verificar_pronto()

    def _verificar_pronto(self):
        if self.senha_ok and self.arquivo_estoque and self.arquivo_notas:
            self.btn_atualizar.disabled = False
        else:
            self.btn_atualizar.disabled = True
        self.update()

    # ---------------- executar atualização ----------------
    def on_click_atualizar(self, e):
        if not self.senha_ok:
            self.liberar_controles()
            return

        if not (self.arquivo_estoque and self.arquivo_notas):
            self.page.snack_bar = ft.SnackBar(ft.Text("Selecione estoque e notas antes de atualizar."))
            self.page.snack_bar.open = True
            self.page.update()
            return

        bases_dir = os.path.join(os.getcwd(), "bases")
        os.makedirs(bases_dir, exist_ok=True)
        dst_estoque = os.path.join(bases_dir, "relatorio_produtos.xlsx")
        dst_notas = os.path.join(bases_dir, "relatorio_notas.xlsx")

        try:
            shutil.copy2(self.arquivo_estoque, dst_estoque)
            shutil.copy2(self.arquivo_notas, dst_notas)
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao copiar arquivos: {ex}"))
            self.page.snack_bar.open = True
            self.page.update()
            return

        def _worker():
            try:
                self.page.snack_bar = ft.SnackBar(ft.Text("Atualização iniciada..."))
                self.page.snack_bar.open = True
                self.page.update()

                atualizador = AtualizarRegras(conn_str=self.conn_str)
                try:
                    atualizador.gerar_e_salvar()
                except TypeError:
                    try:
                        atualizador.gerar_e_salvar(self)
                    except Exception:
                        pass

                self.page.snack_bar = ft.SnackBar(ft.Text("Atualização finalizada."))
                self.page.snack_bar.open = True
            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Erro na atualização: {ex}"))
                self.page.snack_bar.open = True
            finally:
                try:
                    self.refresh_stats()
                except Exception:
                    pass
                self.page.update()

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def get_selected_files(self):
        return self.arquivo_estoque, self.arquivo_notas
