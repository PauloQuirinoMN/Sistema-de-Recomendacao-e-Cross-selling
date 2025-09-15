import pandas as pd
from typing import Optional
from data_utils import normalize_columns, map_columns_by_candidates
from capturar_log import LogCapture

class NotasCleaner:
    """
    Limpa e padroniza DataFrame de notas fiscais.

    Args:
        logger: instância de LogCapture (opcional).
        remove_ambiguous: se True remove descrições ambíguas; se False apenas gera relatório.
    """

    def __init__(self, logger: Optional[LogCapture] = None, remove_ambiguous: bool = True):
        self.logger = logger
        self.remove_ambiguous = remove_ambiguous

        self.candidates = {
            "numero_nota_fiscal": ["numero_nota_fiscal", "numero_nota", "nota_fiscal", "n_nota", "num_nota"],
            "data_venda": ["data_da_venda", "data_venda", "data"],
            "codigo_produto": ["codigo_produto", "codigo", "cod_produto", "cod_prod"],
            "descricao_produto": ["descricao_do_produto", "descricao", "produto", "descricao_produto"],
            "quantidade_produto": ["quantidade_do_produto", "quantidade", "qtd", "qtd_produto"],
            "valor_unitario": ["valor_unitario", "valor_unit", "preco_unitario"],
            "preco_custo": ["preco_de_custo", "preco_custo", "custo"]
        }

        self.final_cols = [
            "numero_nota_fiscal", "data_venda", "codigo_produto",
            "descricao_produto", "quantidade_produto", "valor_unitario",
            "preco_custo", "valor_total_produto", "valor_da_nota"
        ]

        # Relatórios/diagnósticos (populados durante `clean`)
        self.removed_notas_df: Optional[pd.DataFrame] = None
        self.ambiguous_descriptions_df: Optional[pd.DataFrame] = None

        if self.logger:
            self.logger.log("🚀 Inicializado limpeza das Notas .")

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(df, pd.DataFrame):
            raise ValueError("Entrada deve ser um pandas.DataFrame")

        # Trabalhar em cópia para não alterar o objeto original
        df = df.copy()

        # Strip nas colunas antes do mapeamento
        df.columns = df.columns.astype(str).str.strip()

        # 1. Normaliza e mapeia colunas
        df = normalize_columns(df)
        df = map_columns_by_candidates(df, self.candidates)

        # 2. Garantir colunas numéricas básicas (criar com defaults se ausentes)
        for col, default in [
            ("quantidade_produto", 0),
            ("valor_unitario", 0.0),
            ("preco_custo", 0.0)
        ]:
            if col not in df.columns:
                if self.logger:
                    self.logger.log(f"Coluna '{col}' ausente — criando com default {default}.")
                df[col] = default

        # 3. Conversões numéricas seguras
        df["quantidade_produto"] = (
            pd.to_numeric(df["quantidade_produto"], errors="coerce")
            .fillna(0)
            .round(0)
            .astype("Int64")   # preserva NA se houver
        )
        df["valor_unitario"] = (
            pd.to_numeric(df["valor_unitario"], errors="coerce")
            .fillna(0.0)
            .round(2)
        )
        df["preco_custo"] = (
            pd.to_numeric(df["preco_custo"], errors="coerce")
            .fillna(0.0)
            .round(2)
        )

        # 4. Remover notas com problemas (quantidade <= 0 ou valor_unitario == 0)
        if "numero_nota_fiscal" in df.columns:
            before = len(df)
            mask_problem = (df["quantidade_produto"] <= 0) | (df["valor_unitario"] == 0)
            notas_problema_series = df.loc[mask_problem, "numero_nota_fiscal"].dropna().unique()
            notas_problema = set(notas_problema_series.tolist())
            if notas_problema:
                if self.logger:
                    self.logger.log(f"Removendo {len(notas_problema)} notas com problemas (quantidade/valor).")
                # Salva linhas removidas para auditoria
                self.removed_notas_df = df[df["numero_nota_fiscal"].isin(notas_problema)].copy()
                df = df[~df["numero_nota_fiscal"].isin(notas_problema)].copy()
                if self.logger:
                    self.logger.log(f"Linhas removidas: {before - len(df)}")
        else:
            if self.logger:
                self.logger.log("Atenção: 'numero_nota_fiscal' não encontrada; pular remoção por nota.")

        # 5. Detectar descrições ambíguas (mesma descrição com vários códigos)
        if {"descricao_produto", "codigo_produto"}.issubset(df.columns):
            counts = df.groupby("descricao_produto")["codigo_produto"].nunique()
            ambiguous = counts[counts > 1]
            if not ambiguous.empty:
                amb_desc = ambiguous.index.tolist()
                if self.logger:
                    self.logger.log(f"Detectadas {len(amb_desc)} descrições ambíguas (múltiplos códigos).")
                # exportar relatório de linhas ambíguas
                self.ambiguous_descriptions_df = df[df["descricao_produto"].isin(amb_desc)].copy()
                # comportamento controlável: remover ou apenas reportar
                if self.remove_ambiguous:
                    before = len(df)
                    df = df[~df["descricao_produto"].isin(amb_desc)].copy()
                    if self.logger:
                        self.logger.log(f"Removidas {before - len(df)} linhas por descrições ambíguas.")
                else:
                    if self.logger:
                        self.logger.log("As descrições ambíguas foram reportadas, mas não removidas (remove_ambiguous=False).")
        else:
            if self.logger:
                self.logger.log("Campos para detecção de descrições ambíguas ausentes; pulando etapa.")

        # 6. Calcular valor_total_produto e valor_da_nota
        df["valor_total_produto"] = (df["quantidade_produto"] * df["valor_unitario"]).round(2)
        if "numero_nota_fiscal" in df.columns:
            # usar transform para perf e garantia de alinhamento
            df["valor_da_nota"] = df.groupby("numero_nota_fiscal")["valor_total_produto"].transform("sum").round(2)
        else:
            df["valor_da_nota"] = df["valor_total_produto"]

        # 7. Garantir colunas finais
        for c in self.final_cols:
            if c not in df.columns:
                df[c] = pd.NA

        # 8. Selecionar apenas colunas finais na ordem desejada
        df = df[self.final_cols].copy()

        if self.logger:
            self.logger.log(f"Limpeza concluída. Total de registros finais: {len(df)}")
        return df
