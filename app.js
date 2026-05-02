/**
 * app.js — Entry point da Showcase_Page do Tokemize
 *
 * Fluxo de inicialização:
 * 1. Carregar config.json via loadConfig()
 * 2. Renderizar seções estáticas IMEDIATAMENTE (hero, pipeline, techStack, progress, team)
 *    sem esperar pela API
 * 3. Para stats e contribution graph:
 *    a. Verificar CacheStore antes de chamar a API
 *    b. Se cache válido (< 1 hora): usar dados do cache, stale=false
 *    c. Se cache stale: chamar API, atualizar cache, stale=false
 *    d. Se API falhar com cache stale: usar cache, stale=true
 *    e. Se API falhar sem cache: renderStats(null, false) — estado de erro
 * 4. Para avatares da equipe:
 *    a. Buscar avatares de todos os membros via fetchAvatarUrl
 *    b. Montar Map<string, string> e re-renderizar equipe com avatares
 *    c. Se falhar, manter renderização sem avatares (fallback já está no renderTeam)
 *
 * Requirements: 2.6, 2.7, 8.2
 */

import { loadConfig }          from './configLoader.js';
import { CacheStore, DEFAULT_TTL } from './cacheStore.js';
import { fetchRepoStats, fetchCommitActivity, fetchAvatarUrl } from './apiClient.js';

import { renderHero }              from './components/hero.js';
import { renderStats }             from './components/stats.js';
import { renderContributionGraph } from './components/contributionGraph.js';
import { renderProgressTracker }   from './components/progressTracker.js';
import { renderTechStack }         from './components/techStack.js';
import { renderTeam }              from './components/team.js';

// Chaves de cache
const CACHE_KEY_STATS    = 'repo_stats';
const CACHE_KEY_ACTIVITY = 'commit_activity';

const cache = new CacheStore();

/**
 * Carrega e renderiza as estatísticas do repositório.
 * Consulta o CacheStore antes de chamar a API.
 *
 * @param {string} owner
 * @param {string} repo
 * @param {number} timeout
 * @param {Object|null} boardMetrics - Métricas do board vindas do config.json
 */
async function loadAndRenderStats(owner, repo, timeout, boardMetrics = null) {
  const isStale = cache.isStale(CACHE_KEY_STATS, DEFAULT_TTL);

  if (!isStale) {
    // Cache válido — usar diretamente, sem chamar a API
    const cached = cache.get(CACHE_KEY_STATS);
    renderStats(cached, false, boardMetrics);
    return;
  }

  // Cache stale ou ausente — tentar a API
  try {
    const stats = await fetchRepoStats(owner, repo, timeout);
    cache.set(CACHE_KEY_STATS, stats);
    renderStats(stats, false, boardMetrics);
  } catch (err) {
    // API falhou — verificar se há cache stale disponível
    const cached = cache.get(CACHE_KEY_STATS);
    if (cached !== null) {
      // Cache stale disponível: exibir com indicador de desatualização
      renderStats(cached, true, boardMetrics);
    } else {
      // Sem cache e API falhou: exibir estado de erro
      renderStats(null, false, boardMetrics);
    }
  }
}

/**
 * Carrega e renderiza o gráfico de contribuições.
 * Consulta o CacheStore antes de chamar a API.
 *
 * @param {string} owner
 * @param {string} repo
 * @param {number} timeout
 */
async function loadAndRenderContributionGraph(owner, repo, timeout) {
  const isStale = cache.isStale(CACHE_KEY_ACTIVITY, DEFAULT_TTL);

  if (!isStale) {
    // Cache válido — usar diretamente
    const cached = cache.get(CACHE_KEY_ACTIVITY);
    renderContributionGraph(cached);
    return;
  }

  // Cache stale ou ausente — tentar a API
  try {
    const activity = await fetchCommitActivity(owner, repo, timeout);
    cache.set(CACHE_KEY_ACTIVITY, activity);
    renderContributionGraph(activity);
  } catch (err) {
    // API falhou — verificar se há cache stale disponível
    const cached = cache.get(CACHE_KEY_ACTIVITY);
    if (cached !== null) {
      renderContributionGraph(cached);
    }
    // Se não há cache, o gráfico permanece vazio (sem renderização de erro específica)
  }
}

/**
 * Busca avatares de todos os membros da equipe e re-renderiza a seção de equipe.
 * Se qualquer avatar falhar, o membro usa o avatar padrão (fallback no renderTeam).
 *
 * @param {import('./configLoader.js').TeamMember[]} members
 * @param {number} timeout
 */
async function loadAndRenderTeamAvatars(members, timeout) {
  const avatarEntries = await Promise.allSettled(
    members.map(async (member) => {
      const url = await fetchAvatarUrl(member.github, timeout);
      return [member.github, url];
    }),
  );

  /** @type {Map<string, string>} */
  const avatars = new Map();
  for (const result of avatarEntries) {
    if (result.status === 'fulfilled') {
      const [username, url] = result.value;
      avatars.set(username, url);
    }
    // Membros com falha ficam fora do mapa → renderTeam usa avatar padrão
  }

  renderTeam(members, avatars);
}

/**
 * Ponto de entrada principal da Showcase_Page.
 * Orquestra o carregamento de configuração, renderização estática e chamadas à API.
 */
async function init() {
  // ── 1. Carregar configuração ──────────────────────────────────────────────
  const config = await loadConfig();

  const owner   = config.repo?.owner   ?? 'tokemize-org';
  const repo    = config.repo?.name    ?? 'tokemize';
  const timeout = config.repo?.apiTimeout ?? 8000;

  // ── 2. Renderizar seções estáticas IMEDIATAMENTE ──────────────────────────
  // Não aguarda a API — o usuário vê o conteúdo estático instantaneamente.
  renderHero(config);
  renderTechStack(config);
  renderProgressTracker(config.modules);

  // Renderização inicial da equipe sem avatares (fallback para avatar padrão)
  renderTeam(config.team, new Map());

  // ── 3. Carregar dados dinâmicos da API (ou cache) em paralelo ─────────────
  await Promise.allSettled([
    loadAndRenderStats(owner, repo, timeout, config.boardMetrics ?? null),
    loadAndRenderContributionGraph(owner, repo, timeout),
  ]);

  // ── 4. Buscar avatares e re-renderizar equipe ─────────────────────────────
  // Feito após os dados principais para não bloquear o carregamento das stats.
  await loadAndRenderTeamAvatars(config.team, timeout);
}

document.addEventListener('DOMContentLoaded', init);
