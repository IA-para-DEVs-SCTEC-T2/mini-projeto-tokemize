# Implementation Plan: GitHub Pages Project Showcase

## Overview

Implementação da Showcase_Page do Tokemize como um site estático (HTML + CSS + JavaScript puro) hospedado no GitHub Pages. A implementação segue a arquitetura definida no design: `ConfigLoader`, `ApiClient`, `CacheStore` e componentes de UI independentes, com deploy automatizado via GitHub Actions e testes baseados em propriedades usando fast-check.

## Tasks

- [x] 1. Estrutura do projeto e configuração inicial
  - Criar o diretório `docs/showcase/` com a estrutura de arquivos definida no design
  - Criar `docs/showcase/index.html` com o shell HTML semântico (seções `#hero`, `#stats`, `#contribution-graph`, `#progress`, `#pipeline`, `#tech-stack`, `#team`)
  - Criar `docs/showcase/style.css` com variáveis CSS, reset e layout base responsivo (grid/flexbox)
  - Criar `docs/showcase/app.js` como entry point que importa e inicializa todos os módulos
  - Criar `docs/showcase/config.json` com os dados completos do Tokemize conforme o modelo de dados do design (projectName, tagline, repo, problems, pipeline, techStack, modules, team, links)
  - Configurar `package.json` em `docs/showcase/` com fast-check e Vitest como dependências de desenvolvimento
  - Criar `docs/showcase/__tests__/` com arquivos de teste vazios para cada módulo
  - _Requirements: 7.5, 8.1, 8.3_

- [x] 2. Implementar `ConfigLoader`
  - [x] 2.1 Implementar `loadConfig()` em `docs/showcase/configLoader.js`
    - Fazer `fetch('config.json')` e parsear o JSON retornado
    - Validar presença dos campos obrigatórios (`projectName`, `tagline`, `modules`, `team`, `links`)
    - Retornar `DEFAULT_CONFIG` e emitir `console.warn` se o arquivo estiver ausente (404), malformado (SyntaxError) ou com campos obrigatórios faltando
    - Exportar `DEFAULT_CONFIG` como constante com valores padrão do Tokemize
    - _Requirements: 8.1, 8.4_

  - [ ]* 2.2 Escrever property test para `loadConfig` — round-trip (P15)
    - **Property 15: loadConfig faz round-trip completo de AppConfig**
    - **Validates: Requirements 8.1, 8.3**
    - Usar `fc.record` com todos os campos obrigatórios de `AppConfig`
    - Serializar para JSON, mockar `fetch` para retornar esse JSON e verificar igualdade profunda com o objeto original

  - [ ]* 2.3 Escrever property test para `loadConfig` — fallback para entradas inválidas (P16)
    - **Property 16: loadConfig retorna DEFAULT_CONFIG para entradas inválidas**
    - **Validates: Requirements 8.4**
    - Usar `fc.oneof(fc.constant(null), fc.string(), fc.record({...}))` para gerar entradas inválidas
    - Verificar que `loadConfig()` retorna `DEFAULT_CONFIG` sem lançar exceção

- [x] 3. Implementar `CacheStore`
  - [x] 3.1 Implementar `CacheStore` em `docs/showcase/cacheStore.js`
    - Implementar `get(key)`, `set(key, data)` e `isStale(key, maxAgeMs)` sobre `localStorage`
    - Prefixar todas as chaves com `tokemize_cache_`
    - TTL padrão de 3600000 ms (1 hora)
    - `isStale` retorna `true` se `(Date.now() - entry.timestamp) > maxAgeMs`
    - Tratar `localStorage` indisponível (modo privado) com try/catch silencioso
    - _Requirements: 2.7_

  - [ ]* 3.2 Escrever property test para `CacheStore.isStale` (P3)
    - **Property 3: CacheStore.isStale respeita o TTL de 1 hora**
    - **Validates: Requirements 2.7**
    - Usar `fc.integer({ min: 0, max: Date.now() })` para gerar timestamps
    - Verificar que `isStale` retorna `true` se e somente se `(Date.now() - t) > 3600000`

