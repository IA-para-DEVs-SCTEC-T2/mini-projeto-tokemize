/**
 * progressTracker.js — Componente de rastreamento de progresso por módulo
 *
 * Calcula e renderiza o progresso geral e o status de cada módulo.
 * Requirements: 4.1, 4.2, 4.3, 4.4
 */

/**
 * Mapa de status para labels em português.
 */
const STATUS_LABELS = {
  done: 'Concluído',
  in_progress: 'Em desenvolvimento',
  planned: 'Planejado',
};

/**
 * Calcula o percentual de módulos concluídos.
 *
 * @typedef {Object} ModuleConfig
 * @property {string} id - Identificador do módulo
 * @property {string} label - Nome de exibição
 * @property {"done"|"in_progress"|"planned"} status - Status do módulo
 *
 * @param {ModuleConfig[]} modules - Array de módulos
 * @returns {number} Percentual de módulos com status "done" (0–100)
 */
export function calculateProgress(modules) {
  if (!modules || modules.length === 0) return 0;
  const doneCount = modules.filter(m => m.status === 'done').length;
  return (doneCount / modules.length) * 100;
}

/**
 * Renderiza o rastreador de progresso no elemento #progress-container.
 *
 * Exibe:
 * 1. Barra de progresso geral com percentual
 * 2. Grid de cards por módulo com label e badge de status
 *
 * O status exibido SEMPRE vem do campo `status` do módulo (prioridade absoluta).
 *
 * @param {ModuleConfig[]} modules - Array de módulos
 */
export function renderProgressTracker(modules) {
  const container = document.getElementById('progress-container');
  if (!container) return;

  container.innerHTML = '';

  const percentual = Math.round(calculateProgress(modules));

  // ── Barra de progresso geral ──────────────────────────────────
  const progressOverall = document.createElement('div');
  progressOverall.className = 'progress-overall';

  const progressLabel = document.createElement('div');
  progressLabel.className = 'progress-overall-label';

  const labelText = document.createElement('span');
  labelText.textContent = 'Progresso Geral';

  const percentText = document.createElement('span');
  percentText.textContent = `${percentual}%`;

  progressLabel.appendChild(labelText);
  progressLabel.appendChild(percentText);

  const progressTrack = document.createElement('div');
  progressTrack.className = 'progress-bar-track';

  const progressFill = document.createElement('div');
  progressFill.className = 'progress-bar-fill';
  progressFill.style.width = `${percentual}%`;

  progressTrack.appendChild(progressFill);
  progressOverall.appendChild(progressLabel);
  progressOverall.appendChild(progressTrack);
  container.appendChild(progressOverall);

  // ── Grid de módulos ───────────────────────────────────────────
  const modulesGrid = document.createElement('div');
  modulesGrid.className = 'modules-grid';

  for (const mod of modules) {
    // O status exibido SEMPRE vem do campo status do módulo (prioridade absoluta)
    const status = mod.status;
    const statusLabel = STATUS_LABELS[status] ?? status;

    const card = document.createElement('div');
    card.className = 'module-card';

    const labelEl = document.createElement('span');
    labelEl.className = 'module-label';
    labelEl.textContent = mod.label;

    const badge = document.createElement('span');
    badge.className = `module-badge module-badge--${status}`;
    badge.textContent = statusLabel;

    card.appendChild(labelEl);
    card.appendChild(badge);
    modulesGrid.appendChild(card);
  }

  container.appendChild(modulesGrid);
}
