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
import { fetchRepoData, fetchAvatarUrl } from './apiClient.js';

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
 * Carrega stats e contributors em uma única bateria de chamadas à API,
 * depois renderiza ambas as seções.
 *
 * @param {string} owner
 * @param {string} repo
 * @param {number} timeout
 * @param {Object|null} boardMetrics
 */
async function loadAndRenderRepoData(owner, repo, timeout, boardMetrics = null) {
  const statsStale       = cache.isStale(CACHE_KEY_STATS,    DEFAULT_TTL);
  const activityStale    = cache.isStale(CACHE_KEY_ACTIVITY, DEFAULT_TTL);

  // Se ambos os caches são válidos, usa cache direto
  if (!statsStale && !activityStale) {
    renderStats(cache.get(CACHE_KEY_STATS), false, boardMetrics);
    renderContributionGraph(cache.get(CACHE_KEY_ACTIVITY));
    return;
  }

  try {
    // Uma única bateria de 6 chamadas paralelas retorna stats + contributors
    const { stats, contributors } = await fetchRepoData(owner, repo, timeout);

    cache.set(CACHE_KEY_STATS,    stats);
    cache.set(CACHE_KEY_ACTIVITY, contributors);

    renderStats(stats, false, boardMetrics);
    renderContributionGraph(contributors);
  } catch (err) {
    // Fallback para cache stale se disponível
    const cachedStats       = cache.get(CACHE_KEY_STATS);
    const cachedContributors = cache.get(CACHE_KEY_ACTIVITY);

    renderStats(cachedStats ?? null, cachedStats !== null, boardMetrics);
    if (cachedContributors) renderContributionGraph(cachedContributors);
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
  await loadAndRenderRepoData(owner, repo, timeout, config.boardMetrics ?? null);

  // ── 4. Buscar avatares e re-renderizar equipe ─────────────────────────────
  // Feito após os dados principais para não bloquear o carregamento das stats.
  await loadAndRenderTeamAvatars(config.team, timeout);
}

document.addEventListener('DOMContentLoaded', init);