- [x] 4. Implementar `ApiClient`
  - [x] 4.1 Implementar `ApiClient` em `docs/showcase/apiClient.js`
    - Implementar `fetchRepoStats(owner, repo)` agregando chamadas paralelas à GitHub REST API: commits (`/commits?per_page=1`), PRs (`/pulls?state=all`), contributors (`/contributors`), branches (`/branches`) e último commit na main
    - Implementar `fetchCommitActivity(owner, repo)` usando `/stats/commit_activity` e filtrando as últimas 13 semanas
    - Implementar `fetchAvatarUrl(username)` via `/users/{username}`
    - Usar `AbortController` com timeout configurável (padrão 8s via `config.json`)
    - Lançar `ApiError` (classe definida no design) para status HTTP ≥ 400 ou timeout
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1_

  - [ ]* 4.2 Escrever unit tests para `ApiClient` com mocks de fetch
    - Testar resposta bem-sucedida retorna `RepoStats` corretamente mapeado
    - Testar HTTP 4xx lança `ApiError` com status e endpoint corretos
    - Testar timeout (AbortController) lança `ApiError`
    - _Requirements: 2.6_

- [x] 5. Checkpoint — Verificar módulos base
  - Garantir que `ConfigLoader`, `CacheStore` e `ApiClient` passam em todos os testes
  - Verificar que `config.json` é carregado corretamente no browser (abrir `index.html` localmente)
  - Perguntar ao usuário se há dúvidas antes de prosseguir para os componentes de UI

- [x] 6. Implementar componente `renderHero`
  - [x] 6.1 Implementar `renderHero(config)` em `docs/showcase/components/hero.js`
    - Renderizar `config.projectName` e `config.tagline` na seção `#hero`
    - Renderizar os três problemas de `config.problems` como lista visual
    - Renderizar o fluxo do pipeline `config.pipeline` como sequência visual com setas
    - _Requirements: 5.1, 5.2, 5.3_

  - [ ]* 6.2 Escrever property test para `renderHero` (P10)
    - **Property 10: renderHero exibe todos os campos de conteúdo da hero section**
    - **Validates: Requirements 5.1, 5.2, 5.3**
    - Usar `fc.record` para gerar `AppConfig` com `projectName`, `tagline`, `problems` e `pipeline` arbitrários
    - Verificar que o HTML resultante contém cada valor gerado

- [x] 7. Implementar componente `renderTechStack`
  - [x] 7.1 Implementar `renderTechStack(config)` em `docs/showcase/components/techStack.js`
    - Renderizar cada item de `config.techStack` com `name` como texto visível e `url` como `href` do anchor
    - Adicionar `target="_blank" rel="noopener noreferrer"` em todos os links externos
    - _Requirements: 5.4_

  - [ ]* 7.2 Escrever property test para `renderTechStack` (P11)
    - **Property 11: renderTechStack exibe nome e link de cada tecnologia**
    - **Validates: Requirements 5.4**
    - Usar `fc.array(fc.record({ name: fc.string({ minLength: 1 }), url: fc.webUrl() }), { minLength: 1 })`
    - Verificar que cada `name` aparece como texto e cada `url` aparece como `href`

- [x] 8. Implementar componente `renderStats`
  - [x] 8.1 Implementar `renderStats(stats, stale)` em `docs/showcase/components/stats.js`
    - Renderizar os seis campos de `RepoStats` na seção `#stats`: `totalCommits`, `openPRs`, `closedPRs`, `contributors`, `activeBranches` e `lastCommitAt` formatado
    - Quando `stale=true`, adicionar elemento com `data-stale="true"` e mensagem visual de dados desatualizados
    - Quando `stats` é `null` (cache vazio + API falhou), exibir estado de erro com mensagem amigável
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [ ]* 8.2 Escrever property test para `renderStats` — todos os campos (P1)
    - **Property 1: Stats_Widget renderiza todos os campos de RepoStats**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
    - Usar `fc.record({ totalCommits: fc.nat(), openPRs: fc.nat(), closedPRs: fc.nat(), contributors: fc.nat(), activeBranches: fc.nat(), lastCommitAt: fc.date().map(d => d.toISOString()) })`
    - Verificar que o HTML contém cada valor numérico e a data formatada

  - [ ]* 8.3 Escrever property test para `renderStats` — indicador stale (P2)
    - **Property 2: Indicador de dados desatualizados é exibido quando cache é stale**
    - **Validates: Requirements 2.6**
    - Usar o mesmo `fc.record` de P1 com `stale=true`
    - Verificar que o HTML contém elemento com `data-stale="true"`

