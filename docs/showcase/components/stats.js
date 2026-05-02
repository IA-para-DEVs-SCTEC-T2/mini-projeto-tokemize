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
  if (!grid) {
    return;
  }

  grid.innerHTML = '';

  // Estado de erro: stats indisponível
  if (stats === null) {
    const errorEl = document.createElement('div');
    errorEl.className = 'stats-error';
    errorEl.textContent = 'Não foi possível carregar as estatísticas.';
    grid.appendChild(errorEl);
    return;
  }

  // Banner de dados desatualizados (antes dos cards)
  if (stale) {
    const banner = document.createElement('div');
    banner.className = 'stats-stale-banner';
    banner.setAttribute('data-stale', 'true');
    banner.textContent = '⚠ Dados podem estar desatualizados';
    grid.appendChild(banner);
  }

  // Cards de estatísticas do repositório (via API em tempo real)
  const repoCards = [
    { label: 'Total de Commits',  value: stats.totalCommits },
    { label: 'PRs Abertos',       value: stats.openPRs },
    { label: 'PRs Fechados',      value: stats.closedPRs },
    { label: 'Contribuidores',    value: stats.contributors },
    { label: 'Branches Ativas',   value: stats.activeBranches },
    { label: 'Último Commit',     value: formatDate(stats.lastCommitAt) },
  ];

  for (const { label, value } of repoCards) {
    grid.appendChild(createStatCard(label, value));
  }

  // Cards do Project Board (via config.json atualizado pelo workflow)
  if (boardMetrics && boardMetrics.totalCards > 0) {
    const separator = document.createElement('div');
    separator.className = 'stats-section-separator';

    const boardTitle = document.createElement('h3');
    boardTitle.className = 'stats-section-title';
    boardTitle.textContent = boardMetrics.projectTitle
      ? `Board: ${boardMetrics.projectTitle}`
      : 'Project Board';

    grid.appendChild(separator);
    grid.appendChild(boardTitle);

    // Card com total de itens no board
    grid.appendChild(createStatCard('Total de Cards', boardMetrics.totalCards));

    // Um card por status (ex: "Todo", "In Progress", "Done")
    const statusEntries = Object.entries(boardMetrics.cardsByStatus ?? {});
    for (const [status, count] of statusEntries) {
      grid.appendChild(createStatCard(status, count));
    }

    // Timestamp da última atualização do board
    if (boardMetrics.lastUpdatedAt) {
      const updatedEl = document.createElement('p');
      updatedEl.className = 'board-updated-at';
      updatedEl.textContent = `Board atualizado em: ${formatDate(boardMetrics.lastUpdatedAt)}`;
      grid.appendChild(updatedEl);
    }
  }
}
