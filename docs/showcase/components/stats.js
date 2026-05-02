/**
 * stats.js — Componente de renderização da seção de Estatísticas
 *
 * Popula o elemento #stats-grid com os dados de RepoStats e boardMetrics.
 * Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
 */

/**
 * Formata uma data ISO 8601 para exibição localizada em pt-BR.
 *
 * @param {string} isoDate - Data no formato ISO 8601
 * @returns {string} Data formatada
 */
function formatDate(isoDate) {
  try {
    const date = new Date(isoDate);
    return date.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  } catch {
    return isoDate;
  }
}

/**
 * Cria um card de estatística.
 *
 * @param {string} label - Rótulo do card
 * @param {string|number} value - Valor a exibir
 * @returns {HTMLElement}
 */
function createStatCard(label, value) {
  const card = document.createElement('div');
  card.className = 'stat-card';

  const labelEl = document.createElement('span');
  labelEl.className = 'stat-label';
  labelEl.textContent = label;

  const valueEl = document.createElement('span');
  valueEl.className = 'stat-value';
  valueEl.textContent = String(value);

  card.appendChild(labelEl);
  card.appendChild(valueEl);

  return card;
}

/**
 * Renderiza as estatísticas do repositório no elemento #stats-grid.
 *
 * Quando `stats` é null, exibe um estado de erro amigável.
 * Quando `stale` é true, exibe um banner de aviso de dados desatualizados.
 *
 * @param {import('../apiClient.js').RepoStats|null} stats
 * @param {boolean} stale
 * @param {Object|null} [boardMetrics] - Métricas do Project board (do config.json)
 */
export function renderStats(stats, stale, boardMetrics = null) {
  const grid = document.getElementById('stats-grid');
  if (!grid) return;

  grid.innerHTML = '';

  if (stats === null) {
    const errorEl = document.createElement('div');
    errorEl.className = 'stats-error';
    errorEl.textContent = 'Não foi possível carregar as estatísticas.';
    grid.appendChild(errorEl);
    return;
  }

  if (stale) {
    const banner = document.createElement('div');
    banner.className = 'stats-stale-banner';
    banner.setAttribute('data-stale', 'true');
    banner.textContent = '⚠ Dados podem estar desatualizados';
    grid.appendChild(banner);
  }

  // ── Bloco: Repositório ────────────────────────────────────────────────────
  const repoBlock = document.createElement('div');
  repoBlock.className = 'stats-block';

  const repoHeading = document.createElement('h3');
  repoHeading.className = 'stats-block-title';
  repoHeading.textContent = 'Repositório';
  repoBlock.appendChild(repoHeading);

  const repoCards = document.createElement('div');
  repoCards.className = 'stats-cards-row';

  const repoData = [
    { label: 'Total de Commits',  value: stats.totalCommits },
    { label: 'PRs Abertos',       value: stats.openPRs },
    { label: 'PRs Fechados',      value: stats.closedPRs },
    { label: 'Contribuidores',    value: stats.contributors },
    { label: 'Branches Ativas',   value: stats.activeBranches },
    { label: 'Último Commit',     value: formatDate(stats.lastCommitAt) },
  ];

  for (const { label, value } of repoData) {
    repoCards.appendChild(createStatCard(label, value));
  }

  repoBlock.appendChild(repoCards);
  grid.appendChild(repoBlock);

  // ── Bloco: Project Board ──────────────────────────────────────────────────
  if (boardMetrics && boardMetrics.totalCards > 0) {
    const boardBlock = document.createElement('div');
    boardBlock.className = 'stats-block';

    const boardHeading = document.createElement('h3');
    boardHeading.className = 'stats-block-title';
    boardHeading.textContent = boardMetrics.projectTitle
      ? `Board · ${boardMetrics.projectTitle}`
      : 'Project Board';
    boardBlock.appendChild(boardHeading);

    const boardCards = document.createElement('div');
    boardCards.className = 'stats-cards-row';

    boardCards.appendChild(createStatCard('Total de Cards', boardMetrics.totalCards));

    for (const [status, count] of Object.entries(boardMetrics.cardsByStatus ?? {})) {
      boardCards.appendChild(createStatCard(status, count));
    }

    boardBlock.appendChild(boardCards);

    if (boardMetrics.lastUpdatedAt) {
      const updatedEl = document.createElement('p');
      updatedEl.className = 'board-updated-at';
      updatedEl.textContent = `Atualizado em ${formatDate(boardMetrics.lastUpdatedAt)}`;
      boardBlock.appendChild(updatedEl);
    }

    grid.appendChild(boardBlock);
  }
}
