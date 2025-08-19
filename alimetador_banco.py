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


class AtualizadorBase:
    def __init__(self, caminho_estoque="bases/relatorio_produtos.xlsx", caminho_notas="bases/relatorio_notas.xlsx"):
        self.caminho_estoque = caminho_estoque
        self.caminho_notas = caminho_notas
        self.df_modelo = None

    @staticmethod
    def format_time(seconds):
        """Formata segundos em HH:MM:SS"""
        return str(timedelta(seconds=seconds))

    def carregar_e_preparar_base(self):
        """Carrega e limpa as bases de estoque e notas, depois prepara a base unificada"""
        print("Carregando e limpando dados...")
        df_estoque = EstoqueCleaner().clean(pd.read_excel(self.caminho_estoque))
        df_notas = NotasCleaner().clean(pd.read_excel(self.caminho_notas))
        self.df_modelo = BasePreparador().preparar_base(df_estoque, df_notas)

    def processar_produto(self, cod_produto):
        """Processa um único produto e retorna os DataFrames de substitutos e associados"""
        try:
            desc_produto = self.df_modelo.loc[
                self.df_modelo['Código produto'] == cod_produto, 'Descrição do produto'
            ].values[0]
        except IndexError:
            desc_produto = 'Descrição não encontrada'

        # Recomendação de Substitutos
        recomendador = RecomendadorSubstituto(self.df_modelo)
        resultado_sub = recomendador.recomendar(cod_produto)
        resultado_sub.insert(0, "Código pesquisado", cod_produto)
        resultado_sub.insert(1, "Descrição pesquisada", desc_produto)

        # Recomendação por Cross-Selling
        cross = RecomendadorCrossSelling(self.df_modelo)
        regras = cross.gerar_regras(cod_produto, min_support=0.0015, max_len=2)
        df_formatado = cross.formatar_regras(regras) if not regras.empty else pd.DataFrame()

        return resultado_sub, df_formatado

    def atualizar_base(self, intervalo_codigos=(400, 410), progresso_callback=None, log_callback=None):
        start_time = time.time()

        if log_callback:
            log_callback("Iniciando processamento...")

        # Carrega e prepara base
        if log_callback:
            log_callback("Carregando e limpando dados...")

        if log_callback:
            log_callback("Iniciando limpeza da base de estoque...")
        df_estoque = EstoqueCleaner().clean(pd.read_excel(self.caminho_estoque))

        if log_callback:
            log_callback("Limpeza de estoque concluída.")

        if log_callback:
            log_callback("Iniciando limpeza da base de notas...")
        df_notas = NotasCleaner().clean(pd.read_excel(self.caminho_notas))

        if log_callback:
            log_callback("Limpeza de notas concluída.")

        self.df_modelo = BasePreparador().preparar_base(df_estoque, df_notas)


        # Agora que a limpeza acabou, começamos a barra de progresso
        codigos_unicos = self.df_modelo['Código produto'].unique()[intervalo_codigos[0]:intervalo_codigos[1]]
        total_produtos = len(codigos_unicos)



        if log_callback:
            log_callback(f"Processando {total_produtos} produtos...")



        if len(codigos_unicos) == 0:
            if log_callback:
                log_callback("Nenhum código encontrado para processar.")
            return

        for i, cod_produto in enumerate(codigos_unicos, 1):
            try:
                resultado_sub, df_formatado = self.processar_produto(cod_produto)
                salvar_no_banco(resultado_sub, df_formatado, self.df_modelo)

                if progresso_callback:
                    progresso_callback(i, total_produtos)

            except Exception as e:
                if log_callback:
                    log_callback(f"{i}/{total_produtos} | Erro: {str(e)}")
                continue


        total_time = time.time() - start_time
    # 🔹 Mensagem final
        if log_callback:
            data_atual = datetime.now().strftime("%d/%m/%Y")
            log_callback(f"Base atualizada em {data_atual} - {self.format_time(total_time)}.")
