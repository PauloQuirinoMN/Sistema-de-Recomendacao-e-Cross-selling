import pandas as pd
from datetime import timedelta, datetime
from limpeza_estoque import EstoqueCleaner
from limpeza_notas import NotasCleaner
from limpeza_base_mesclada import BasePreparador
from substitutos import RecomendadorSubstituto
from recomendador import RecomendadorCrossSelling
from salva_banco import salvar_no_banco
import asyncio


class AtualizadorBase:
    def __init__(
        self,
        caminho_estoque="bases/relatorio_produtos.xlsx",
        caminho_notas="bases/relatorio_notas.xlsx",
        log_callback=None,
        progresso_callback=None,
        fim_callback=None
    ):
        self.caminho_estoque = caminho_estoque
        self.caminho_notas = caminho_notas
        self.df_modelo = None
        self.log_callback = log_callback
        self.progresso_callback = progresso_callback
        self.fim_callback = fim_callback

    @staticmethod
    def format_time(seconds):
        """Formata segundos em HH:MM:SS"""
        return str(timedelta(seconds=seconds))

    async def carregar_e_preparar_base(self, log_callback=None):
        """Carrega e limpa as bases de estoque e notas de forma assíncrona"""
        if log_callback:
            log_callback("Iniciando carregamento das bases...")

        loop = asyncio.get_event_loop()

        # Limpa base de estoque
        if log_callback:
            log_callback("Limpando base de estoque...")
        df_estoque = await loop.run_in_executor(
            None,
            lambda: EstoqueCleaner().clean(pd.read_excel(self.caminho_estoque))
        )

        # Limpa base de notas
        if log_callback:
            log_callback("Limpando base de notas...")
        df_notas = await loop.run_in_executor(
            None,
            lambda: NotasCleaner().clean(pd.read_excel(self.caminho_notas))
        )

        # Prepara base mesclada
        if log_callback:
            log_callback("Preparando base mesclada...")
        self.df_modelo = await loop.run_in_executor(
            None,
            lambda: BasePreparador().preparar_base(df_estoque, df_notas)
        )

    async def processar_produto(self, cod_produto):
        """Processa um produto de forma assíncrona"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._processar_produto_sincrono, cod_produto)

    def _processar_produto_sincrono(self, cod_produto):
        """Processamento síncrono de um produto"""
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

        # Cross-selling
        cross = RecomendadorCrossSelling(self.df_modelo)
        regras = cross.gerar_regras(cod_produto, min_support=0.0015, max_len=2)
        df_formatado = cross.formatar_regras(regras) if not regras.empty else pd.DataFrame()

        return resultado_sub, df_formatado

    async def atualizar_base(
        self,
        intervalo_codigos=(0, 100),
        progresso_callback=None,
        log_callback=None,
        fim_callback=None
    ):
        """Atualiza toda a base de produtos, calculando substitutos e cross-selling"""
        # Armazena callbacks
        self.progresso_callback = progresso_callback
        self.log_callback = log_callback
        self.fim_callback = fim_callback

        if self.log_callback:
            self.log_callback("Iniciando processamento...")

        # Carrega e prepara base
        await self.carregar_e_preparar_base(log_callback=self.log_callback)

        codigos_unicos = self.df_modelo['Código produto'].unique()[intervalo_codigos[0]:intervalo_codigos[1]]
        total_produtos = len(codigos_unicos)

        if self.log_callback:
            self.log_callback(f"Processando {total_produtos} produtos...")

        # Processa cada produto
        for i, cod_produto in enumerate(codigos_unicos, 1):
            try:
                resultado_sub, df_formatado = await self.processar_produto(cod_produto)

                # Salva no banco
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    lambda: salvar_no_banco(resultado_sub, df_formatado, self.df_modelo)
                )

                # Atualiza progresso
                if self.progresso_callback:
                    self.progresso_callback(i, total_produtos)
                    await asyncio.sleep(0)  # permite UI processar

            except Exception as e:
                if self.log_callback:
                    self.log_callback(f"Erro no produto {cod_produto}: {str(e)}")
                continue

        # Finaliza e atualiza logs
        if self.fim_callback:
            data_atual = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
            qtd_itens = total_produtos
            self.fim_callback(data_atual, qtd_itens)

        if self.log_callback:
            self.log_callback(f"Última Atualização em {data_atual} - {qtd_itens} itens")

            # Salva última atualização em arquivo
            with open("ultima_atualizacao.txt", "w", encoding="utf-8") as f:
                f.write(f"Última Atualização em {data_atual} - {qtd_itens} itens")
