# Requirements Document

## Introduction

A página GitHub Pages do Tokemize é um site estático de showcase do projeto, hospedado via GitHub Pages e atualizado automaticamente por GitHub Actions. O objetivo é apresentar o projeto de forma visual e profissional em apresentações, exibindo estatísticas de contribuições, progresso do desenvolvimento, a proposta de valor do produto e os membros da equipe. A página deve ser autoexplicativa para qualquer pessoa que acesse o repositório ou assista a uma apresentação.

## Glossary

- **Showcase_Page**: A página GitHub Pages estática do projeto Tokemize.
- **GitHub_Actions**: Serviço de CI/CD do GitHub responsável por construir e publicar a página automaticamente.
- **Stats_Widget**: Componente visual que exibe uma métrica específica do projeto (ex: número de commits, PRs, contribuidores).
- **Contribution_Graph**: Visualização gráfica da atividade de commits ao longo do tempo.
- **Progress_Tracker**: Componente que exibe o progresso de desenvolvimento por módulo ou milestone.
- **GitHub_API**: API REST pública do GitHub usada para buscar dados do repositório em tempo real.
- **Static_Site**: Site composto apenas por HTML, CSS e JavaScript, sem backend próprio.
- **Deploy_Workflow**: Workflow do GitHub Actions responsável por publicar a Showcase_Page no branch `gh-pages`.

---

## Requirements

### Requirement 1: Publicação Automática via GitHub Actions

**User Story:** Como membro da equipe, quero que a página seja publicada automaticamente a cada push na branch principal, para que o showcase esteja sempre atualizado sem intervenção manual.

#### Acceptance Criteria

1. WHEN um push é feito na branch `main`, THE Deploy_Workflow SHALL construir e publicar a Showcase_Page no branch `gh-pages`.
2. THE Deploy_Workflow SHALL concluir a publicação em no máximo 5 minutos após o push.
3. IF o build da Showcase_Page falhar, THEN THE Deploy_Workflow SHALL registrar o erro no log do GitHub Actions e interromper o deploy sem sobrescrever a versão anterior publicada.
4. THE Showcase_Page SHALL estar acessível via URL pública do GitHub Pages após cada deploy bem-sucedido.

---

### Requirement 2: Exibição de Estatísticas do Repositório

**User Story:** Como apresentador do projeto, quero ver estatísticas atualizadas do repositório na página, para demonstrar o progresso e a atividade do projeto durante apresentações.

#### Acceptance Criteria

1. WHEN a Showcase_Page é carregada, THE Stats_Widget SHALL exibir o número total de commits do repositório.
2. WHEN a Showcase_Page é carregada, THE Stats_Widget SHALL exibir o número de pull requests abertos e fechados.
3. WHEN a Showcase_Page é carregada, THE Stats_Widget SHALL exibir o número de contribuidores únicos do repositório.
4. WHEN a Showcase_Page é carregada, THE Stats_Widget SHALL exibir o número de branches ativas.
5. WHEN a Showcase_Page é carregada, THE Stats_Widget SHALL exibir a data e hora do último commit na branch `main`.
6. IF a GitHub_API retornar erro ou timeout, THEN THE Stats_Widget SHALL exibir o último valor em cache e indicar visualmente que os dados podem estar desatualizados.
7. THE Stats_Widget SHALL atualizar os dados via GitHub_API com no máximo 1 hora de defasagem em relação ao estado real do repositório.

---

### Requirement 3: Visualização do Gráfico de Contribuições

**User Story:** Como apresentador do projeto, quero exibir um gráfico de atividade de commits ao longo do tempo, para mostrar visualmente o ritmo de desenvolvimento da equipe.

#### Acceptance Criteria

1. WHEN a Showcase_Page é carregada, THE Contribution_Graph SHALL exibir a frequência de commits agrupados por semana nos últimos 90 dias.
2. THE Contribution_Graph SHALL diferenciar visualmente as contribuições por autor usando cores distintas.
3. WHEN o usuário passa o cursor sobre uma barra do Contribution_Graph, THE Contribution_Graph SHALL exibir um tooltip com o número de commits e o período correspondente.
4. THE Contribution_Graph SHALL ser renderizado como um elemento SVG ou Canvas acessível, com texto alternativo descrevendo o conteúdo.

---

### Requirement 4: Rastreamento de Progresso por Módulo

**User Story:** Como apresentador do projeto, quero exibir o progresso de implementação de cada módulo do Tokemize, para mostrar o que já foi construído e o que está em desenvolvimento.

