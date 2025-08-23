# 🛒 Sistema de Recomendação e Cross-Selling

Este projeto implementa um sistema de **recomendação de produtos** desenvolvido para uma distribuidora.  
O objetivo é melhorar a experiência de venda e reduzir perdas quando produtos estão fora de estoque, oferecendo:

- **Substitutos de produtos** (baseados em categoria, preço e margem).  
- **Cross-selling** (regras de associação via Apriori para sugerir produtos frequentemente comprados juntos).  

A solução foi construída em **Python**, possui uma **interface em Flet** e armazena os resultados em um **banco PostgreSQL**.

---

## ⚙️ Funcionalidades
- Limpeza e validação das bases de **estoque** e **notas fiscais**.  
- Geração de uma base consolidada para processamento.  
- Recomendação de produtos **substitutos**.  
- Recomendação de **cross-selling** com algoritmo Apriori.  
- Interface gráfica interativa com **Flet**.  
- Persistência dos resultados em **PostgreSQL**.  

---

## 📂 Estrutura do Projeto
```bash
.
├── main.py                  # Arquivo principal da interface (Flet)
├── limpeza_estoque.py       # Classe de limpeza do estoque
├── limpeza_notas.py         # Classe de limpeza das notas fiscais
├── limpeza_base_mesclada.py # Preparador da base consolidada
├── substitutos.py           # Recomendador de produtos substitutos
├── recomendador.py          # Recomendador de cross-selling (Apriori)
├── salva_banco.py           # Conexão e salvamento no PostgreSQL
├── alimentador_banco.py     # Atualizador e alimentador do banco de dados
├── consolidar.py            # Consolida bases para processamento
├── consultas.py             # Consultas ao banco de dados
├── manual.py                # Manual de instruções do sistema
├── ultima_atualizacao.txt   # Log da última atualização da base
├── requeriment.txt          # Dependências do projeto
└── README.md                # Documentação do projeto
