/**
 * app.js — Entry point da Showcase_Page do Tokemize
 *
 * Todos os dados dinâmicos (stats, contributors, PRs) são lidos do config.json,
 * que é atualizado pelo workflow update-board-metrics.yml a cada 6 horas.
 * Zero chamadas à GitHub API no browser — sem risco de rate limit.
 */

import { loadConfig }            from './configLoader.js';
import { renderHero }            from './components/hero.js';
import { renderStats }           from './components/stats.js';
import { renderContributionGraph, renderPRGraph } from './components/contributionGraph.js';
import { renderProgressTracker } from './components/progressTracker.js';
import { renderTechStack }       from './components/techStack.js';
import { renderTeam }            from './components/team.js';

async function init() {
  const config = await loadConfig();

  // ── Seções estáticas ──────────────────────────────────────────────────────
  renderHero(config);
  renderTechStack(config);
  renderProgressTracker(config.modules);

  // ── Equipe com avatares do config.json ────────────────────────────────────
  // contributors tem avatar_url; monta o mapa para renderTeam
  const avatars = new Map();
  for (const c of (config.contributors ?? [])) {
    if (c.login && c.avatar_url) avatars.set(c.login, c.avatar_url);
  }
  // Também mapeia pelo github username dos membros da equipe
  for (const member of (config.team ?? [])) {
    if (!avatars.has(member.github)) {
      const match = (config.contributors ?? []).find(c => c.login === member.github);
      if (match) avatars.set(member.github, match.avatar_url);
    }
  }
  renderTeam(config.team, avatars);

  // ── Stats do repositório ──────────────────────────────────────────────────
  if (config.repoStats) {
    renderStats(config.repoStats, false, config.boardMetrics ?? null);
  } else {
    renderStats(null, false, config.boardMetrics ?? null);
  }

  // ── Commits por contribuidor ──────────────────────────────────────────────
  renderContributionGraph(config.contributors ?? []);

  // ── PRs por contribuidor ──────────────────────────────────────────────────
  renderPRGraph(config.prAuthors ?? []);
}

document.addEventListener('DOMContentLoaded', init);
