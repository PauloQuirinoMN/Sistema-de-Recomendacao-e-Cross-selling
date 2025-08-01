# main.py

import pandas as pd
from limpeza_estoque import EstoqueCleaner
from limpeza_notas import NotasCleaner
from limpeza_base_mesclada import BasePreparador
from substitutos import RecomendadorSubstituto
from recomendador import RecomendadorCrossSelling

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
    cod_produto = 29923
    # 🔁 Altere aqui o produto para testar
    print(f"🔍 Produto pesquisado: {cod_produto} (Substituição)\n")

    recomendador = RecomendadorSubstituto(df_modelo)
    resultado_sub = recomendador.recomendar(cod_produto)

    print("📦 Resultado da Recomendação de Substitutos:")
    print(resultado_sub.to_string(), "\n")

    # 4. Recomendação por Cross-Selling
    print(f"🔄 Produto pesquisado: {cod_produto} (Cross-Selling)\n")
    cross = RecomendadorCrossSelling(df_modelo)
    regras = cross.gerar_regras(cod_produto, min_support=0.005, min_threshold=1.0, max_len=2)

    if regras.empty:
        print("⚠️ Nenhum produto associado encontrado para cross-selling.")
    else:
        df_formatado = cross.formatar_regras(regras)
        print("🤝 Produtos frequentemente comprados juntos:")
        print(df_formatado.head(6).to_string())

if __name__ == "__main__":
    main()
