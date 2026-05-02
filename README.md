# Tokemize — Agente de otimização de Contexto para LLMs

> *"Uma camada intermediária que melhora como usamos IA."*

## 🚨 O Problema

Agentes de IA recebem contexto demais e sem critério, o que acaba prejudicando o desenvolvimento de software moderno.

**Principais consequências:**
- 💸 Alto custo de tokens.
- 📉 Respostas imprecisas e alucinações.
- ⏳ Processamento ineficiente.

## 💡 A Ideia

Um agente inteligente que decide **exatamente** o que deve ser enviado ao LLM, otimizando cada requisição técnica. 

> *"Mais contexto não significa melhor resposta."*

**Como funciona:**
`Entrada Bruta` ➔ `Tokemize` ➔ `Entrada Otimizada`

## 🏗️ Arquitetura da Solução

O fluxo da solução foi projetado para atuar como um middleware inteligente:

`Usuário` ➔ `Tokemize` ➔ `Seleção` ➔ `Resumo` ➔ `Otimização` ➔ `LLM`

Para detalhes completos da arquitetura, consulte [docs/architecture.md](docs/architecture.md).

## 🧩 Componentes do Sistema

- **Análise de Repositório:** Mapeamento completo da estrutura do código.
- **Seleção Inteligente:** Filtro de relevância baseado no contexto técnico da requisição.
- **Compressão e Resumo:** Redução semântica inteligente do volume de dados.
- **Cache de Contexto:** Eficiência máxima e redução de custos em consultas repetitivas.

## 🛠️ Tecnologias Utilizadas

- **[Python](https://docs.python.org/3/):** Orquestração Principal.
- **[Tree-sitter](https://tree-sitter.github.io/tree-sitter/):** Análise Sintática do código.
- **[FAISS](https://faiss.ai/index.html):** Indexação Vetorial para buscas eficientes.
- **APIs de LLM:** Integrações com serviços como OpenAI, Anthropic e [Groq](https://console.groq.com/docs/overview).

Para detalhes e justificativas de cada tecnologia, consulte [docs/technologies.md](docs/technologies.md).

## 🚀 Instalação e Execução

### Pré-requisitos

- Python 3.10 ou superior
- [pip](https://pip.pypa.io/en/stable/)

### Instalação

```bash
# Clone o repositório
git clone https://github.com/IA-para-DEVs-SCTEC-T2/mini-projeto-tokemize.git
cd mini-projeto-tokemize

# (Recomendado) Crie e ative um ambiente virtual
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

# Instale as dependências
pip install -e .
```

### Executando os testes

```bash
# Testes Python
python -m pytest tests/

# Testes do showcase (requer Node.js 18+)
cd docs/showcase
npm install
npm test
```

## 💻 Exemplo de Uso

> **Nota:** o módulo principal ainda está em desenvolvimento. O exemplo abaixo ilustra o fluxo previsto.

```python
from tokemize import Tokemize

# Inicializa o agente apontando para um repositório local
agent = Tokemize(repo_path="./meu-projeto")

# Envia uma query — o Tokemize seleciona e otimiza o contexto automaticamente
response = agent.query(
    prompt="Como funciona a autenticação de usuários neste projeto?",
    llm_provider="openai",
)

print(response)
```

## 📚 Documentação

| Documento | Descrição |
|---|---|
| [docs/architecture.md](docs/architecture.md) | Fluxo e componentes da arquitetura |
| [docs/technologies.md](docs/technologies.md) | Stack tecnológica e justificativas |
| [docs/roadmap.md](docs/roadmap.md) | Progresso dos módulos e próximas entregas |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Guia de contribuição (branches e commits) |

## 👥 Equipe

- **Eneri da Costa Junior** ([@jrcosta](https://github.com/jrcosta))
- **Guilherme Valerio Mertens** ([@gvmertens](https://github.com/gvmertens))
- **Paulo Sergio** ([@PauloSergioLR](https://github.com/PauloSergioLR))
- **Samuel Magalhães Marques** ([@samuelmarquesgit](https://github.com/samuelmarquesgit))
- **Eduardo Notari** ([@edunotari](https://github.com/edunotari))
