import psycopg2
from psycopg2 import sql
import pandas as pd

class InserirDados:
    def __init__(self, db_config):
        """Configuração básica da conexão"""
        self.conn = None
        self.db_config = db_config
    
    def conectar(self):
        """Estabelece conexão com o banco"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            print("Conexão estabelecida!")
            return True
        except Exception as e:
            print(f"Erro ao conectar: {e}")
            return False
    
    def desconectar(self):
        """Fecha a conexão"""
        if self.conn:
            self.conn.close()
            print("Conexão encerrada.")

    def inserir_substitutos(self, produto_pesquisado, substitutos):
        """
        Insere dados na tabela de substitutos
        Args:
            produto_pesquisado: dict {'codigo': str, 'descricao': str}
            substitutos: lista de dicts [{'codigo': str, 'descricao': str, ...}]
        """
        try:
            with self.conn.cursor() as cursor:
                query = """
                INSERT INTO produtos_substitutos (
                    produto_pesquisado_cod, produto_pesquisado_des,
                    produto_recomendado_cod, produto_recomendado_des,
                    valor_unitario, margem_percentual, estoque, categoria
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                dados = [(
                    produto_pesquisado['codigo'],
                    produto_pesquisado['descricao'],
                    item['codigo'],
                    item['descricao'],
                    item['valor_unitario'],
                    item['margem_percentual'],
                    item['estoque'],
                    item['categoria']
                ) for item in substitutos]
                
                cursor.executemany(query, dados)
                self.conn.commit()
                print(f"{len(substitutos)} substitutos inseridos!")
                return True
                
        except Exception as e:
            self.conn.rollback()
            print(f"Erro ao inserir substitutos: {e}")
            return False

    def inserir_associados(self, produto_pesquisado, associados):
        """
        Insere dados na tabela de associados
        Args:
            produto_pesquisado: dict {'codigo': str, 'descricao': str}
            associados: lista de dicts [{'codigo': str, 'descricao': str, ...}]
        """
        try:
            with self.conn.cursor() as cursor:
                query = """
                INSERT INTO produtos_associados (
                    produto_pesquisado_cod, produto_pesquisado_des,
                    produto_associado_cod, produto_associado_des,
                    suporte, confianca
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """
                
                dados = [(
                    produto_pesquisado['codigo'],
                    produto_pesquisado['descricao'],
                    item['codigo'],
                    item['descricao'],
                    item['suporte'],
                    item['confianca']
                ) for item in associados]
                
                cursor.executemany(query, dados)
                self.conn.commit()
                print(f"{len(associados)} associados inseridos!")
                return True
                
        except Exception as e:
            self.conn.rollback()
            print(f"Erro ao inserir associados: {e}")
            return False


# Exemplo de uso
if __name__ == "__main__":
    # Configuração do banco (substitua com seus dados)
    config = {
        'dbname': 'bd_recomenda',
        'user': 'postgres',
        'password': 'recomenda',
        'host': 'localhost',
        'port': '5432'
    }

    # Dados de exemplo
    produto = {'codigo': 'P001', 'descricao': 'Martelo'}
    
    substitutos = [
        {'codigo': 'P002', 'descricao': 'Martelo Pequeno', 'valor_unitario': 25.90, 
         'margem_percentual': 15.0, 'estoque': 50, 'categoria': 'Ferramentas'},
        {'codigo': 'P003', 'descricao': 'Marreta', 'valor_unitario': 34.50,
         'margem_percentual': 20.5, 'estoque': 30, 'categoria': 'Ferramentas'}
    ]
    
    associados = [
        {'codigo': 'P004', 'descricao': 'Prego 20mm', 'suporte': 15.0, 'confianca': 75.0},
        {'codigo': 'P005', 'descricao': 'Luva de Proteção', 'suporte': 8.5, 'confianca': 60.0}
    ]

    # Execução
    db = InserirDados(config)
    if db.conectar():
        try:
            db.inserir_substitutos(produto, substitutos)
            db.inserir_associados(produto, associados)
        finally:
            db.desconectar()