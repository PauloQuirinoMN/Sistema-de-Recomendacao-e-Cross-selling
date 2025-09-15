"""
Refatoração de atualizar.py
- Mantive as assinaturas públicas e os nomes dos métodos principais da classe `AtualizacaoComponent`.
- Separei responsabilidades em 3 helpers internos (PasswordController, FileHandler, WorkerCoordinator) para:
    * isolar lógica de senha
    * isolar manipulação/validação de arquivos
    * coordenar o pipeline de processamento (worker)

Objetivo: melhorar legibilidade e facilitar testes sem mudar a API usada externamente.
"""

import os
import shutil
import time
import threading
from typing import Optional

import flet as ft
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Componentes externos 
from atualizador_regras import AtualizarRegras
from associados import CrossSellingSimples
from capturar_log import LogCapture

# ------------------------ Helpers internos ------------------------
class _PasswordController:
    """Controla o comportamento do campo de senha e habilita/desabilita controles.

    Recebe a instância do componente e age sobre seus elementos UI já existentes.
    """

    def __init__(self, parent):
        self.parent = parent

    def toggle(self):
        show = not self.parent.password_row.visible
        self.parent.password_row.visible = show
        self.parent.pwd_field.visible = show
        self.parent.btn_confirm_pwd.visible = show
        self.parent.btn_cancel_pwd.visible = show
        if show:
            self.parent.pwd_field.value = ""
            self.parent.pwd_field.error_text = None
        self.parent.update()

    def confirm(self, e=None):
        val = (self.parent.pwd_field.value or "").strip()
        if val == "123ja":
            self.parent.senha_ok = True
            self.parent.btn_upload_estoque.disabled = False
            self.parent.btn_upload_notas.disabled = False
            # esconde a senha
            self.parent.password_row.visible = False
            self.parent.pwd_field.visible = False
            self.parent.btn_confirm_pwd.visible = False
            self.parent.btn_cancel_pwd.visible = False
            self.parent._verificar_pronto()
        else:
            self.parent.pwd_field.error_text = "Senha incorreta"
        self.parent.update()

    def cancel(self, e=None):
        self.parent.password_row.visible = False
        self.parent.pwd_field.visible = False
        self.parent.btn_confirm_pwd.visible = False
        self.parent.btn_cancel_pwd.visible = False
        self.parent.pwd_field.value = ""
        self.parent.pwd_field.error_text = None
        self.parent.update()


class _FileHandler:
    """Gerencia FilePickers, seleção de arquivos e cópia para a pasta `bases`.

    - Mantém os handlers com as mesmas assinaturas presentes no componente.
    - Atualiza labels e atributos (arquivo_estoque, arquivo_notas) do componente.
    """

    def __init__(self, parent):
        self.parent = parent

    def attach_to_page(self, page: ft.Page):
        # Anexa filepickers ao page.overlay
        if self.parent.file_picker_estoque not in page.overlay:
            page.overlay.append(self.parent.file_picker_estoque)
        if self.parent.file_picker_notas not in page.overlay:
            page.overlay.append(self.parent.file_picker_notas)
        self.parent._filepickers_attached = True
        self.parent.page = page
        try:
            self.parent.refresh_stats()
        finally:
            self.parent.update()

    def pick_estoque(self, e: Optional[ft.ControlEvent] = None):
        page = self.parent._get_page(e)
        if not self.parent.senha_ok:
            self.parent._toggle_password_row()
            return
        if page and not self.parent._filepickers_attached:
            try:
                self.attach_to_page(page)
            except Exception:
                pass
        try:
            self.parent.file_picker_estoque.pick_files(allow_multiple=False)
        except Exception:
            if page:
                page.pick_files(allow_multiple=False, on_result=self.parent._on_estoque_result)

    def pick_notas(self, e: Optional[ft.ControlEvent] = None):
        page = self.parent._get_page(e)
        if not self.parent.senha_ok:
            self.parent._toggle_password_row()
            return
        if page and not self.parent._filepickers_attached:
            try:
                self.attach_to_page(page)
            except Exception:
                pass
        try:
            self.parent.file_picker_notas.pick_files(allow_multiple=False)
        except Exception:
            if page:
                page.pick_files(allow_multiple=False, on_result=self.parent._on_notas_result)

    def on_estoque_result(self, ev: ft.FilePickerResultEvent):
        if ev.files and len(ev.files) > 0:
            f = ev.files[0]
            path = getattr(f, "path", None) or getattr(f, "name", None)
            self.parent.arquivo_estoque = path
            self.parent.label_arquivo_estoque.value = getattr(f, "name", path)
        else:
            self.parent.arquivo_estoque = None
            self.parent.label_arquivo_estoque.value = "Nenhum arquivo"
        self.parent._verificar_pronto()
        self.parent.update()

    def on_notas_result(self, ev: ft.FilePickerResultEvent):
        if ev.files and len(ev.files) > 0:
            f = ev.files[0]
            path = getattr(f, "path", None) or getattr(f, "name", None)
            self.parent.arquivo_notas = path
            self.parent.label_arquivo_notas.value = getattr(f, "name", path)
        else:
            self.parent.arquivo_notas = None
            self.parent.label_arquivo_notas.value = "Nenhum arquivo"
        self.parent._verificar_pronto()
        self.parent.update()

    def copy_to_bases(self, src_estoque: str, src_notas: str) -> tuple[str, str]:
        bases = os.path.join(os.getcwd(), "bases")
        os.makedirs(bases, exist_ok=True)
        dst_estoque = os.path.join(bases, "relatorio_produtos.xlsx")
        dst_notas = os.path.join(bases, "relatorio_notas.xlsx")
        shutil.copy2(src_estoque, dst_estoque)
        shutil.copy2(src_notas, dst_notas)
        return dst_estoque, dst_notas


