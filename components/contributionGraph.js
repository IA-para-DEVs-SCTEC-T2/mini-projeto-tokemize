/**
 * contributionGraph.js — Painel de contribuidores do repositório
 *
 * Renderiza cards com avatar, nome e total de commits de cada contribuidor,
 * usando dados do endpoint /contributors da GitHub API.
 * Requirements: 3.1, 3.2, 3.3, 3.4
 */

/** Paleta de cores distintas para autores */
const AUTHOR_COLOR_PALETTE = [
  '#58a6ff',
  '#3fb950',
  '#d29922',
  '#f85149',
  '#bc8cff',
  '#ff7b72',
  '#79c0ff',
  '#56d364',
  '#e3b341',
  '#ff9bce',
  '#ffa657',
  '#8b949e',
];

/**
 * Retorna um Map com uma cor distinta por autor.
 *
 * @param {string[]} authors
 * @returns {Map<string, string>}
 */
export function getAuthorColors(authors) {
  const colorMap = new Map();
  const uniqueAuthors = [...new Set(authors)];
  uniqueAuthors.forEach((author, index) => {
    colorMap.set(author, AUTHOR_COLOR_PALETTE[index % AUTHOR_COLOR_PALETTE.length]);
  });
  return colorMap;
}

/**
 * @typedef {Object} Contributor
 * @property {string} login
 * @property {number} contributions
 * @property {string} avatar_url
 * @property {string} html_url
 */

/**
 * Renderiza o painel de contribuidores no elemento #contribution-graph-container.
 * Exibe avatar, login e total de commits de cada contribuidor.
 *
 * @param {Contributor[]} contributors
 */
export function renderContributionGraph(contributors) {
  const container = document.getElementById('contribution-graph-container');
  if (!container) return;

  container.innerHTML = '';

  if (!Array.isArray(contributors) || contributors.length === 0) {
    const empty = document.createElement('p');
    empty.className = 'loading-placeholder';
    empty.textContent = 'Nenhum dado de contribuição disponível.';
    container.appendChild(empty);
    return;
  }

  const colorMap = getAuthorColors(contributors.map(c => c.login));

  // Total de commits para calcular percentual de cada autor
  const totalCommits = contributors.reduce((sum, c) => sum + c.contributions, 0);

  const grid = document.createElement('div');
  grid.className = 'contributors-grid';
  grid.setAttribute('role', 'list');
  grid.setAttribute('aria-label', `${contributors.length} contribuidores do repositório`);

  for (const contributor of contributors) {
    const color = colorMap.get(contributor.login) ?? '#8b949e';
    const pct = totalCommits > 0
      ? Math.round((contributor.contributions / totalCommits) * 100)
      : 0;

    const card = document.createElement('div');
    card.className = 'contributor-card';
    card.setAttribute('role', 'listitem');
    card.style.setProperty('--contributor-color', color);

    // Avatar
    const img = document.createElement('img');
    img.className = 'contributor-avatar';
    img.src = contributor.avatar_url;
    img.alt = `Avatar de ${contributor.login}`;
    img.width = 64;
    img.height = 64;
    img.loading = 'lazy';
    // fallback se a imagem falhar
    img.onerror = () => { img.src = 'assets/default-avatar.svg'; };

    // Info
    const info = document.createElement('div');
    info.className = 'contributor-info';

    const name = document.createElement('a');
    name.className = 'contributor-name';
    name.href = contributor.html_url;
    name.target = '_blank';
    name.rel = 'noopener noreferrer';
    name.textContent = contributor.login;

    const commits = document.createElement('span');
    commits.className = 'contributor-commits';
    commits.textContent = `${contributor.contributions} commits`;

    // Barra de progresso proporcional
    const barTrack = document.createElement('div');
    barTrack.className = 'contributor-bar-track';
    barTrack.setAttribute('role', 'progressbar');
    barTrack.setAttribute('aria-valuenow', String(pct));
    barTrack.setAttribute('aria-valuemin', '0');
    barTrack.setAttribute('aria-valuemax', '100');
    barTrack.setAttribute('aria-label', `${pct}% dos commits`);

    const barFill = document.createElement('div');
    barFill.className = 'contributor-bar-fill';
    barFill.style.width = `${pct}%`;
    barFill.style.backgroundColor = color;

    barTrack.appendChild(barFill);
    info.appendChild(name);
    info.appendChild(commits);
    info.appendChild(barTrack);

    card.appendChild(img);
    card.appendChild(info);
    grid.appendChild(card);
  }

  container.appendChild(grid);
}

