# Design Document — GitHub Pages Project Showcase

## Overview

A Showcase_Page do Tokemize é um site estático (HTML + CSS + JavaScript puro) hospedado no GitHub Pages. Seu objetivo é apresentar o projeto de forma visual e profissional, exibindo estatísticas em tempo real do repositório, progresso de desenvolvimento por módulo, proposta de valor e membros da equipe.

A página não possui backend próprio. Todos os dados dinâmicos são obtidos diretamente da GitHub REST API pública no lado do cliente (browser). O conteúdo configurável é lido de um arquivo `config.json` estático. O deploy é totalmente automatizado via GitHub Actions a cada push na branch `main`.

### Objetivos de Design

- **Zero dependência de backend**: toda a lógica roda no browser.
- **Configuração declarativa**: conteúdo editável via `config.json` sem tocar no HTML.
- **Resiliência a falhas de API**: cache local (localStorage) garante exibição mesmo offline.
- **Performance**: carregamento completo em ≤ 3 segundos em 10 Mbps.
- **Acessibilidade**: WCAG 2.1 AA (contraste ≥ 4.5:1, texto alternativo em gráficos).

---

## Architecture

### Visão Geral

```
┌─────────────────────────────────────────────────────────────┐
│                        GitHub Pages                         │
│                                                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌─────────┐  │
│  │ index.html│   │ style.css│   │  app.js  │   │config.  │  │
│  │  (shell) │   │ (design) │   │ (lógica) │   │  json   │  │
│  └──────────┘   └──────────┘   └──────────┘   └─────────┘  │
│                        │                                    │
│              ┌──────────▼──────────┐                        │
│              │   Module Loader     │                        │
│              │  (ES Modules / IIFE)│                        │
│              └──────────┬──────────┘                        │
│         ┌───────────────┼───────────────┐                   │
│         ▼               ▼               ▼                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ ConfigLoader│ │  ApiClient  │ │  CacheStore │           │
│  └─────────────┘ └──────┬──────┘ └─────────────┘           │
│                         │                                   │
└─────────────────────────┼───────────────────────────────────┘
                          │ fetch()
                          ▼
                 ┌─────────────────┐
                 │  GitHub REST API│
                 │  (api.github.com│
                 │   /repos/...)   │
                 └─────────────────┘
```

### Fluxo de Dados

1. Browser carrega `index.html` → referencia `style.css` e `app.js`.
2. `app.js` faz `fetch('config.json')` → popula conteúdo estático (nome, tagline, módulos, membros).
3. `ApiClient` faz chamadas paralelas à GitHub API para buscar commits, PRs, contribuidores, branches e avatares.
4. `CacheStore` (localStorage) é consultado antes de cada chamada à API; se o cache for válido (< 1 hora), os dados em cache são usados diretamente.
5. Cada componente de UI recebe os dados e renderiza seu fragmento HTML/SVG.
6. Em caso de falha na API, o componente exibe os dados em cache com indicador visual de desatualização.

### Deploy Pipeline

```
push → main
    └─► GitHub Actions (deploy.yml)
            ├── checkout
            ├── build (copy/minify assets)
            └── deploy → gh-pages branch
                    └─► GitHub Pages serve
```

---

## Components and Interfaces

### 1. `ConfigLoader`

Responsável por carregar e validar o `config.json`.

```javascript
/**
 * @typedef {Object} ModuleConfig
 * @property {string} id        - Identificador do módulo (ex: "parser")
 * @property {string} label     - Nome de exibição
 * @property {"done"|"in_progress"|"planned"} status - Status manual
 */

/**
 * @typedef {Object} TeamMember
 * @property {string} name       - Nome completo
 * @property {string} github     - Username do GitHub
 * @property {string} [avatar]   - URL de avatar (opcional; fallback para API)
 */

/**
 * @typedef {Object} AppConfig
 * @property {string}         projectName
 * @property {string}         tagline
 * @property {ModuleConfig[]} modules
 * @property {TeamMember[]}   team
 * @property {Object}         links       - Links externos (docs, repo, etc.)
 */

async function loadConfig(): Promise<AppConfig>
```

