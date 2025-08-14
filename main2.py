import pandas as pd
import time
from datetime import timedelta, datetime
from limpeza_estoque import EstoqueCleaner
from limpeza_notas import NotasCleaner
from limpeza_base_mesclada import BasePreparador
from substitutos import RecomendadorSubstituto
from recomendador import RecomendadorCrossSelling
from salva_banco import salvar_consolidado, salvar_no_banco
import psycopg2
import gc


class AtualizadorBase:
    def __init__(self, caminho_estoque="bases/relatorio_produtos.xlsx",
                 caminho_notas="bases/relatorio_notas.xlsx"):
        self.caminho_estoque = caminho_estoque
        self.caminho_notas = caminho_notas

    @staticmethod
    def format_time(seconds):
        return str(timedelta(seconds=seconds))

    def carregar_base(self):
        """Carrega e limpa as bases de estoque e notas"""
        print("Carregando e limpando dados...")
        df_estoque = EstoqueCleaner().clean(pd.read_excel(self.caminho_estoque))
        df_notas = NotasCleaner().clean(pd.read_excel(self.caminho_notas))
        df_modelo = BasePreparador().preparar_base(df_estoque, df_notas)
        return df_modelo

    def processar_produto(self, df_modelo, cod_produto):
        """Processa um único produto e retorna os DataFrames de substitutos e associados"""
        try:
            desc_produto = df_modelo.loc[
                df_modelo['Código produto'] == cod_produto, 'Descrição do produto'
            ].values[0]
        except IndexError:
            desc_produto = 'Descrição não encontrada'

        # Substitutos
        recomendador = RecomendadorSubstituto(df_modelo)
        resultado_sub = recomendador.recomendar(cod_produto)
        resultado_sub.insert(0, "Código pesquisado", cod_produto)
        resultado_sub.insert(1, "Descrição pesquisada", desc_produto)

        # Cross-selling
        cross = RecomendadorCrossSelling(df_modelo)
        regras = cross.gerar_regras(cod_produto, min_support=0.0015, max_len=2)
        df_formatado = cross.formatar_regras(regras) if not regras.empty else pd.DataFrame()

        return resultado_sub, df_formatado

    def atualizar_base(self, intervalo_codigos=(0, 10), progresso_callback=None, log_callback=None):
        start_time = time.time()

        if log_callback:
            log_callback("Iniciando processamento...")

        # Conexão com banco
        conn = psycopg2.connect(
            host="localhost",
            dbname="bd_recomenda",
            user="postgres",
            password="recomenda",
            port=5432
        )

        # Etapa 1: carregar e preparar base consolidada
        if log_callback:
            log_callback("Carregando e limpando bases...")
        df_modelo = self.carregar_base()

        # Etapa 2: salvar base consolidada no banco
        if log_callback:
            log_callback("Salvando base consolidada no banco...")
        salvar_consolidado(df_modelo, conn)

        # Liberar df_modelo da memória se for muito grande
        gc.collect()

        # Etapa 3: processar cada produto do intervalo
        codigos_unicos = df_modelo['Código produto'].unique()[intervalo_codigos[0]:intervalo_codigos[1]]
        total_produtos = len(codigos_unicos)

        if log_callback:
            log_callback(f"Processando {total_produtos} produtos para recomendações...")

        for i, cod_produto in enumerate(codigos_unicos, 1):
            try:
                resultado_sub, df_formatado = self.processar_produto(df_modelo, cod_produto)
                salvar_no_banco(conn, cod_produto, resultado_sub, df_formatado)

                # Liberar memória
                del resultado_sub, df_formatado
                gc.collect()

                if progresso_callback:
                    progresso_callback(i, total_produtos)

            except Exception as e:
                if log_callback:
                    log_callback(f"{i}/{total_produtos} | Erro: {str(e)}")
                continue

        conn.close()
        total_time = time.time() - start_time
        if log_callback:
            data_atual = datetime.now().strftime("%d/%m/%Y")
            log_callback(f"Base atualizada em {data_atual} - {self.format_time(total_time)}.")
