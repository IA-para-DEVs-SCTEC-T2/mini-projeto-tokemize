/**
 * ApiClient — abstração sobre a GitHub REST API.
 * Todas as chamadas usam fetch nativo com AbortController para timeout.
 */

const BASE_URL = 'https://api.github.com';

// ---------------------------------------------------------------------------
// ApiError
// ---------------------------------------------------------------------------

/**
 * Erro lançado quando uma chamada à GitHub API falha (HTTP ≥ 400 ou timeout).
 */
export class ApiError extends Error {
  /**
   * @param {number} status    - Código HTTP (ou 0 para timeout/abort)
   * @param {string} endpoint  - URL do endpoint que falhou
   * @param {string} message   - Mensagem descritiva
   */
  constructor(status, endpoint, message) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.endpoint = endpoint;
  }
}

// ---------------------------------------------------------------------------
// Helpers internos
// ---------------------------------------------------------------------------

/**
 * Executa um fetch com timeout via AbortController.
 * Lança ApiError em caso de timeout ou status HTTP ≥ 400.
 *
 * @param {string} url
 * @param {number} timeout - ms
 * @returns {Promise<Response>}
 */
async function fetchWithTimeout(url, timeout) {
  const controller = new AbortController();
  const timerId = setTimeout(() => controller.abort(), timeout);

  let response;
  try {
    response = await fetch(url, { signal: controller.signal });
  } catch (err) {
    clearTimeout(timerId);
    if (err.name === 'AbortError') {
      throw new ApiError(0, url, `Request timed out after ${timeout}ms: ${url}`);
    }
    throw new ApiError(0, url, `Network error: ${err.message}`);
  }

  clearTimeout(timerId);

  if (!response.ok) {
    throw new ApiError(response.status, url, `HTTP ${response.status} from ${url}`);
  }

  return response;
}

/**
 * Extrai o total de itens a partir do header Link da GitHub API.
 * Técnica: per_page=1 + ler o número da última página no rel="last".
 *
 * @param {Response} response
 * @returns {number}
 */
function parseTotalFromLinkHeader(response) {
  const linkHeader = response.headers.get('Link');
  if (!linkHeader) return 1;
  const match = linkHeader.match(/<[^>]*[?&]page=(\d+)[^>]*>;\s*rel="last"/);
  if (!match) return 1;
  return parseInt(match[1], 10);
}

/**
 * Constrói a URL completa para a GitHub API.
 *
 * @param {string} path
 * @param {Record<string, string|number>} [params]
 * @returns {string}
 */
function buildUrl(path, params = {}) {
  const url = new URL(`${BASE_URL}${path}`);
  for (const [key, value] of Object.entries(params)) {
    url.searchParams.set(key, String(value));
  }
  return url.toString();
}

// ---------------------------------------------------------------------------
// fetchRepoStats
// ---------------------------------------------------------------------------

/**
 * @typedef {Object} RepoStats
 * @property {number} totalCommits
 * @property {number} openPRs
 * @property {number} closedPRs
 * @property {number} contributors
 * @property {number} activeBranches
 * @property {string} lastCommitAt   - ISO 8601
 */

/**
 * Busca estatísticas do repositório na GitHub API.
 * Reutiliza a resposta de /contributors para evitar chamada duplicada.
 *
 * @param {string} owner
 * @param {string} repo
 * @param {number} [timeout=8000]
 * @returns {Promise<{ stats: RepoStats, contributors: Contributor[] }>}
 */