- [x] 9. Implementar componente `renderContributionGraph`
  - [x] 9.1 Implementar `renderContributionGraph(activity)` em `docs/showcase/components/contributionGraph.js`
    - Renderizar gráfico de barras SVG com as semanas de `WeeklyActivity[]`
    - Implementar função de mapeamento de cores por autor (uma cor distinta por username)
    - Adicionar `aria-label` descritivo no elemento `<svg>` e `<title>` interno
    - Implementar tooltip `<div role="tooltip">` posicionado via evento `mousemove` em cada barra
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [ ]* 9.2 Escrever property test — filtro das últimas 13 semanas (P4)
    - **Property 4: Contribution_Graph cobre exatamente as últimas 13 semanas**
    - **Validates: Requirements 3.1**
    - Usar `fc.array(fc.record({ week: fc.date().map(d => d.toISOString().slice(0,10)), totalCommits: fc.nat(), byAuthor: fc.dictionary(fc.string(), fc.nat()) }))`
    - Verificar que apenas semanas dentro dos últimos 90 dias são passadas ao renderer

  - [ ]* 9.3 Escrever property test — cores distintas por autor (P5)
    - **Property 5: Contribution_Graph atribui cores distintas por autor**
    - **Validates: Requirements 3.2**
    - Usar `fc.array(fc.string({ minLength: 1 }), { minLength: 1 })` para gerar N autores distintos
    - Verificar que a função de mapeamento de cores retorna N valores distintos

  - [ ]* 9.4 Escrever property test — aria-label não vazio no SVG (P6)
    - **Property 6: Contribution_Graph SVG possui atributo de acessibilidade não vazio**
    - **Validates: Requirements 3.4**
    - Usar `fc.array(weeklyActivityArb)` para gerar dados arbitrários
    - Verificar que o SVG renderizado possui `aria-label` com valor não vazio

  - [ ]* 9.5 Escrever unit test para tooltip do Contribution_Graph
    - Simular evento `mousemove` sobre uma barra do SVG
    - Verificar que o tooltip exibe número de commits e período correspondente
    - _Requirements: 3.3_

- [x] 10. Implementar componente `renderProgressTracker`
  - [x] 10.1 Implementar `calculateProgress(modules)` e `renderProgressTracker(modules)` em `docs/showcase/components/progressTracker.js`
    - `calculateProgress` retorna `(módulos com status "done" / total) * 100`
    - `renderProgressTracker` exibe badge de status por módulo (`done`, `in_progress`, `planned`) e barra de progresso geral
    - Status manual do `config.json` tem prioridade absoluta — não inferir status de outras fontes
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [ ]* 10.2 Escrever property test — label e status de cada módulo (P7)
    - **Property 7: Progress_Tracker renderiza label e status de cada módulo**
    - **Validates: Requirements 4.1, 4.2**
    - Usar `fc.array(fc.record({ id: fc.string(), label: fc.string({ minLength: 1 }), status: fc.constantFrom("done", "in_progress", "planned") }), { minLength: 1 })`
    - Verificar que o HTML contém o `label` e uma representação visual do `status` de cada módulo

  - [ ]* 10.3 Escrever property test — cálculo de percentual (P8)
    - **Property 8: calculateProgress retorna a porcentagem correta de módulos concluídos**
    - **Validates: Requirements 4.3**
    - Usar `fc.array(moduleConfigArb, { minLength: 1 })`
    - Verificar que o resultado é exatamente `(count("done") / total) * 100`

  - [ ]* 10.4 Escrever property test — prioridade do status manual (P9)
    - **Property 9: Status manual tem prioridade absoluta no Progress_Tracker**
    - **Validates: Requirements 4.4**
    - Usar `moduleConfigArb` com status explícito
    - Verificar que o status exibido sempre iguala o valor configurado

- [x] 11. Implementar componente `renderTeam`
  - [x] 11.1 Implementar `renderTeam(members, avatars)` em `docs/showcase/components/team.js`
    - Renderizar nome e link `https://github.com/{member.github}` para cada membro
    - Quando o username está no mapa `avatars`, usar a URL fornecida como `src` do `<img>`
    - Quando o username está ausente do mapa `avatars`, usar caminho de avatar padrão como `src`
    - Adicionar `alt` descritivo em todos os elementos `<img>`
    - _Requirements: 6.1, 6.2, 6.3_

  - [ ]* 11.2 Escrever property test — nome e link GitHub de cada membro (P12)
    - **Property 12: renderTeam exibe nome e link GitHub de cada membro**
    - **Validates: Requirements 6.1**
    - Usar `fc.array(fc.record({ name: fc.string({ minLength: 1 }), github: fc.string({ minLength: 1 }) }), { minLength: 1 })`
    - Verificar que o HTML contém cada `name` e um anchor com `href` igual a `https://github.com/{github}`

  - [ ]* 11.3 Escrever property test — avatar presente (P13)
    - **Property 13: Avatar do membro é exibido quando disponível**
    - **Validates: Requirements 6.2**
    - Usar `teamMemberArb` + `fc.webUrl()` para gerar URL de avatar
    - Verificar que o `<img>` tem `src` igual à URL fornecida no mapa

  - [ ]* 11.4 Escrever property test — avatar padrão quando ausente (P14)
    - **Property 14: Avatar padrão é exibido quando API não está disponível**
    - **Validates: Requirements 6.3**
    - Usar `teamMemberArb` com mapa de avatares vazio
    - Verificar que o `<img>` tem `src` igual ao caminho do avatar padrão

