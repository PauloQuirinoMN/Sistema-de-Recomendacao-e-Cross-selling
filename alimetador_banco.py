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

    def atualizar_base(self, intervalo_codigos=(0, 100)):
        """Executa o processo completo de atualização da base"""
        start_time = time.time()
        print("Iniciando processamento...")

        # 1. Carrega e prepara base
        self.carregar_e_preparar_base()

        # 2. Seleciona faixa de produtos para processar
        codigos_unicos = self.df_modelo['Código produto'].unique()[intervalo_codigos[0]:intervalo_codigos[1]]
        total_produtos = len(codigos_unicos)
        produtos_processados = 0
        print(f"\nProcessando {total_produtos} produtos...")

        # 3. Processa cada produto
        for i, cod_produto in enumerate(codigos_unicos, 1):
            produto_start = time.time()
            try:
                resultado_sub, df_formatado = self.processar_produto(cod_produto)
                salvar_no_banco(resultado_sub, df_formatado, self.df_modelo)
                produtos_processados += 1
                tempo_produto = time.time() - produto_start
                horario = datetime.now().strftime("%H:%M:%S")
                print(f"{i}/{total_produtos} | Cód: {cod_produto} | Tempo: {tempo_produto:.1f}s | Horário: {horario}")
            except Exception as e:
                print(f"{i}/{total_produtos} | Cód: {cod_produto} | Erro: {str(e)}")
                continue
        

        # 4. Relatório final
        total_time = time.time() - start_time
        print(f"\nProcesso concluído!")
        print(f"Tempo total: {self.format_time(total_time)}")
        print(f"Média por produto: {total_time / total_produtos:.1f}s")

