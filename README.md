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

## 👥 Equipe

- **Eneri da Costa Junior** ([@jrcosta](https://github.com/jrcosta))
- **Guilherme Valerio Mertens** ([@gvmertens](https://github.com/gvmertens))
- **Paulo Sergio** ([@PauloSergioLR](https://github.com/PauloSergioLR))
- **Samuel Magalhães Marques** ([@samuelmarquesgit](https://github.com/samuelmarquesgit))
- **Eduardo Notari** ([@edunotari](https://github.com/edunotari))
