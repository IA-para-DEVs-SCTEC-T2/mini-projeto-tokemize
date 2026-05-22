# Fluxograma do Projeto Tokemize

O diagrama Mermaid esta no arquivo [`fluxograma-projeto.mmd`](./fluxograma-projeto.mmd).

Para visualizar:
- **GitHub**: abra o arquivo `.mmd` diretamente no navegador
- **VS Code**: instale a extensao "Mermaid Preview" e abra o `.mmd`
- **CLI**: `npx @mermaid-js/mermaid-cli mmdc -i fluxograma-projeto.mmd -o fluxograma-projeto.svg`

## Visao do Fluxo

O fluxograma cobre o caminho principal da CLI:

1. Entrada do usuario com repositorio e tarefa.
2. Validacao de caminho e descricao da tarefa.
3. Analise do repositorio e extracao de artefatos.
4. Selecao dos artefatos mais relevantes.
5. Compressao e persistencia opcional do contexto.
6. Geracao do prompt final.
7. Saidas opcionais em arquivo, terminal e clipboard.
