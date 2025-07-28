import pandas as pd

class EstoqueCleaner:
    def __init__(self, logger=None):
        """
        Inicializa o limpador de base de estoque
        
        Args:
            logger: Objeto logger para registro de mensagens (opcional)
        """
        self.logger = logger
        self.colunas_manter = [
            'Código', 'Produto', 'Código da categoria', 'Categoria',
            'Código da Marca', 'Marca', 'Preço de custo', 'Quantidade estoque'
        ]
    
    def clean(self, df_estoque: pd.DataFrame) -> pd.DataFrame:
        """
        Executa todo o pipeline de limpeza da base de estoque
        
        Args:
            df_estoque: DataFrame com os dados brutos de estoque
            
        Returns:
            DataFrame limpo e tratado
        """
        try:
            self._log("Iniciando limpeza da base de estoque")
            
            # 1. Selecionar colunas relevantes
            df = df_estoque[self.colunas_manter].copy()
            
            # 2. Tratar valores problemáticos no estoque
            df = self._tratar_estoque(df)
            
            # 3. Verificar e tratar duplicatas
            df = self._tratar_duplicatas(df)
            
            # 4. Verificar integridade dos relacionamentos
            df = self._verificar_integridade(df)
            
            # 5. Ajustar tipos de dados e formatação
            df = self._ajustar_formatos(df)
            
            # 6. Renomear colunas
            df = df.rename(columns={'Código': 'Código produto'})
            
            # 7. Validar resultados
            self._validar_resultados(df)
            
            self._log("Limpeza da base de estoque concluída com sucesso")
            return df
            
        except Exception as e:
            self._log(f"Erro ao limpar base de estoque: {str(e)}", level="error")
            raise

    def _tratar_estoque(self, df: pd.DataFrame) -> pd.DataFrame:
        """Trata valores nulos e negativos na coluna de estoque"""
        self._log("Tratando valores de estoque")
        df['Quantidade estoque'] = df['Quantidade estoque'].fillna(0)
        df.loc[df['Quantidade estoque'] < 0, 'Quantidade estoque'] = 0
        return df

    def _tratar_duplicatas(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove registros duplicados e inconsistentes"""
        self._log("Verificando duplicatas")
        
        # Remover produtos com múltiplos códigos
        produto_multiplos_codigos = df.groupby("Produto")["Código"].nunique()
        produtos_problemas = produto_multiplos_codigos[produto_multiplos_codigos > 1].index
        df_limpo = df[~df["Produto"].isin(produtos_problemas)].copy()
        
        # Remover categorias com múltiplos códigos
        categoria_multiplos_codigos = df_limpo.groupby("Categoria")["Código da categoria"].nunique()
        categorias_problemas = categoria_multiplos_codigos[categoria_multiplos_codigos > 1].index
        df_limpo = df_limpo[~df_limpo["Categoria"].isin(categorias_problemas)].copy()
        
        # Remover marcas com múltiplos códigos
        marca_multiplos_codigos = df_limpo.groupby("Marca")["Código da Marca"].nunique()
        marcas_problemas = marca_multiplos_codigos[marca_multiplos_codigos > 1].index
        df_limpo = df_limpo[~df_limpo["Marca"].isin(marcas_problemas)].copy()
        
        return df_limpo

    def _verificar_integridade(self, df: pd.DataFrame) -> pd.DataFrame:
        """Verifica a integridade dos relacionamentos"""
        self._log("Verificando integridade dos dados")
        
        # Verificar unicidade dos códigos de produto
        if df['Código'].duplicated().any():
            self._log("Aviso: Existem códigos de produto duplicados", level="warning")
        
        # Verificar consistência entre código e categoria
        cat_por_codigo = df.groupby('Código')['Código da categoria'].nunique()
        if (cat_por_codigo > 1).any():
            self._log("Aviso: Existem códigos associados a múltiplas categorias", level="warning")
        
        return df

    def _ajustar_formatos(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ajusta tipos de dados e formatação"""
        self._log("Ajustando formatos")
        
        # Converter tipos
        df['Quantidade estoque'] = df['Quantidade estoque'].astype('int64')
        
        # Arredondar preço de custo
        df['Preço de custo'] = df['Preço de custo'].round(2)
        
        return df

    def _validar_resultados(self, df: pd.DataFrame):
        """Gera relatório de validação"""
        self._log("Validando resultados")
        
        # Estatísticas básicas
        originais = len(self.colunas_manter)
        atuais = len(df)
        perc_removido = ((originais - atuais) / originais) * 100
        
        self._log(f"Total original: {originais} registros")
        self._log(f"Total após limpeza: {atuais} registros")
        self._log(f"Percentual removido: {perc_removido:.2f}%")
        
        # Verificação final
        if df.isnull().sum().sum() > 0:
            self._log("Aviso: Existem valores nulos após a limpeza", level="warning")
        
        if (df['Quantidade estoque'] < 0).any():
            self._log("Erro: Existem valores negativos no estoque após limpeza", level="error")

    def _log(self, message: str, level: str = "info"):
        """Método auxiliar para logging"""
        if self.logger:
            getattr(self.logger, level)(message)
        else:
            print(f"[{level.upper()}] {message}")


# Exemplo de uso:
estoque_cleaner = EstoqueCleaner()
df_estoque_limpo = estoque_cleaner.clean('bases/relatorio_produto.xlsx')