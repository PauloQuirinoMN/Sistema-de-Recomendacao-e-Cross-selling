# Sistema de Recomendação de Produtos -- MVP v1.0

Sistema desenvolvido em Python para fornecer recomendações de produtos em vendas, com foco em **substitutos** (produtos similares) e **associados** (cross-selling). O sistema analisa dados de estoque e notas fiscais, gera regras de associação e apresenta uma interface gráfica interativa.

## 📌 Funcionalidades

1. **Recomendação de Substitutos**
   - Sugere produtos similares da mesma categoria quando um item não está disponível.
   - Considera preço, margem e estoque para oferecer alternativas relevantes.

2. **Recomendação de Produtos Associados (Cross-Selling)**
   - Indica produtos frequentemente comprados juntos com base em regras de associação usando um modelo de Machine Learning (Apriori).
   - Permite aumentar o ticket médio das vendas.

3. **Atualização Automática da Base**
   - Carrega e limpa automaticamente as bases de estoque e notas fiscais.
   - Gera tabelas consolidadas no banco de dados PostgreSQL.
   - Permite atualização assíncrona e acompanhamento em tempo real via UI.

4. **Interface Interativa**
   - Pesquisa de produtos por código.
   - Exibição de resultados de substitutos e produtos associados em tabelas.
   - Logs de processamento e progresso visíveis durante a atualização.
   - Manual integrado para orientação do usuário.

5. **Armazenamento e Persistência**
   - Base de dados PostgreSQL organizada em três tabelas:
     - `produtos_consolidados` -- Base completa de produtos mesclado base de estoque e notas fiscais.
     - `produtos_substitutos` -- Produtos sugeridos como alternativas.
     - `produtos_associados` -- Produtos frequentemente comprados juntos.

## 🛠 Tecnologias e Dependências

- **Python 3.11+**
- **Bibliotecas**:
  - pandas==2.3.0
  - numpy==2.3.2
  - openpyxl==3.1.5
  - mlxtend==0.23.1
  - python-dateutil==2.9.0
  - pytz==2025.2
  - flet==0.26.0
  - psycopg2==2.9.10
  - SQLAlchemy==2.0.43
- **Banco de Dados**: PostgreSQL 15+

- 
## ⚙️ Estrutura do Projeto
``` 
├── assets/                  # Arquivos de mídia ou ícones da interface
├── bases/                   # Arquivos Excel de estoque e notas fiscais
├── venv/                    # Ambiente virtual Python
├── .gitignore               # Arquivos e pastas ignorados pelo Git
├── alimentador_banco2.py    # Carrega, limpa e prepara a base; gera substitutos e associados
├── consolidar.py            # Consolida dados em tabela única de produtos
├── consultas.py             # Classes de busca e criação de tabelas de recomendação
├── limpeza_base_mesclada.py # Limpeza e preparação da base mesclada
├── limpeza_estoque.py       # Limpeza da base de estoque
├── limpeza_notas.py         # Limpeza da base de notas fiscais
├── main.py                  # Interface principal (Flet)
├── manual.py                # Componente UI com instruções do sistema
├── recomendador.py          # Regras de associação e cross-selling
├── requirements.txt         # Dependências do projeto
├── salva_banco.py           # Insere dados substitutos, associados no banco
├── substitutos.py           # Geração de produtos substitutos
└── ultima_atualizacao.txt   # Log da última atualização da base
```

## ⚡ Como Usar

### 1. Configurar o Banco de Dados
- Instale e configure PostgreSQL.
- Crie o banco `rec`.
- Certifique-se que o usuário tenha permissões de leitura e escrita.

### 2. Instalar Dependências

pip install -r requirements.txt

### 3. Preparar Bases de Dados

- Coloque os arquivos Excel de estoque e notas em `bases/`.
- Nome sugerido:
  - `relatorio_produtos.xlsx`
  - `relatorio_notas.xlsx`

### 4. Executar o Sistema


python main.py

### 5. Uso da Interface

- Digite o **código do produto** no campo de pesquisa.
- Clique em **Enter** para exibir informações do produto, substitutos e produtos associados.
- Limpa a tela voltando ao Manual clicando em **Limpar pesquisa**.
- Clique em **Atualizar bases de dados** para recarregar as informações.

#### Fluxo do sistema

- O sistema carrega e limpa os dados de estoque e notas fiscais.
- Consolida a base em `produtos_consolidados`.
- Calcula substitutos e associados.
- Atualiza a interface com recomendações ao buscar um código de produto.

## Observações

- A primeira execução gera arquivos de log e atualiza o banco com a base consolidada.
- A interface exibe mensagens claras em caso de código inválido ou produto não encontrado.
- As recomendações são limitadas para evitar inserções excessivas no banco.

## 📝 Notas Técnicas