class _WorkerCoordinator:
    """Coordena o pipeline (leitura, limpeza, geração de regras e persistência).

    Mantém o comportamento original do `_worker` mas isolado para facilitar testes.
    """

    def __init__(self, parent):
        self.parent = parent

    @staticmethod
    def _extrair_lista_produtos(df):
        candidatos = [
            "codigo_produto", "codigo produto", "codigo", "Código produto",
            "Codigo produto", "Codigo", "cod_produto", "cod_prod"
        ]
        for c in candidatos:
            if c in df.columns:
                return list(df[c].dropna().unique())
        for c in df.columns:
            if df[c].dtype.kind in ("i", "u") and df[c].nunique() > 0:
                return list(df[c].dropna().unique())
        raise KeyError(f"Nenhuma coluna de código produto encontrada. Colunas: {df.columns.tolist()}")

    def run(self, senha: str, dst_estoque: str, dst_notas: str):
        import traceback
        try:
            # --- 1) Lendo arquivos
            self.parent.logger.log("📂 Lendo arquivos Excel...")
            df_produtos_raw = pd.read_excel(dst_estoque, engine="openpyxl")
            df_notas_raw = pd.read_excel(dst_notas, engine="openpyxl")

            # --- 2) Limpeza / Normalização
            self.parent.logger.log  ("🧹 Limpando e preparando dados...")
            from limpeza_estoque import EstoqueCleaner
            from limpeza_notas import NotasCleaner
            from consolidar import ConsolidadoNormalizer  

            estoque_cleaner = EstoqueCleaner(logger=self.parent.logger)
            df_produtos = estoque_cleaner.clean(df_produtos_raw)

            notas_cleaner = NotasCleaner(logger=self.parent.logger)
            df_notas = notas_cleaner.clean(df_notas_raw)

            # --- 2.1) Normalizador Consolidado
            conn_str = f"postgresql+psycopg2://postgres:{senha}@192.168.0.200:5432/rec"
            self.parent.logger.log("📊 Criando tabelas normalizadas e salvando dados...")
            normalizador = ConsolidadoNormalizer(conn_str=conn_str, logger=self.parent.logger)
            normalizador.processar(df_estoque=df_produtos, df_notas=df_notas)

            # --- 3) Gerar cross-selling
            self.parent.logger.log("🔗 Gerando regras de associação...")
            cross_obj = CrossSellingSimples(df_notas=df_notas, df_produtos=df_produtos, logger=self.parent.logger)
            produtos = self._extrair_lista_produtos(df_produtos)

            # --- 4) Atualizar no banco (regras)
            self.parent.logger.log("💾 Salvando regras no banco de dados...")
            atualizador = AtualizarRegras(conn_str=conn_str, logger=self.parent.logger)
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
            self.parent.logger.log("✅ Atualização concluída com sucesso!")

        except Exception as e:
            print("Erro durante atualização:", e)
            traceback.print_exc()
            self.parent.logger.log(f"❌ Erro: {str(e)}")
        finally:
            # sempre reativa o botão correto e atualiza stats
            try:
                self.parent.btn_atualizar.disabled = False
            except Exception:
                try:
                    self.parent.atualizar_btn.disabled = False
                except Exception:
                    pass
            try:
                self.parent.update()
            except Exception:
                pass
            try:
                self.parent.refresh_stats()
            except Exception:
                pass


