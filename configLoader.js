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

/** Campos obrigatórios que devem estar presentes no config.json */
const REQUIRED_FIELDS = ['projectName', 'tagline', 'modules', 'team', 'links'];

/**
 * Configuração padrão do Tokemize.
 * Usada como fallback quando config.json está ausente, malformado ou incompleto.
 *
 * @type {AppConfig}
 */
export const DEFAULT_CONFIG = {
  projectName: 'Tokemize',
  tagline: 'Otimização de contexto para LLMs',
  repo: {
    owner: 'tokemize-org',
    name: 'tokemize',
    apiTimeout: 8000,
  },
  problems: [
    'Contexto demais em prompts técnicos',
    'Prompts longos e difíceis de revisar',
    'Uso ineficiente de tokens',
  ],
  pipeline: ['Repositório + tarefa', 'Tokemize', 'Contexto compacto', 'Prompt otimizado'],
  techStack: [
    { name: 'Python', url: 'https://docs.python.org/3/' },
    { name: 'Tree-sitter', url: 'https://tree-sitter.github.io/tree-sitter/' },
    { name: 'FAISS', url: 'https://faiss.ai/index.html' },
    { name: 'Typer', url: 'https://typer.tiangolo.com/' },
    { name: 'pyperclip', url: 'https://pyperclip.readthedocs.io/' },
  ],
  modules: [
    { id: 'repository-analyzer', label: 'Repository Analyzer', status: 'done' },
    { id: 'intelligent-selector', label: 'Intelligent Selector', status: 'done' },
    { id: 'compressor', label: 'Compressor', status: 'done' },
    { id: 'context-store', label: 'Context Store', status: 'done' },
    { id: 'prompt-builder', label: 'Prompt Builder', status: 'done' },
    { id: 'clipboard-output', label: 'Clipboard/Output', status: 'done' },
  ],
  team: [
    { name: 'Eneri da Costa Junior',      github: 'jrcosta'          },
    { name: 'Guilherme Valerio Mertens',  github: 'gvmertens'        },
    { name: 'Paulo Sergio',               github: 'PauloSergioLR'    },
    { name: 'Samuel Magalhães Marques',   github: 'samuelmarquesgit' },
    { name: 'Eduardo Notari',             github: 'edunotari'        },
  ],
  links: {
    repo: 'https://github.com/tokemize-org/tokemize',
    readme: 'https://github.com/tokemize-org/tokemize#readme',
  },
};

/**
 * Valida se o objeto de configuração possui todos os campos obrigatórios.
 *
 * @param {unknown} config - Objeto a ser validado
 * @returns {boolean} `true` se todos os campos obrigatórios estiverem presentes
 */
function hasRequiredFields(config) {
  if (config === null || typeof config !== 'object') return false;
  return REQUIRED_FIELDS.every((field) => field in config);
}

/**
 * Carrega e valida o arquivo `config.json`.
 *
 * Comportamento de fallback (retorna `DEFAULT_CONFIG` + emite `console.warn`):
 * - Arquivo ausente (response.ok === false / 404)
 * - JSON malformado (SyntaxError no parse)
 * - Campos obrigatórios faltando
 *
 * @returns {Promise<AppConfig>} Configuração carregada ou `DEFAULT_CONFIG`
 */
export async function loadConfig() {
  let response;

  try {
    response = await fetch('config.json');
  } catch (networkError) {
    console.warn(
      '[ConfigLoader] Falha ao buscar config.json (erro de rede). Usando DEFAULT_CONFIG.',
      networkError,
    );
    return DEFAULT_CONFIG;
  }

  if (!response.ok) {
    console.warn(
      `[ConfigLoader] config.json não encontrado (HTTP ${response.status}). Usando DEFAULT_CONFIG.`,
    );
    return DEFAULT_CONFIG;
  }

  let parsed;
  try {
    parsed = await response.json();
  } catch (syntaxError) {
    console.warn(
      '[ConfigLoader] config.json contém JSON malformado. Usando DEFAULT_CONFIG.',
      syntaxError,
    );
    return DEFAULT_CONFIG;
  }

  if (!hasRequiredFields(parsed)) {
    const missing = REQUIRED_FIELDS.filter((f) => !(f in (parsed ?? {})));
    console.warn(
      `[ConfigLoader] config.json está faltando campos obrigatórios: ${missing.join(', ')}. Usando DEFAULT_CONFIG.`,
    );
    return DEFAULT_CONFIG;
  }

  return parsed;
}