- Se `config.json` estiver ausente ou malformado, retorna `DEFAULT_CONFIG` e emite `console.warn`.

---

### 2. `ApiClient`

Abstração sobre a GitHub REST API. Todas as chamadas são feitas com `fetch` nativo.

```javascript
/**
 * @typedef {Object} RepoStats
 * @property {number} totalCommits
 * @property {number} openPRs
 * @property {number} closedPRs
 * @property {number} contributors
 * @property {number} activeBranches
 * @property {string} lastCommitAt   - ISO 8601
 */

async function fetchRepoStats(owner: string, repo: string): Promise<RepoStats>
async function fetchCommitActivity(owner: string, repo: string): Promise<WeeklyActivity[]>
async function fetchAvatarUrl(username: string): Promise<string>
```

- Todas as funções lançam `ApiError` em caso de falha HTTP (status ≥ 400 ou timeout).
- Timeout configurável via `config.json` (padrão: 8 segundos).

---

### 3. `CacheStore`

Camada de cache sobre `localStorage`.

```javascript
/**
 * @typedef {Object} CacheEntry<T>
 * @property {T}      data
 * @property {number} timestamp  - Unix ms
 */

function get<T>(key: string): T | null
function set<T>(key: string, data: T): void
function isStale(key: string, maxAgeMs: number): boolean
```

- TTL padrão: 3600000 ms (1 hora), alinhado ao requisito 2.7.
- Chaves prefixadas com `tokemize_cache_` para evitar colisões.

---

### 4. Componentes de UI

Cada componente é uma função pura que recebe dados e retorna/atualiza um fragmento do DOM.

| Componente | Elemento alvo | Dados de entrada |
|---|---|---|
| `renderHero(config)` | `#hero` | `AppConfig` |
| `renderStats(stats, stale)` | `#stats` | `RepoStats`, `boolean` |
| `renderContributionGraph(activity)` | `#contribution-graph` | `WeeklyActivity[]` |
| `renderProgressTracker(modules)` | `#progress` | `ModuleConfig[]` |
| `renderTeam(members, avatars)` | `#team` | `TeamMember[]`, `Map<string,string>` |
| `renderPipeline(config)` | `#pipeline` | `AppConfig` |
| `renderTechStack(config)` | `#tech-stack` | `AppConfig` |

---

### 5. `ContributionGraph`

Renderiza um gráfico de barras SVG com atividade semanal de commits.

- Dados: array de `{ week: string, commits: number, byAuthor: Record<string, number> }` (últimas 13 semanas ≈ 90 dias).
- Tooltip: elemento `<div role="tooltip">` posicionado via `mousemove`.
- Acessibilidade: `<svg aria-label="Gráfico de contribuições: X commits nas últimas 13 semanas">` + `<title>` interno.

---

### 6. `ProgressTracker`

Calcula e exibe o progresso por módulo.

```
percentual = (módulos com status "done" / total de módulos) × 100
```

- Status manual em `config.json` tem prioridade absoluta (requisito 4.4).
- Exibe barra de progresso geral + badge de status por módulo.

---

### 7. Deploy Workflow (`deploy.yml`)

```yaml
name: Deploy GitHub Pages

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs/showcase
          keep_files: false
```

- Em caso de falha no build, o workflow termina com `exit 1` sem sobrescrever o branch `gh-pages`.
- Timeout de 5 minutos alinhado ao requisito 1.2.

---

## Data Models

### `config.json` — Estrutura Completa

