# main.py

import pandas as pd
from limpeza_estoque import EstoqueCleaner
from limpeza_notas import NotasCleaner
from limpeza_base_mesclada import BasePreparador
from substitutos import RecomendadorSubstituto
from recomendador import RecomendadorCrossSelling
from main_test import salvar_no_banco

def main():
    print("[INFO] Iniciando processo de recomendação...\n")

    # 1. Limpar bases
    print("[INFO] Limpando base de estoque...")
    estoque_raw = pd.read_excel("bases/relatorio_produtos.xlsx")
    df_estoque_limpo = EstoqueCleaner().clean(estoque_raw)
    print("[INFO] Estoque limpo com sucesso.")

    print("[INFO] Limpando base de notas fiscais...")
    notas_raw = pd.read_excel("bases/relatorio_notas.xlsx")
    df_notas_limpa = NotasCleaner().clean(notas_raw)
    print("[INFO] Notas limpas com sucesso.")

    # 2. Preparar base final
    preparador = BasePreparador()
    df_modelo = preparador.preparar_base(df_estoque_limpo, df_notas_limpa)


    print(f"[INFO] Base final possui {len(df_modelo)} registros válidos\n")
    # 3. Recomendação de Substitutos
    cod_produto = 6560

    # busca descrição do produto pesquisado
    desc_produto_pesquisado = None
    try:
        desc_produto_pesquisado = df_modelo.loc[
            df_modelo['Código produto'] == cod_produto, 'Descrição do produto'
        ].values[0]
    except IndexError:
        desc_produto_pesquisado = 'Descrição não encontrada'

    print(f"🔍 Produto pesquisado: {cod_produto} (Substituição)\n")

    recomendador = RecomendadorSubstituto(df_modelo)
    resultado_sub = recomendador.recomendar(cod_produto)

    # 🔹 Adiciona código e descrição do produto pesquisado no DataFrame
    resultado_sub.insert(0, "Código pesquisado", cod_produto)
    resultado_sub.insert(1, "Descrição pesquisada", desc_produto_pesquisado)

    print("📦 Resultado da Recomendação de Substitutos:")
    print(resultado_sub.to_string(), "\n")


    # 4. Recomendação por Cross-Selling
    print(f"🔄 Produto pesquisado: {cod_produto} (Cross-Selling)\n")
    cross = RecomendadorCrossSelling(df_modelo)
    regras = cross.gerar_regras(cod_produto, min_support=0.005, min_threshold=1.0, max_len=2)

    df_formatado = pd.DataFrame()

    if regras.empty:
        print("⚠️ Nenhum produto associado encontrado para cross-selling.")
    else:
        df_formatado = cross.formatar_regras(regras)
        print("🤝 Produtos frequentemente comprados juntos:")
        print(df_formatado.head(6).to_string())

        # Salvar no banco
    # Depois de gerar df_modelo, resultado_sub e df_formatado
    salvar_no_banco(resultado_sub, df_formatado, df_modelo, limite=6)


    return cod_produto, desc_produto_pesquisado, resultado_sub, df_formatado

if __name__ == "__main__":
    main()
