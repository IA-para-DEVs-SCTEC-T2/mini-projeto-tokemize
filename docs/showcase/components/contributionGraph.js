/**
 * contributionGraph.js — Componente de gráfico de barras SVG de contribuições
 *
 * Renderiza atividade semanal de commits como gráfico de barras SVG acessível.
 * Requirements: 3.1, 3.2, 3.3, 3.4
 */

/** Paleta de cores distintas para autores (pelo menos 10 cores) */
const AUTHOR_COLOR_PALETTE = [
  '#58a6ff', // accent blue
  '#3fb950', // green
  '#d29922', // yellow/amber
  '#f85149', // red
  '#bc8cff', // purple
  '#ff7b72', // coral
  '#79c0ff', // light blue
  '#56d364', // light green
  '#e3b341', // gold
  '#ff9bce', // pink
  '#ffa657', // orange
  '#8b949e', // neutral gray
];

/**
 * Retorna um Map com uma cor distinta por autor.
 *
 * @param {string[]} authors - Array de usernames
 * @returns {Map<string, string>} Mapa de username → cor hex
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
 * Formata uma data ISO (ex: "2025-01-06") para label abreviado (ex: "Jan 06").
 *
 * @param {string} isoDate - Data no formato "YYYY-MM-DD"
 * @returns {string} Label formatado
 */
function formatWeekLabel(isoDate) {
  try {
    const date = new Date(isoDate + 'T00:00:00');
    return date.toLocaleDateString('pt-BR', { month: 'short', day: '2-digit' });
  } catch {
    return isoDate;
  }
}

/**
 * Renderiza um gráfico de barras SVG de atividade semanal de commits.
 *
 * @typedef {Object} WeeklyActivity
 * @property {string} week - Data ISO do início da semana (ex: "2025-01-06")
 * @property {number} totalCommits - Total de commits na semana
 * @property {Object} byAuthor - Mapa de username → número de commits
 *
 * @param {WeeklyActivity[]} activity - Array de atividade semanal
 */
export function renderContributionGraph(activity) {
  const container = document.getElementById('contribution-graph-container');
  if (!container) return;

  // Limpa o conteúdo anterior
  container.innerHTML = '';

  const totalCommits = activity.reduce((sum, w) => sum + (w.totalCommits ?? 0), 0);
  const ariaLabel = `Gráfico de contribuições: ${totalCommits} commits nas últimas ${activity.length} semanas`;

  // Dimensões do SVG
  const svgWidth = 780;
  const svgHeight = 200;
  const barWidth = 40;
  const barGap = 20;
  const paddingTop = 10;
  const paddingBottom = 40; // espaço para labels do eixo X
  const paddingLeft = 10;
  const chartHeight = svgHeight - paddingTop - paddingBottom;

  // Altura máxima de commits para escala
  const maxCommits = Math.max(...activity.map(w => w.totalCommits ?? 0), 1);

  // Cria o SVG
  const svgNS = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(svgNS, 'svg');
  svg.setAttribute('viewBox', `0 0 ${svgWidth} ${svgHeight}`);
  svg.setAttribute('width', '100%');
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', ariaLabel);

  // <title> interno para acessibilidade
  const titleEl = document.createElementNS(svgNS, 'title');
  titleEl.textContent = ariaLabel;
  svg.appendChild(titleEl);

  // Referência ao tooltip
  const tooltip = document.getElementById('graph-tooltip');

  // Renderiza cada barra
  activity.forEach((week, index) => {
    const commits = week.totalCommits ?? 0;
    const barHeight = chartHeight * (commits / maxCommits);
    const x = paddingLeft + index * (barWidth + barGap);
    const y = paddingTop + (chartHeight - barHeight);

    // Grupo da barra (barra + label)
    const group = document.createElementNS(svgNS, 'g');
    group.setAttribute('class', 'bar-group');

    // Retângulo da barra
    const rect = document.createElementNS(svgNS, 'rect');
    rect.setAttribute('x', String(x));
    rect.setAttribute('y', String(y));
    rect.setAttribute('width', String(barWidth));
    rect.setAttribute('height', String(Math.max(barHeight, 1)));
    rect.setAttribute('fill', 'var(--color-accent, #58a6ff)');
    rect.setAttribute('rx', '3');
    rect.setAttribute('ry', '3');
    rect.setAttribute('tabindex', '0');
    rect.setAttribute('aria-label', `${commits} commits — semana de ${week.week}`);

    // Tooltip via mouse events
    if (tooltip) {
      rect.addEventListener('mouseenter', (e) => {
        tooltip.textContent = `${commits} commits — semana de ${week.week}`;
        tooltip.classList.add('visible');
        tooltip.removeAttribute('aria-hidden');
      });

      rect.addEventListener('mousemove', (e) => {
        tooltip.style.left = `${e.clientX + 12}px`;
        tooltip.style.top = `${e.clientY - 28}px`;
      });

      rect.addEventListener('mouseleave', () => {
        tooltip.classList.remove('visible');
        tooltip.setAttribute('aria-hidden', 'true');
      });

      // Suporte a teclado (focus/blur)
      rect.addEventListener('focus', (e) => {
        tooltip.textContent = `${commits} commits — semana de ${week.week}`;
        tooltip.classList.add('visible');
        tooltip.removeAttribute('aria-hidden');
      });

      rect.addEventListener('blur', () => {
        tooltip.classList.remove('visible');
        tooltip.setAttribute('aria-hidden', 'true');
      });
    }

    group.appendChild(rect);

    // Label do eixo X
    const label = document.createElementNS(svgNS, 'text');
    label.setAttribute('x', String(x + barWidth / 2));
    label.setAttribute('y', String(svgHeight - 8));
    label.setAttribute('text-anchor', 'middle');
    label.setAttribute('font-size', '10');
    label.setAttribute('fill', 'var(--color-text-secondary, #8b949e)');
    label.setAttribute('aria-hidden', 'true');
    label.textContent = formatWeekLabel(week.week);

    group.appendChild(label);
    svg.appendChild(group);
  });

  container.appendChild(svg);
}
