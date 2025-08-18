import pandas as pd
import time
from datetime import timedelta, datetime
from limpeza_estoque import EstoqueCleaner
from limpeza_notas import NotasCleaner
from limpeza_base_mesclada import BasePreparador
from substitutos import RecomendadorSubstituto
from recomendador import RecomendadorCrossSelling
from salva_banco import salvar_no_banco
import psycopg2
import asyncio


class AtualizadorBase:
    def __init__(
        self,
        caminho_estoque="bases/relatorio_produtos.xlsx",
        caminho_notas="bases/relatorio_notas.xlsx",
        log_callback=None,
        progresso_callback=None
    ):
        self.caminho_estoque = caminho_estoque
        self.caminho_notas = caminho_notas
        self.df_modelo = None
        self.log_callback = log_callback
        self.progresso_callback = progresso_callback

    @staticmethod
    def format_time(seconds):
        """Formata segundos em HH:MM:SS"""
        return str(timedelta(seconds=seconds))

    async def carregar_e_preparar_base(self, log_callback=None):
        """Carrega e limpa as bases de estoque e notas de forma assíncrona"""
        if log_callback:
            log_callback("Iniciando carregamento das bases...")

        # Carrega os DataFrames em threads separadas para não bloquear a UI
        loop = asyncio.get_event_loop()
        
        if log_callback:
            log_callback("Limpando base de estoque...")
        df_estoque = await loop.run_in_executor(
            None, 
            lambda: EstoqueCleaner().clean(pd.read_excel(self.caminho_estoque))
        )
        
        if log_callback:
            log_callback("Limpando base de notas...")
        df_notas = await loop.run_in_executor(
            None,
            lambda: NotasCleaner().clean(pd.read_excel(self.caminho_notas))
        )
        
        if log_callback:
            log_callback("Preparando base mesclada...")
        self.df_modelo = await loop.run_in_executor(
            None,
            lambda: BasePreparador().preparar_base(df_estoque, df_notas)
        )

    async def processar_produto(self, cod_produto):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._processar_produto_sincrono, cod_produto)

    def _processar_produto_sincrono(self, cod_produto):
        try:
            desc_produto = self.df_modelo.loc[
                self.df_modelo['Código produto'] == cod_produto, 'Descrição do produto'
            ].values[0]
        except IndexError:
            desc_produto = 'Descrição não encontrada'

        recomendador = RecomendadorSubstituto(self.df_modelo)
        resultado_sub = recomendador.recomendar(cod_produto)
        resultado_sub.insert(0, "Código pesquisado", cod_produto)
        resultado_sub.insert(1, "Descrição pesquisada", desc_produto)

        cross = RecomendadorCrossSelling(self.df_modelo)
        regras = cross.gerar_regras(cod_produto, min_support=0.0015, max_len=2)
        df_formatado = cross.formatar_regras(regras) if not regras.empty else pd.DataFrame()

        return resultado_sub, df_formatado

    async def atualizar_base(
        self, 
        intervalo_codigos=(0, 100),
        progresso_callback=None,
        log_callback=None
    ):
        # Armazena os callbacks para uso interno
        self.progresso_callback = progresso_callback
        self.log_callback = log_callback

        start_time = time.time()

        if self.log_callback:
            self.log_callback("Iniciando processamento...")

        # Carrega e prepara a base de forma assíncrona, passando o log_callback
        await self.carregar_e_preparar_base(log_callback=self.log_callback)

        codigos_unicos = self.df_modelo['Código produto'].unique()[intervalo_codigos[0]:intervalo_codigos[1]]
        total_produtos = len(codigos_unicos)
        
        if self.log_callback:
            self.log_callback(f"Processando {total_produtos} produtos...")

        # Processa cada produto
        for i, cod_produto in enumerate(codigos_unicos, 1):
            try:
                resultado_sub, df_formatado = await self.processar_produto(cod_produto)
                
                # Salva no banco em executor/thread separada
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None, 
                    lambda: salvar_no_banco(resultado_sub, df_formatado, self.df_modelo)
                )

                # Atualiza barra de progresso
                if self.progresso_callback:
                    self.progresso_callback(i, total_produtos)
                    await asyncio.sleep(0)  # permite UI processar

            except Exception as e:
                if self.log_callback:
                    self.log_callback(f"Erro no produto {cod_produto}: {str(e)}")
                continue

        total_time = time.time() - start_time
        if self.log_callback:
            data_atual = datetime.now().strftime("%d/%m/%Y")
            self.log_callback(f"Base atualizada em {data_atual} - {self.format_time(total_time)}.")
