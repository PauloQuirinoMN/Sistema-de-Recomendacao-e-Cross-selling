import pandas as pd
import time
import asyncio
from datetime import timedelta, datetime

from limpeza_estoque import EstoqueCleaner
from limpeza_notas import NotasCleaner
from limpeza_base_mesclada import BasePreparador
from substitutos import RecomendadorSubstituto
from recomendador import RecomendadorCrossSelling
from salva_banco import salvar_no_banco


class AtualizadorBase:
    """
    Responsável por carregar, preparar e atualizar a base de dados
    para o sistema de recomendação.
    """

    def __init__(
        self,
        caminho_estoque: str = "bases/relatorio_produtos.xlsx",
        caminho_notas: str = "bases/relatorio_notas.xlsx",
        log_callback=None,
        progresso_callback=None
    ):
        self.caminho_estoque = caminho_estoque
        self.caminho_notas = caminho_notas
        self.df_modelo = None
        self.log_callback = log_callback
        self.progresso_callback = progresso_callback

    # =====================
    # Utilidades
    # =====================
    @staticmethod
    def format_time(seconds: float) -> str:
        """Formata segundos em HH:MM:SS"""
        return str(timedelta(seconds=seconds))

    def _log(self, mensagem: str):
        """Envia log para callback, se existir"""
        if self.log_callback:
            self.log_callback(mensagem)

    # =====================
    # Carregamento de Bases
    # =====================
    async def carregar_e_preparar_base(self):
        """Carrega e limpa as bases de estoque e notas de forma assíncrona"""
        self._log("Iniciando carregamento das bases...")
        loop = asyncio.get_event_loop()

        self._log("🔄 Limpando base de estoque...")
        df_estoque = await loop.run_in_executor(
            None,
            lambda: EstoqueCleaner().clean(pd.read_excel(self.caminho_estoque))
        )

        self._log("🔄 Limpando base de notas...")
        df_notas = await loop.run_in_executor(
            None,
            lambda: NotasCleaner().clean(pd.read_excel(self.caminho_notas))
        )

        self._log("🔄 Preparando base mesclada...")
        self.df_modelo = await loop.run_in_executor(
            None,
            lambda: BasePreparador().preparar_base(df_estoque, df_notas)
        )

    # =====================
    # Processamento Produto
    # =====================
    async def processar_produto(self, cod_produto: int):
        """Processa substitutos e cross-selling de um produto específico"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._processar_produto_sincrono, cod_produto)

    def _processar_produto_sincrono(self, cod_produto: int):
        """Versão síncrona do processamento de produto"""
        try:
            desc_produto = self.df_modelo.loc[
                self.df_modelo['Código produto'] == cod_produto, 'Descrição do produto'
            ].values[0]
        except IndexError:
            desc_produto = 'Descrição não encontrada'

        # Substitutos
        recomendador = RecomendadorSubstituto(self.df_modelo)
        resultado_sub = recomendador.recomendar(cod_produto)
        resultado_sub.insert(0, "Código pesquisado", cod_produto)
        resultado_sub.insert(1, "Descrição pesquisada", desc_produto)

        # Cross-Selling
        cross = RecomendadorCrossSelling(self.df_modelo)
        regras = cross.gerar_regras(cod_produto, min_support=0.0015, max_len=2)
        df_formatado = cross.formatar_regras(regras) if not regras.empty else pd.DataFrame()

        return resultado_sub, df_formatado

    # =====================
    # Atualização Geral
    # =====================
    async def atualizar_base(
        self,
        intervalo_codigos: tuple = (0, 100),
    ):
        """Processa todos os produtos dentro do intervalo e atualiza a base no banco"""
        start_time = time.time()
        self._log("🚀 Iniciando processamento...")

        # Carrega e prepara a base
        await self.carregar_e_preparar_base()

        codigos_unicos = self.df_modelo['Código produto'].unique()[intervalo_codigos[0]:intervalo_codigos[1]]
        total_produtos = len(codigos_unicos)
        self._log(f"🔢 Processando {total_produtos} produtos...")

        loop = asyncio.get_event_loop()

        # Processa cada produto
        for i, cod_produto in enumerate(codigos_unicos, 1):
            try:
                resultado_sub, df_formatado = await self.processar_produto(cod_produto)

                # Salva no banco em executor separado
                await loop.run_in_executor(
                    None,
                    lambda: salvar_no_banco(resultado_sub, df_formatado, self.df_modelo)
                )

                # Atualiza progresso
                if self.progresso_callback:
                    self.progresso_callback(i, total_produtos)
                await asyncio.sleep(0)  # permite UI processar

            except Exception as e:
                self._log(f"❌ Erro no produto {cod_produto}: {str(e)}")
                continue

        # Finalização
        total_time = time.time() - start_time
        data_atual = datetime.now().strftime("%d/%m/%Y")
        self._log(f"✅ Base atualizada em {data_atual} - {self.format_time(total_time)}.")
        await asyncio.sleep(0)
