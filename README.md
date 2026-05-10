# Tokemize - Otimização de Contexto para LLMs

> Gera contexto compacto e direcionado para usar em chatbots de IDE e outras ferramentas com LLM.

## O Problema

Ferramentas com LLM recebem contexto demais e sem criterio, o que prejudica o desenvolvimento de software moderno.

**Principais consequencias:**
- Alto custo de tokens.
- Respostas imprecisas e alucinacoes.
- Processamento ineficiente.
- Prompts longos, dificeis de revisar e pouco reproduziveis.

## A Ideia

O Tokemize analisa um repositorio local e prepara um prompt otimizado com apenas o contexto relevante para uma tarefa tecnica. Ele nao chama provedores de LLM nem retorna uma resposta gerada por IA; o resultado e um prompt pronto para ser colado no chatbot da IDE.

> "Mais contexto nao significa melhor resposta."

**Como funciona:**

`Repositorio + tarefa` -> `Tokemize` -> `Contexto compacto` -> `Prompt otimizado`

## Fluxo Atual

A implementacao atual da CLI executa um pipeline local, sem chamada a LLM:

1. **Repository Analyzer:** analisa os arquivos do repositorio informado.
2. **Intelligent Selector:** seleciona os artefatos mais relevantes para a tarefa.
3. **Compressor:** compacta o contexto selecionado.
4. **Context Store:** salva o contexto em `.tokemize/context/` quando possivel.
5. **Prompt Builder:** monta um prompt Markdown com a tarefa e as referencias do contexto.
6. **Clipboard/Output:** copia o prompt para a area de transferencia, imprime no terminal ou salva em arquivo.

Fluxo resumido:

`Usuario` -> `Tokemize CLI` -> `Analise` -> `Selecao` -> `Compactacao` -> `Prompt otimizado`

Para detalhes completos da arquitetura, consulte [docs/architecture.md](docs/architecture.md).

## Componentes do Sistema

- **Analise de Repositorio:** mapeamento da estrutura e dos artefatos do codigo.
- **Selecao Inteligente:** filtro de relevancia baseado na tarefa tecnica informada.
- **Compressao de Contexto:** reducao do volume de dados preservando informacao util.
- **Persistencia de Contexto:** armazenamento local do contexto compacto para auditoria e reuso.
- **Geracao de Prompt:** montagem do prompt final para uso em chatbots de IDE.

## Tecnologias Utilizadas

- **[Python](https://docs.python.org/3/):** CLI e orquestracao principal.
- **[Tree-sitter](https://tree-sitter.github.io/tree-sitter/):** analise sintatica do codigo.
- **[FAISS](https://faiss.ai/index.html):** base planejada para indexacao vetorial e busca semantica.
- **[Typer](https://typer.tiangolo.com/):** comandos de linha de comando.
- **[pyperclip](https://pyperclip.readthedocs.io/):** copia do prompt para a area de transferencia.

Para detalhes e justificativas de cada tecnologia, consulte [docs/technologies.md](docs/technologies.md).

## Instalacao e Execucao

### Pre-requisitos

- Python 3.11 ou superior
- [pip](https://pip.pypa.io/en/stable/)

### Instalacao

```bash
# Clone o repositorio
git clone https://github.com/IA-para-DEVs-SCTEC-T2/mini-projeto-tokemize.git
cd mini-projeto-tokemize

# Crie e ative um ambiente virtual
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

# Instale as dependencias
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

## Exemplo de Uso

Analise o repositorio atual e gere um prompt otimizado para uma tarefa:

```bash
tokemize toke "corrija o fluxo de login" --repo . --print
```

Salve o prompt gerado em um arquivo Markdown:

```bash
tokemize prepare ./meu-projeto "explique como a autenticacao funciona" --output prompt.md
```

Ao final, o Tokemize entrega um prompt otimizado. Esse prompt pode ser colado no chatbot da IDE ou em outro LLM de sua escolha.

## Documentacao

| Documento | Descricao |
|---|---|
| [docs/architecture.md](docs/architecture.md) | Fluxo e componentes da arquitetura |
| [docs/technologies.md](docs/technologies.md) | Stack tecnologica e justificativas |
| [docs/roadmap.md](docs/roadmap.md) | Progresso dos modulos e proximas entregas |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Guia de contribuicao (branches e commits) |

## Equipe

- **Eneri da Costa Junior** ([@jrcosta](https://github.com/jrcosta))
- **Guilherme Valerio Mertens** ([@gvmertens](https://github.com/gvmertens))
- **Paulo Sergio** ([@PauloSergioLR](https://github.com/PauloSergioLR))
- **Samuel Magalhaes Marques** ([@samuelmarquesgit](https://github.com/samuelmarquesgit))
- **Eduardo Notari** ([@edunotari](https://github.com/edunotari))