- [x] 12. Checkpoint — Verificar todos os componentes de UI
  - Garantir que todos os testes de componentes passam
  - Verificar renderização visual abrindo `index.html` localmente com dados mockados
  - Perguntar ao usuário se há dúvidas antes de prosseguir para a integração

- [x] 13. Integrar componentes em `app.js`
  - [x] 13.1 Implementar o fluxo de inicialização em `app.js`
    - Carregar `config.json` via `loadConfig()` ao iniciar
    - Para cada chamada à `ApiClient`, consultar `CacheStore` antes de fazer fetch; usar cache se válido (< 1 hora)
    - Chamar `renderHero`, `renderTechStack`, `renderProgressTracker` e `renderTeam` com dados do `config.json` imediatamente (sem esperar API)
    - Chamar `renderStats` e `renderContributionGraph` com dados da API (ou cache); passar `stale=true` quando cache estiver desatualizado
    - Em caso de falha na API com cache vazio, chamar `renderStats(null, false)` para exibir estado de erro
    - _Requirements: 2.6, 2.7, 8.2_

  - [ ]* 13.2 Escrever smoke test de integração
    - Mockar `fetch` para retornar dados realistas do repositório Tokemize
    - Verificar que todos os componentes são renderizados sem erros no DOM
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 4.1, 5.1, 6.1_

- [x] 14. Implementar estilos responsivos e acessibilidade
  - [x] 14.1 Implementar layout responsivo em `style.css`
    - Garantir renderização correta em 1280×720, 1920×1080, 2560×1440 e largura mínima de 375px usando media queries
    - Implementar paleta de cores com razão de contraste ≥ 4.5:1 entre texto e fundo (WCAG 2.1 AA)
    - Otimizar assets para carregamento ≤ 3 segundos em 10 Mbps (sem imagens pesadas, CSS/JS minificados no build)
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [ ]* 14.2 Escrever unit test de contraste de cores WCAG
    - Verificar cada par texto/fundo definido no CSS usando fórmula de luminância relativa
    - Confirmar razão de contraste ≥ 4.5:1 para todos os pares
    - _Requirements: 7.3_

- [x] 15. Criar o workflow de deploy (`deploy.yml`)
  - Criar `.github/workflows/deploy.yml` conforme o design:
    - Trigger: `push` na branch `main`
    - Job com `timeout-minutes: 5` e `permissions: contents: write`
    - Steps: `actions/checkout@v4` → `peaceiris/actions-gh-pages@v4` com `publish_dir: ./docs/showcase` e `keep_files: false`
  - Garantir que falha em qualquer step termina o job com código não-zero sem sobrescrever `gh-pages`
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 16. Checkpoint final — Garantir que tudo está integrado
  - Garantir que todos os testes passam (`npx vitest run` em `docs/showcase/`)
  - Verificar que `config.json` com campos ausentes exibe `DEFAULT_CONFIG` e emite `console.warn`
  - Verificar que o workflow `deploy.yml` está sintaticamente correto (lint com `actionlint` ou validação manual)
  - Perguntar ao usuário se há dúvidas antes de considerar a implementação concluída

## Notes

- Tarefas marcadas com `*` são opcionais e podem ser puladas para um MVP mais rápido
- Cada tarefa referencia requisitos específicos para rastreabilidade
- Os checkpoints garantem validação incremental antes de avançar para a próxima fase
- Os property tests usam fast-check com mínimo de 100 iterações por propriedade (`numRuns: 100`)
- Cada teste PBT deve incluir o comentário: `// Feature: github-pages-project-showcase, Property N: <texto>`
- O site é um Static_Site puro — nenhuma dependência de backend é permitida
- O `config.json` é a única fonte de verdade para conteúdo configurável; status manual de módulos tem prioridade absoluta
