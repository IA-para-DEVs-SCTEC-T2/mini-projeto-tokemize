/**
 * testMetrics.js — Componente de renderização da seção "Qualidade de Código"
 *
 * Popula o elemento #test-metrics com os dados de testMetrics do config.json.
 * Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9
 */

/**
 * Converte um timestamp ISO 8601 para o formato "DD/MM/YYYY HH:MM"
 * no timezone local do navegador.
 *
 * @param {string|null} isoTimestamp - Timestamp ISO 8601
 * @returns {string} Data formatada ou "—" se inválido
 */
function formatLocalDateTime(isoTimestamp) {
  if (!isoTimestamp) return '—';
  try {
    const date = new Date(isoTimestamp);
    if (isNaN(date.getTime())) return '—';
    const day    = String(date.getDate()).padStart(2, '0');
    const month  = String(date.getMonth() + 1).padStart(2, '0');
    const year   = date.getFullYear();
    const hours  = String(date.getHours()).padStart(2, '0');
    const mins   = String(date.getMinutes()).padStart(2, '0');
    return `${day}/${month}/${year} ${hours}:${mins}`;
  } catch {
    return '—';
  }
}

/**
 * Cria um card de métrica com label e valor, seguindo o padrão .stat-card.
 *
 * @param {string} label - Rótulo do card
 * @param {string|number} value - Valor a exibir
 * @returns {HTMLElement}
 */
function createMetricCard(label, value) {
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
 * Cria o indicador de status (passing / failing / unknown).
 *
 * @param {'passing'|'failing'|'unknown'} status
 * @returns {HTMLElement}
 */
function createStatusIndicator(status) {
  const wrapper = document.createElement('div');
  wrapper.className = 'test-status-indicator';

  const dot = document.createElement('span');
  dot.className = 'test-status-dot';
  dot.setAttribute('aria-hidden', 'true');

  const label = document.createElement('span');
  label.className = 'test-status-label';

  if (status === 'passing') {
    dot.style.backgroundColor = '#22c55e';
    dot.textContent = '✓';
    label.textContent = 'Passando';
    wrapper.setAttribute('aria-label', 'Status: Passando');
  } else if (status === 'failing') {
    dot.style.backgroundColor = '#ef4444';
    dot.textContent = '✗';
    label.textContent = 'Falhando';
    wrapper.setAttribute('aria-label', 'Status: Falhando');
  } else {
    dot.style.backgroundColor = '#9ca3af';
    dot.textContent = '?';
    label.textContent = 'Desconhecido';
    wrapper.setAttribute('aria-label', 'Status: Desconhecido');
  }

  wrapper.appendChild(dot);
  wrapper.appendChild(label);

  return wrapper;
}

/**
 * Renderiza a seção "Qualidade de Código" no elemento #test-metrics.
 *
 * Quando `testMetrics` é null/undefined/vazio, exibe mensagem de indisponibilidade.
 *
 * @param {Object|null|undefined} testMetrics - Dados de testMetrics do config.json
 */
export function renderTestMetrics(testMetrics) {
  const section = document.getElementById('test-metrics');
  if (!section) return;

  // Limpa o conteúdo existente (placeholder)
  section.innerHTML = '';

  const inner = document.createElement('div');
  inner.className = 'section-inner';

  const heading = document.createElement('h2');
  heading.id = 'test-metrics-title';
  heading.className = 'section-title';
  heading.textContent = 'Qualidade de Código';
  inner.appendChild(heading);

  // Caso sem dados
  if (!testMetrics || Object.keys(testMetrics).length === 0) {
    const empty = document.createElement('p');
    empty.className = 'loading-placeholder';
    empty.textContent = 'Métricas de teste não disponíveis';
    inner.appendChild(empty);
    section.appendChild(inner);
    return;
  }

  const grid = document.createElement('div');
  grid.className = 'stats-grid';
  grid.setAttribute('aria-live', 'polite');
  grid.setAttribute('aria-atomic', 'true');

  // ── Bloco principal ───────────────────────────────────────────────────────
  const block = document.createElement('div');
  block.className = 'stats-block';

  const blockHeading = document.createElement('h3');
  blockHeading.className = 'stats-block-title';
  blockHeading.textContent = 'Resultados dos Testes';
  block.appendChild(blockHeading);

  // Status indicator
  block.appendChild(createStatusIndicator(testMetrics.status ?? 'unknown'));

  const cards = document.createElement('div');
  cards.className = 'stats-cards-row';

  // Total de Testes
  cards.appendChild(createMetricCard('Total de Testes', testMetrics.totalTests ?? 0));

  // Taxa de Sucesso
  const total = testMetrics.totalTests ?? 0;
  const passed = testMetrics.passed ?? 0;
  const successRate = total > 0
    ? `${(passed / total * 100).toFixed(1)}%`
    : '—';
  cards.appendChild(createMetricCard('Taxa de Sucesso', successRate));

  // Testes Passados
  cards.appendChild(createMetricCard('Passados', passed));

  // Testes Falhados
  cards.appendChild(createMetricCard('Falhados', testMetrics.failed ?? 0));

  // Cobertura (somente se disponível e não null)
  if (testMetrics.coverage !== null && testMetrics.coverage !== undefined) {
    cards.appendChild(
      createMetricCard('Cobertura de Código', `${Number(testMetrics.coverage).toFixed(1)}%`)
    );
  }

  block.appendChild(cards);

  // Última execução
  if (testMetrics.lastRunAt) {
    const lastRun = document.createElement('p');
    lastRun.className = 'board-updated-at';
    lastRun.textContent = `Última execução: ${formatLocalDateTime(testMetrics.lastRunAt)}`;
    block.appendChild(lastRun);
  }

  grid.appendChild(block);
  inner.appendChild(grid);
  section.appendChild(inner);
}
