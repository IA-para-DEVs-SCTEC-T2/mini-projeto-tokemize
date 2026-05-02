---
title: Stack de Tecnologia
inclusion: always
---

# Stack Principal

## Linguagem
- Python 3.11+ como linguagem de orquestração principal

## Análise Sintática
- Tree-sitter para parsing e extração de estrutura do código-fonte
- Suporte a múltiplas linguagens (Python, Java, JavaScript, TypeScript etc.)
- Extração de funções, classes, imports e símbolos relevantes por escopo

## Indexação Vetorial
- FAISS para indexação e busca por similaridade semântica
- Embeddings gerados via API (OpenAI text-embedding ou equivalente)
- Índices persistidos localmente para reuso entre sessões

## Integração com LLMs
- OpenAI API (GPT-4o, GPT-4-turbo)
- Anthropic API (Claude Sonnet, Claude Opus)
- Abstração comum para troca de provider sem alterar o pipeline

## Convenções de Código
- Tipagem estática com type hints em todas as funções e classes
- Docstrings no padrão Google Style
- Gerenciamento de dependências com Poetry ou pip + requirements.txt
- Variáveis de ambiente via python-dotenv (.env), nunca hardcoded
- Testes com pytest

## O que Evitar
- Nunca enviar contexto raw sem passar pelo pipeline de otimização
- Nunca instanciar clientes de LLM diretamente fora da camada de integração
- Não misturar lógica de parsing com lógica de seleção de contexto