```json
{
  "projectName": "Tokemize",
  "tagline": "Uma camada intermediária que melhora como usamos IA",
  "repo": {
    "owner": "tokemize-org",
    "name": "tokemize",
    "apiTimeout": 8000
  },
  "problems": [
    "Alto custo de tokens",
    "Respostas imprecisas e alucinações",
    "Processamento ineficiente"
  ],
  "pipeline": ["Entrada Bruta", "Tokemize", "Entrada Otimizada"],
  "techStack": [
    { "name": "Python", "url": "https://docs.python.org/3/" },
    { "name": "Tree-sitter", "url": "https://tree-sitter.github.io/tree-sitter/" },
    { "name": "FAISS", "url": "https://faiss.ai/index.html" },
    { "name": "OpenAI API", "url": "https://platform.openai.com/docs" },
    { "name": "Anthropic API", "url": "https://docs.anthropic.com" }
  ],
  "modules": [
    { "id": "parser",                "label": "Parser",              "status": "in_progress" },
    { "id": "indexer",               "label": "Indexer",             "status": "in_progress" },
    { "id": "selector",              "label": "Selector",            "status": "planned"     },
    { "id": "optimizer",             "label": "Optimizer",           "status": "planned"     },
    { "id": "integrations/llm",      "label": "LLM Integration",     "status": "in_progress" },
    { "id": "integrations/embeddings","label": "Embeddings",         "status": "planned"     }
  ],
  "team": [
    { "name": "Eneri da Costa Junior",       "github": "jrcosta"          },
    { "name": "Guilherme Valerio Mertens",   "github": "gvmertens"        },
    { "name": "Paulo Sergio",                "github": "PauloSergioLR"    },
    { "name": "Samuel Magalhães Marques",    "github": "samuelmarquesgit" },
    { "name": "Eduardo Notari",              "github": "edunotari"        }
  ],
  "links": {
    "repo": "https://github.com/tokemize-org/tokemize",
    "readme": "https://github.com/tokemize-org/tokemize#readme"
  }
}
```

### `WeeklyActivity`

```typescript
interface WeeklyActivity {
  week: string;           // ISO date do início da semana (ex: "2025-01-06")
  totalCommits: number;
  byAuthor: Record<string, number>; // { "username": commitCount }
}
```

### `CacheEntry<T>`

```typescript
interface CacheEntry<T> {
  data: T;
  timestamp: number;  // Date.now()
}
```

### `ApiError`

```typescript
class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly endpoint: string,
    message: string
  ) { super(message); }
}
```

---

## Correctness Properties


*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Stats_Widget renderiza todos os campos de RepoStats

*For any* `RepoStats` object, `renderStats(stats, stale)` SHALL produce HTML containing the values of `totalCommits`, `openPRs`, `closedPRs`, `contributors`, `activeBranches`, and a formatted representation of `lastCommitAt`.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

---

### Property 2: Indicador de dados desatualizados é exibido quando cache é stale

*For any* `RepoStats` object, when `renderStats(stats, stale=true)` is called, the rendered HTML SHALL contain a stale-indicator element (e.g., an element with `data-stale="true"` or a specific CSS class).

**Validates: Requirements 2.6**

---

### Property 3: CacheStore.isStale respeita o TTL de 1 hora

*For any* cache entry timestamp `t` and `maxAge = 3600000` ms, `isStale(key, maxAge)` SHALL return `true` if and only if `(Date.now() - t) > maxAge`.

**Validates: Requirements 2.7**

---

### Property 4: Contribution_Graph cobre exatamente as últimas 13 semanas

*For any* commit activity array, the data passed to the graph renderer SHALL contain only weeks whose start date falls within the last 90 days (≈ 13 weeks) relative to the current date.

**Validates: Requirements 3.1**

---

### Property 5: Contribution_Graph atribui cores distintas por autor

*For any* `WeeklyActivity` array with N distinct author usernames, the color mapping function SHALL assign N distinct color values — one per author.

**Validates: Requirements 3.2**

---

### Property 6: Contribution_Graph SVG possui atributo de acessibilidade não vazio

*For any* `WeeklyActivity` array, the SVG element rendered by `renderContributionGraph` SHALL have a non-empty `aria-label` attribute describing the graph content.

**Validates: Requirements 3.4**

---

### Property 7: Progress_Tracker renderiza label e status de cada módulo