export async function fetchRepoData(owner, repo, timeout = 8000) {
  const base = `/repos/${owner}/${repo}`;

  const commitsUrl      = buildUrl(`${base}/commits`,      { per_page: 1 });
  const openPRsUrl      = buildUrl(`${base}/pulls`,        { state: 'open',   per_page: 1 });
  const closedPRsUrl    = buildUrl(`${base}/pulls`,        { state: 'closed', per_page: 1 });
  const contributorsUrl = buildUrl(`${base}/contributors`, { per_page: 30 }); // body completo, serve para stats e cards
  const branchesUrl     = buildUrl(`${base}/branches`,     { per_page: 1 });
  const lastCommitUrl   = buildUrl(`${base}/commits`,      { sha: 'main', per_page: 1 });

  const [
    commitsRes,
    openPRsRes,
    closedPRsRes,
    contributorsRes,
    branchesRes,
    lastCommitRes,
  ] = await Promise.all([
    fetchWithTimeout(commitsUrl,      timeout),
    fetchWithTimeout(openPRsUrl,      timeout),
    fetchWithTimeout(closedPRsUrl,    timeout),
    fetchWithTimeout(contributorsUrl, timeout),
    fetchWithTimeout(branchesUrl,     timeout),
    fetchWithTimeout(lastCommitUrl,   timeout),
  ]);

  const totalCommits   = parseTotalFromLinkHeader(commitsRes);
  const openPRs        = parseTotalFromLinkHeader(openPRsRes);
  const closedPRs      = parseTotalFromLinkHeader(closedPRsRes);
  const activeBranches = parseTotalFromLinkHeader(branchesRes);

  // Lê o body de contributors uma única vez — serve para contar e para os cards
  const contributorsData = await contributorsRes.json();
  const contributorsList = Array.isArray(contributorsData) ? contributorsData : [];

  // Conta pelo Link header se houver mais de 30; senão usa o tamanho do array
  const contributorsTotal = parseTotalFromLinkHeader(contributorsRes) > 1
    ? parseTotalFromLinkHeader(contributorsRes)
    : contributorsList.length;

  const lastCommitData = await lastCommitRes.json();
  const lastCommitAt = Array.isArray(lastCommitData) && lastCommitData.length > 0
    ? lastCommitData[0]?.commit?.author?.date ?? new Date(0).toISOString()
    : new Date(0).toISOString();

  const stats = {
    totalCommits,
    openPRs,
    closedPRs,
    contributors: contributorsTotal,
    activeBranches,
    lastCommitAt,
  };

  const contributors = contributorsList.map((c) => ({
    login:         c.login ?? 'unknown',
    contributions: c.contributions ?? 0,
    avatar_url:    c.avatar_url ?? '',
    html_url:      c.html_url ?? `https://github.com/${c.login}`,
  }));

  return { stats, contributors };
}

// Mantidos para compatibilidade com testes existentes
export async function fetchRepoStats(owner, repo, timeout = 8000) {
  const { stats } = await fetchRepoData(owner, repo, timeout);
  return stats;
}

// ---------------------------------------------------------------------------
// fetchPRsByAuthor
// ---------------------------------------------------------------------------

/**
 * @typedef {Object} PRAuthor
 * @property {string} login
 * @property {number} total      - total de PRs (abertos + fechados)
 * @property {number} open
 * @property {number} closed
 * @property {string} avatar_url
 * @property {string} html_url
 */

/**
 * Busca todos os PRs (abertos + fechados) e agrupa por autor.
 * Usa per_page=100 para minimizar chamadas.
 *
 * @param {string} owner
 * @param {string} repo
 * @param {number} [timeout=8000]
 * @returns {Promise<PRAuthor[]>}
 */
export async function fetchPRsByAuthor(owner, repo, timeout = 8000) {
  const url = buildUrl(`/repos/${owner}/${repo}/pulls`, {
    state: 'all',
    per_page: 100,
  });

  const response = await fetchWithTimeout(url, timeout);
  const data = await response.json();

  if (!Array.isArray(data)) return [];

  /** @type {Map<string, PRAuthor>} */
  const authorMap = new Map();

  for (const pr of data) {
    const login      = pr?.user?.login ?? 'unknown';
    const avatarUrl  = pr?.user?.avatar_url ?? '';
    const htmlUrl    = pr?.user?.html_url ?? `https://github.com/${login}`;
    const isOpen     = pr?.state === 'open';

    if (!authorMap.has(login)) {
      authorMap.set(login, { login, total: 0, open: 0, closed: 0, avatar_url: avatarUrl, html_url: htmlUrl });
    }

    const entry = authorMap.get(login);
    entry.total  += 1;
    if (isOpen) entry.open   += 1;
    else        entry.closed += 1;
  }

  // Ordena por total decrescente
  return [...authorMap.values()].sort((a, b) => b.total - a.total);
}