# ------------------------ Componente principal (API mantida) ------------------------
class AtualizacaoComponent(ft.Column):
    """
    Componente para controlar atualização (upload .xlsx + executar AtualizarRegras).
    Uso:
        comp = AtualizacaoComponent(conn_str, page)
        page.add(comp).
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

        self.logger = LogCapture(ui_callback=self.update_last_log)

        # estado
        self.arquivo_estoque: Optional[str] = None
        self.arquivo_notas: Optional[str] = None
        self.senha_ok: bool = False
        self._filepickers_attached = False

        # labels e elementos UI
        self.txt_ultima = ft.Text("Última atualização: —", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK54)
        self.txt_produtos = ft.Text("0", size=18, weight=ft.FontWeight.BOLD)
        self.txt_associados = ft.Text("0", size=18, weight=ft.FontWeight.BOLD)

        self.label_arquivo_estoque = ft.Text("Estoque/Produtos", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800)
        self.label_arquivo_notas = ft.Text("Notas/Vendas", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800)

        # botões principais
        self.btn_liberar = ft.TextButton("Liberar", on_click=lambda e: self._toggle_password_row())
        self.btn_upload_estoque = ft.IconButton(
            icon=ft.Icons.UPLOAD_FILE,
            tooltip="COLUNAS OBRIGATÓRIAS:\n"
                        "•	codigo_produto → identificador único do produto\n"
                        "•	descricao_produto → nome/descrição do produto\n"
                        "•	preco_custo → custo unitário\n"
                         "•	quantidade_estoque → quantidade disponível em estoque\n",
            disabled=True,
            on_click=lambda e: self.pick_estoque(e),
        )
        
        self.btn_upload_notas = ft.IconButton(
            icon=ft.Icons.UPLOAD_FILE,
            tooltip="COLUNAS OBRIGATÓRIAS:\n"
                    "•	numero_nota_fiscal → número da nota fiscal\n"
                    "•	codigo_produto → identificador do produto\n"
                    "•	descricao_produto → descrição/nome do produto\n"
                    "•	quantidade_produto → quantidade vendida\n"
                    "•	valor_unitario → preço unitário\n"
                    "•	preco_custo → custo do produto\n",
            disabled=True,
            on_click=lambda e: self.pick_notas(e),
        )
        self.btn_atualizar = ft.TextButton("Atualizar", disabled=True, on_click=lambda e: self.on_click_atualizar(e))

        # campo de senha inline (inicialmente escondido)
        self.pwd_field = ft.TextField(password=True, width=360, height=100, visible=False, autofocus=True, on_submit=lambda ev: self._confirm_password(ev))
        self.btn_confirm_pwd = ft.TextButton("Confirmar", visible=False, on_click=lambda e: self._confirm_password(e))
        self.btn_cancel_pwd = ft.TextButton("Cancelar", visible=False, on_click=lambda e: self._cancel_password(e))
        self.password_row = ft.Row(
            [
                self.pwd_field, 
                self.btn_confirm_pwd, 
                self.btn_cancel_pwd
            ],
            alignment=ft.MainAxisAlignment.CENTER, 
            vertical_alignment=ft.CrossAxisAlignment.START,
            spacing=5,
            visible=False,
        )

        # FilePickers (anexar depois via attach_to_page)
        self.file_picker_estoque = ft.FilePicker(on_result=self._on_estoque_result)
        self.file_picker_notas = ft.FilePicker(on_result=self._on_notas_result)

        # instanciar helpers passando self (não alteram interface pública)
        self._pwd_ctrl = _PasswordController(self)
        self._file_handler = _FileHandler(self)
        self._worker_coordinator = _WorkerCoordinator(self)

        self.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            [
                                ft.Text("Última atualização", weight=ft.FontWeight.BOLD),
                                ft.Row([self.txt_ultima], expand=True)
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_AROUND),
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
                shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.BLUE_100, offset=ft.Offset(2, 2)),                
                expand=True,
                height=140,
                width=680,
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
    def update_last_log(self, message: str):
        # chamado automaticamente pelo logger
        self.txt_ultima.value = message
        self.page.update()

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
                        ts = r.strftime("%d/%m/%Y  %H:%M:%S")
                    except Exception:
                        ts = str(r)
                        ts = ft.TextStyle(size=20)
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
        self._pwd_ctrl.toggle()

    def _confirm_password(self, e=None):
        self._pwd_ctrl.confirm(e)

    def _cancel_password(self, e=None):
        self._pwd_ctrl.cancel(e)

    # ---------------- file pickers (delegado) ----------------
    def pick_estoque(self, e: Optional[ft.ControlEvent] = None):
        self._file_handler.pick_estoque(e)

    def pick_notas(self, e: Optional[ft.ControlEvent] = None):
        self._file_handler.pick_notas(e)

    def _on_estoque_result(self, ev: ft.FilePickerResultEvent):
        self._file_handler.on_estoque_result(ev)

    def _on_notas_result(self, ev: ft.FilePickerResultEvent):
        self._file_handler.on_notas_result(ev)

    def _verificar_pronto(self):
        self.btn_atualizar.disabled = not (self.senha_ok and self.arquivo_estoque and self.arquivo_notas)
        self.update()

    # ---------------- executar atualização ----------------
    def on_click_atualizar(self, e: Optional[ft.ControlEvent] = None):
        page = self._get_page(e)
        if not self.senha_ok:
            self._toggle_password_row()
            return

        if not (self.arquivo_estoque and self.arquivo_notas):
            self.logger.log("Selecione estoque e notas antes de atualizar.")
            return

        # copia arquivos para a pasta bases usando o FileHandler
        try:
            dst_estoque, dst_notas = self._file_handler.copy_to_bases(self.arquivo_estoque, self.arquivo_notas)
        except Exception as ex:
            self.logger.log(f"Erro ao copiar arquivos: {ex}")
            return

        # desabilita botão até terminar
        self.btn_atualizar.disabled = True
        self.update()

        # executa em thread separada para não travar UI
        senha = "dev2025"  # ⚠️ futuramente uma parametrização segura
        threading.Thread(
            target=self._worker,
            args=(senha, dst_estoque, dst_notas),
            daemon=True
        ).start()

    # ---------------- worker ----------------
    def _worker(self, senha: str, dst_estoque: str, dst_notas: str):
        # Exibe mensagem inicial no logger
        texto = ft.Text("Aguarde um Instante...", size=20, weight=ft.FontWeight.BOLD)
        self.logger.log(texto.value)

        try:
            # roda o processamento pesado delegando ao coordenador
            self._worker_coordinator.run(senha, dst_estoque, dst_notas)
        except Exception as e:
            print("Erro no worker delegador:", e)
        finally:
            # Após processamento, desabilita todos os botões exceto "Liberar"
            self.liberar_controles()
            if hasattr(self, "atualizar_conexao"):
                self.atualizar_conexao()
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
        Apenas mantém o botão de liberar disponível após o processamento.
        Usuário precisa fornecer a senha para nova atualização.
        """
        self.senha_ok = False  # garante que a senha seja solicitada
        self.btn_upload_estoque.disabled = True
        self.btn_upload_notas.disabled = True
        self.btn_atualizar.disabled = True  # botão de atualizar também fica desabilitado
        self.update()