#### Acceptance Criteria

1. THE Progress_Tracker SHALL exibir o status de cada módulo principal do Tokemize: `parser`, `indexer`, `selector`, `optimizer`, `integrations/llm` e `integrations/embeddings`.
2. WHEN um módulo possui arquivos de código-fonte no repositório, THE Progress_Tracker SHALL exibir o status desse módulo como "Em desenvolvimento" ou "Concluído" com base em critério configurável no arquivo de configuração da página.
3. THE Progress_Tracker SHALL representar o progresso geral do projeto como uma porcentagem calculada a partir do número de módulos com status "Concluído" em relação ao total de módulos.
4. WHERE o status de um módulo for configurado manualmente, THE Progress_Tracker SHALL priorizar o valor configurado sobre qualquer inferência automática.

---

### Requirement 5: Apresentação da Proposta de Valor

**User Story:** Como visitante da página, quero entender rapidamente o que é o Tokemize e qual problema ele resolve, para que eu possa compreender o projeto sem precisar ler o README.

#### Acceptance Criteria

1. THE Showcase_Page SHALL exibir o nome do projeto "Tokemize" e o tagline *"Uma camada intermediária que melhora como usamos IA"* na seção principal (hero).
2. THE Showcase_Page SHALL exibir os três problemas principais que o Tokemize resolve: alto custo de tokens, respostas imprecisas e processamento ineficiente.
3. THE Showcase_Page SHALL exibir o fluxo do pipeline de forma visual: `Entrada Bruta → Tokemize → Entrada Otimizada`.
4. THE Showcase_Page SHALL exibir as tecnologias utilizadas (Python, Tree-sitter, FAISS, OpenAI API, Anthropic API) com links para suas respectivas documentações oficiais.

---

### Requirement 6: Exibição dos Membros da Equipe

**User Story:** Como visitante da página, quero ver quem são os membros da equipe do Tokemize, para reconhecer os contribuidores do projeto.

#### Acceptance Criteria

1. THE Showcase_Page SHALL exibir o nome e o link para o perfil GitHub de cada membro da equipe: Eneri da Costa Junior, Guilherme Valerio Mertens, Paulo Sergio, Samuel Magalhães Marques e Eduardo Notari.
2. WHEN a GitHub_API estiver disponível, THE Showcase_Page SHALL exibir o avatar de cada membro carregado diretamente do perfil GitHub correspondente.
3. IF a GitHub_API não estiver disponível, THEN THE Showcase_Page SHALL exibir um avatar padrão no lugar da foto do membro.

---

### Requirement 7: Design Responsivo e Adequado para Apresentações

**User Story:** Como apresentador do projeto, quero que a página seja visualmente clara em telas grandes (projetores e monitores), para que o conteúdo seja legível durante apresentações.

#### Acceptance Criteria

1. THE Showcase_Page SHALL ser renderizada corretamente em resoluções de 1280×720, 1920×1080 e 2560×1440.
2. THE Showcase_Page SHALL ser renderizada corretamente em dispositivos móveis com largura mínima de 375px.
3. THE Showcase_Page SHALL utilizar contraste de cores com razão mínima de 4.5:1 entre texto e fundo, conforme WCAG 2.1 nível AA.
4. THE Showcase_Page SHALL carregar completamente em no máximo 3 segundos em conexão de 10 Mbps.
5. THE Showcase_Page SHALL ser implementada como um Static_Site sem dependência de backend próprio, utilizando apenas HTML, CSS e JavaScript.

---

### Requirement 8: Configuração Declarativa do Conteúdo

**User Story:** Como membro da equipe, quero poder atualizar o conteúdo da página (status dos módulos, textos, links) editando um arquivo de configuração, para não precisar modificar o HTML diretamente.

#### Acceptance Criteria

1. THE Showcase_Page SHALL ler as configurações de conteúdo a partir de um arquivo `config.json` localizado na raiz do projeto da página.
2. WHEN o arquivo `config.json` é atualizado e um push é feito na branch `main`, THE Deploy_Workflow SHALL publicar a Showcase_Page com o conteúdo atualizado automaticamente.
3. THE `config.json` SHALL permitir configurar: nome do projeto, tagline, lista de módulos com seus status, lista de membros da equipe e links externos.
4. IF o arquivo `config.json` estiver ausente ou malformado, THEN THE Showcase_Page SHALL exibir os valores padrão definidos em código e registrar um aviso no console do navegador.