// ---------------------------------------------------------------------------
// fetchCommitActivity (mantido para compatibilidade com testes)
// ---------------------------------------------------------------------------

/**
 * @typedef {Object} WeeklyActivity
 * @property {string} week          - ISO date string do início da semana (YYYY-MM-DD)
 * @property {number} totalCommits
 * @property {Object} byAuthor      - Mapa de author login → número de commits
 */

/**
 * Retorna a data de início (segunda-feira) da semana de uma data.
 *
 * @param {Date} date
 * @returns {string} Data no formato YYYY-MM-DD
 */
function getWeekStart(date) {
  const d = new Date(date);
  const day = d.getUTCDay();
  const diff = (day === 0 ? -6 : 1 - day);
  d.setUTCDate(d.getUTCDate() + diff);
  return d.toISOString().split('T')[0];
}

/**
 * Busca a atividade de commits das últimas 13 semanas diretamente do endpoint
 * de commits, agrupando por semana no cliente.
 *
 * Mais confiável que /stats/commit_activity, que retorna 202 enquanto o
 * GitHub calcula os dados em background.
 *
 * @param {string} owner
 * @param {string} repo
 * @param {number} [timeout=8000]
 * @returns {Promise<WeeklyActivity[]>}
 */
export async function fetchCommitActivity(owner, repo, timeout = 8000) {
  const since = new Date();
  since.setUTCDate(since.getUTCDate() - 91);
  const sinceIso = since.toISOString();

  const url = buildUrl(`/repos/${owner}/${repo}/commits`, {
    since: sinceIso,
    per_page: 100,
  });

  const response = await fetchWithTimeout(url, timeout);
  const data = await response.json();

  if (!Array.isArray(data) || data.length === 0) return [];

  /** @type {Map<string, { totalCommits: number, byAuthor: Record<string, number> }>} */
  const weekMap = new Map();

  for (const commit of data) {
    const dateStr = commit?.commit?.author?.date ?? commit?.commit?.committer?.date;
    if (!dateStr) continue;

    const weekKey = getWeekStart(new Date(dateStr));
    const author = commit?.author?.login ?? commit?.commit?.author?.name ?? 'unknown';

    if (!weekMap.has(weekKey)) {
      weekMap.set(weekKey, { totalCommits: 0, byAuthor: {} });
    }

    const entry = weekMap.get(weekKey);
    entry.totalCommits += 1;
    entry.byAuthor[author] = (entry.byAuthor[author] ?? 0) + 1;
  }

  // Gera todas as 13 semanas (com zeros para semanas sem commits)
  const uniqueWeeks = [];
  for (let i = 12; i >= 0; i--) {
    const d = new Date();
    d.setUTCDate(d.getUTCDate() - i * 7);
    const w = getWeekStart(d);
    if (!uniqueWeeks.includes(w)) uniqueWeeks.push(w);
  }
  uniqueWeeks.sort();

  return uniqueWeeks.map((week) => {
    const entry = weekMap.get(week) ?? { totalCommits: 0, byAuthor: {} };
    return { week, totalCommits: entry.totalCommits, byAuthor: entry.byAuthor };
  });
}

// ---------------------------------------------------------------------------
// fetchAvatarUrl
// ---------------------------------------------------------------------------

/**
 * Busca a URL do avatar de um usuário do GitHub.
 *
 * @param {string} username
 * @param {number} [timeout=8000]
 * @returns {Promise<string>}
 */
export async function fetchAvatarUrl(username, timeout = 8000) {
  const url = buildUrl(`/users/${username}`);
  const response = await fetchWithTimeout(url, timeout);
  const data = await response.json();
  return data.avatar_url;
}