*For any* non-empty array of `ModuleConfig` objects, `renderProgressTracker(modules)` SHALL produce HTML containing each module's `label` and a visual representation of its `status`.

**Validates: Requirements 4.1, 4.2**

---

### Property 8: calculateProgress retorna a porcentagem correta de módulos concluídos

*For any* non-empty array of `ModuleConfig` objects, `calculateProgress(modules)` SHALL return `(count of modules with status "done" / modules.length) * 100`.

**Validates: Requirements 4.3**

---

### Property 9: Status manual tem prioridade absoluta no Progress_Tracker

*For any* `ModuleConfig` with an explicit `status` field, the status displayed by `renderProgressTracker` SHALL always equal the configured value, regardless of any other input or inferred state.

**Validates: Requirements 4.4**

---

### Property 10: renderHero exibe todos os campos de conteúdo da hero section

*For any* `AppConfig`, `renderHero(config)` SHALL produce HTML containing `config.projectName`, `config.tagline`, each string in `config.problems`, and each step in `config.pipeline`.

**Validates: Requirements 5.1, 5.2, 5.3**

---

### Property 11: renderTechStack exibe nome e link de cada tecnologia

*For any* `AppConfig` with a non-empty `techStack` array, `renderTechStack(config)` SHALL produce HTML containing each technology's `name` as visible text and its `url` as an anchor `href`.

**Validates: Requirements 5.4**

---

### Property 12: renderTeam exibe nome e link GitHub de cada membro

*For any* array of `TeamMember` objects, `renderTeam(members, avatars)` SHALL produce HTML containing each member's `name` and an anchor with `href` equal to `https://github.com/{member.github}`.

**Validates: Requirements 6.1**

---

### Property 13: Avatar do membro é exibido quando disponível

*For any* `TeamMember` and a non-null avatar URL in the avatars map, `renderTeam` SHALL produce an `<img>` element with `src` equal to the provided avatar URL for that member.

**Validates: Requirements 6.2**

---

### Property 14: Avatar padrão é exibido quando API não está disponível

*For any* `TeamMember` whose username is absent from the avatars map (or the map is empty), `renderTeam` SHALL produce an `<img>` element with `src` equal to the default avatar path.

**Validates: Requirements 6.3**

---

### Property 15: loadConfig faz round-trip completo de AppConfig

*For any* valid `AppConfig` object containing all required fields (`projectName`, `tagline`, `modules`, `team`, `links`), serializing it to JSON and loading it via `loadConfig()` SHALL return an object deeply equal to the original.

**Validates: Requirements 8.1, 8.3**

---

### Property 16: loadConfig retorna DEFAULT_CONFIG para entradas inválidas

*For any* input that is `null`, `undefined`, an empty string, syntactically invalid JSON, or a JSON object missing required fields, `loadConfig()` SHALL return `DEFAULT_CONFIG` without throwing an exception.

**Validates: Requirements 8.4**

---

## Error Handling

### Falhas na GitHub API

| Cenário | Comportamento |
|---|---|
| HTTP 4xx / 5xx | `ApiClient` lança `ApiError`; componente usa dados do cache |
| Timeout (> 8s) | `fetch` é abortado via `AbortController`; `ApiError` é lançado |
| Cache vazio + API falhou | Componente exibe estado de erro com mensagem amigável |
| Cache stale + API falhou | Dados em cache são exibidos com indicador visual de desatualização |

### Falhas no config.json

| Cenário | Comportamento |
|---|---|
| Arquivo ausente (404) | `loadConfig()` retorna `DEFAULT_CONFIG`; `console.warn` emitido |
| JSON malformado | `JSON.parse` lança `SyntaxError`; capturado, retorna `DEFAULT_CONFIG` |
| Campos obrigatórios ausentes | Validação de schema retorna `DEFAULT_CONFIG` para campos faltantes |

### Falhas no Deploy