- Atualizações da base são **assíncronas**, evitando travamento da interface.
- Regras de associação (cross-selling) usam **Apriori** com suporte e confiança configuráveis.
- Logs detalhados são gravados em `ultima_atualizacao.txt`.
- UI construída com **Flet**, oferecendo uma experiência responsiva e moderna.

## 💡 Dicas

- Use códigos completos de produtos para maior precisão.
- Verifique substitutos antes de oferecer alternativas aos clientes.
- Explore produtos associados para aumentar o ticket médio.

## 🔒 Segurança e Observações

- Banco PostgreSQL deve estar protegido com senha e acessível apenas à rede confiável.
- Evite executar o sistema em redes públicas sem VPN ou firewall adequado.

## Fluxo de execução e dependências entre arquivos

### 1. main.py
- Ponto de entrada do sistema (interface Flet).
- Cria a interface de busca de produtos, tabela de substitutos e associados.
- Conecta ao banco de dados PostgreSQL via SQLAlchemy.
- Dependências chamadas:
  - `alimentador_banco2.py` → para atualizar e processar a base.
  - `consultas.py` → para buscar produtos, gerar tabelas de substitutos e associados.
  - `manual.py` → componente UI com instruções do sistema.

### 2. alimentador_banco2.py
- Carrega e limpa as bases de estoque e notas fiscais.
- Consolida a base em uma base mesclada pronta para análise.
- Chama sequencialmente:
  - `limpeza_estoque.py` → limpa a base de estoque.
  - `limpeza_notas.py` → limpa a base de notas fiscais.
  - `limpeza_base_mesclada.py` → combina e prepara a base mesclada.
- Depois, para cada produto da base:
  - `substitutos.py` → gera produtos substitutos com base na categoria, preço, margem e estoque.
  - `recomendador.py` → gera produtos associados (cross-selling) usando regras de associação (Apriori).
- Finaliza salvando tudo no banco via:
  - `salva_banco.py` → insere produtos substitutos e associados no PostgreSQL.
  - `consolidar.py` → garante que a base consolidada de produtos exista no banco antes da inserção.

### 3. consultas.py
- Fornece funções e classes para a interface:
  - `PesquisaProduto` → busca informações de um produto no banco.
  - `TabelaRecomendacao` → monta a tabela de substitutos para o UI.
  - `TabelaAssociados` → monta a tabela de produtos comprados juntos para o UI.

### 4. manual.py
- Componente UI estático, apenas fornece instruções de uso do sistema.
- Não possui dependências, apenas é carregado dentro do UI principal (main.py) quando não há resultados.

### 5. salva_banco.py
- Insere os dados de substitutos e associados no PostgreSQL.
- Chama `consolidar.py` para criar a tabela de produtos consolidados, se necessário.

### 6. consolidar.py
- Consolida a base de produtos em `produtos_consolidados`.
- Garantia de integridade antes de salvar substitutos ou produtos associados.

## ✅ Resumo do fluxo de dados:

1. A interface (`main.py`) inicia e solicita dados.
2. `alimentador_banco2.py` carrega e limpa os dados das bases (estoque + notas).
3. Gera a base consolidada (`limpeza_base_mesclada.py`).
4. Calcula substitutos (`substitutos.py`) e associados/cross-selling (`recomendador.py`).
5. Salva no banco (`salva_banco.py`), garantindo a base consolidada (`consolidar.py`).
6. A interface (`main.py`) busca informações do banco e exibe via `consultas.py` e `manual.py`.

## Legenda do fluxo:

### 1. main.py → Interface do sistema, inicia todo o processo e chama:
- `alimentador_banco2.py` → atualiza a base de produtos, substitutos e associados.
- `consultas.py` → busca produtos e gera tabelas para UI.

### 2. alimentador_banco2.py → orquestra a limpeza, consolidação e cálculos:
- `limpeza_estoque.py` → limpa base de estoque.
- `limpeza_notas.py` → limpa base de notas.
- `limpeza_base_mesclada.py` → cria base mesclada pronta para análise.
- `substitutos.py` → gera produtos substitutos.
- `recomendador.py` → gera produtos associados (cross-selling).
- `salva_banco.py` → insere os dados no banco, chamando `consolidar.py` se necessário.

### 3. consultas.py → fornece funções para UI, exibindo:
- `TabelaRecomendacao` → tabela de substitutos.
- `TabelaAssociados` → tabela de produtos comprados juntos.

## 📊 Diagrama de Fluxo de Dados do Sistema
```
main.py (UI Flet)
├─> alimentador_banco2.py   (Atualiza base de dados)
│   └─> limpeza_estoque.py
│      └─> limpeza_notas.py
│         └─> limpeza_base_mesclada.py
│            └─> substitutos.py
│               └─> recomendador.py   (cross-selling)
│                  └─> salva_banco.py
│                     └─> consolidar.py
│                        └─> consultas.py    (busca produtos e gera tabelas de recomendação)
├─> TabelaRecomendacao
└─> TabelaAssociados
```


