import psycopg2
import pandas as pd 
from limpeza_base_mesclada import BasePreparador

class ConsultasBanco:
    def __init__(self, host="localhost", dbname="bd_recomenda", user="postgres", password="recomenda", port=5432):
        self.conn = None
        try:
            self.conn = psycopg2.connect(
                host=host,
                dbname=dbname,
                user=user,
                password=password,
                port=port
            )
        except Exception as e:
            print(f"[ERRO] Falha ao conectar ao banco de dados: {e}")

    def PesquisarProduto(self, cod_produto):
        """Consulta o banco de dados para obter informações sobre um produto específico"""
        if not self.conn:
            print("[ERRO] Conexão com o banco de dados não estabelecida.")
            return None
        
        try:
            cur = self.conn.cursor()
            cur.execute("""
                SELECT * FROM produtos_substitutos
                WHERE produto_pesquisado_cod = %s
            """, (cod_produto,))
            resultado = cur.fetchall()

            cur.close()
            return resultado[0][0:7]
        except Exception as e:
            print(f"[ERRO] Falha ao consultar o banco de dados: {e}")
            return None
        

    def fechar_conexao(self):
        """Fecha a conexão com o banco de dados"""
        if self.conn:
            self.conn.close()
        print("[INFO] Conexão com o banco de dados fechada.")


BasePreparador.preparar_base()
resultado = ConsultasBanco(host="localhost", dbname="bd_recomenda", user="postgres", password="recomenda", port=5432).PesquisarProduto('32608')
print(resultado)