- O workflow usa `peaceiris/actions-gh-pages` com `keep_files: false` apenas após build bem-sucedido.
- Se qualquer step falhar, o job termina com código de saída não-zero e o branch `gh-pages` não é modificado.
- Erros são visíveis nos logs do GitHub Actions (requisito 1.3).

---

## Testing Strategy

### Abordagem Dual

A estratégia combina testes de exemplo (unit tests) para comportamentos específicos e testes baseados em propriedades (property-based tests) para verificar invariantes universais.

### Property-Based Testing

**Biblioteca**: [fast-check](https://fast-check.dev/) (JavaScript) — escolhida por ser a biblioteca PBT mais madura para o ecossistema JS/TS, com suporte a geradores arbitrários complexos e shrinking automático.

**Configuração**: mínimo de 100 iterações por propriedade (`numRuns: 100`).

**Tag de referência**: cada teste deve incluir um comentário no formato:
```
// Feature: github-pages-project-showcase, Property N: <texto da propriedade>
```

**Propriedades implementadas como testes PBT** (uma por propriedade):

| Propriedade | Função testada | Arbitrários |
|---|---|---|
| P1 | `renderStats` | `fc.record({ totalCommits: fc.nat(), openPRs: fc.nat(), ... })` |
| P2 | `renderStats` (stale) | mesmo record + `stale=true` |
| P3 | `CacheStore.isStale` | `fc.integer()` para timestamp |
| P4 | filtro de semanas | `fc.array(weeklyActivityArb)` |
| P5 | mapeamento de cores | `fc.array(fc.string(), { minLength: 1 })` para autores |
| P6 | `renderContributionGraph` | `fc.array(weeklyActivityArb)` |
| P7 | `renderProgressTracker` | `fc.array(moduleConfigArb, { minLength: 1 })` |
| P8 | `calculateProgress` | `fc.array(moduleConfigArb, { minLength: 1 })` |
| P9 | `renderProgressTracker` (prioridade) | `moduleConfigArb` com status explícito |
| P10 | `renderHero` | `appConfigArb` |
| P11 | `renderTechStack` | `appConfigArb` com techStack não vazio |
| P12 | `renderTeam` | `fc.array(teamMemberArb, { minLength: 1 })` |
| P13 | `renderTeam` (avatar presente) | `teamMemberArb` + `fc.webUrl()` |
| P14 | `renderTeam` (avatar ausente) | `teamMemberArb` + mapa vazio |
| P15 | `loadConfig` round-trip | `appConfigArb` |
| P16 | `loadConfig` fallback | `fc.oneof(fc.constant(null), fc.string(), invalidJsonArb)` |

### Unit Tests (Testes de Exemplo)

Focados em cenários específicos não cobertos pelas propriedades:

- Tooltip do `ContributionGraph` ao passar o cursor (requisito 3.3) — simula evento `mousemove`.
- Contraste de cores WCAG 2.1 AA (requisito 7.3) — verifica cada par texto/fundo definido no CSS.
- Renderização com dados reais do repositório Tokemize (smoke test de integração).

### Testes de Integração / Smoke

- Verificar que o workflow de deploy é acionado por push na `main`.
- Verificar que a URL do GitHub Pages retorna HTTP 200 após deploy.
- Verificar que falha no build não sobrescreve o branch `gh-pages`.
- Verificar tempo de carregamento com Lighthouse (≤ 3s em 10 Mbps).

### Estrutura de Arquivos de Teste

```
docs/showcase/
├── index.html
├── style.css
├── config.json
├── app.js
└── __tests__/
    ├── configLoader.test.js      # P15, P16 + unit tests
    ├── apiClient.test.js         # mocks de fetch
    ├── cacheStore.test.js        # P3
    ├── renderStats.test.js       # P1, P2
    ├── renderContributionGraph.test.js  # P4, P5, P6 + tooltip example
    ├── renderProgressTracker.test.js    # P7, P8, P9
    ├── renderHero.test.js        # P10
    ├── renderTechStack.test.js   # P11
    └── renderTeam.test.js        # P12, P13, P14
```
