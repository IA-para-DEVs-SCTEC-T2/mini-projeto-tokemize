// Feature: github-pages-project-showcase, Property 7: Progress_Tracker renderiza label e status de cada módulo
// Feature: github-pages-project-showcase, Property 8: calculateProgress retorna a porcentagem correta
// Feature: github-pages-project-showcase, Property 9: Status manual tem prioridade absoluta

import { describe, test, expect, beforeEach } from 'vitest';
import * as fc from 'fast-check';
import { renderProgressTracker, calculateProgress } from '../components/progressTracker.js';

function setupDOM() {
  document.body.innerHTML = '<div id="progress-container"></div>';
}

const statusArb = fc.constantFrom('done', 'in_progress', 'planned');

const moduleConfigArb = fc.record({
  id:     fc.string({ minLength: 1, maxLength: 20 }),
  label:  fc.string({ minLength: 1, maxLength: 30 }),
  status: statusArb,
});

describe('renderProgressTracker', () => {
  beforeEach(setupDOM);

  test('P7 — renderiza label e status de cada módulo', () => {
    // Feature: github-pages-project-showcase, Property 7
    fc.assert(
      fc.property(fc.array(moduleConfigArb, { minLength: 1, maxLength: 10 }), (modules) => {
        setupDOM();
        renderProgressTracker(modules);

        // Usa textContent dos elementos para evitar falsos negativos com escape HTML
        const labelEls = [...document.querySelectorAll('.module-label')].map(el => el.textContent);
        const badgeEls = [...document.querySelectorAll('.module-badge')];

        const allLabelsPresent = modules.every(mod => labelEls.includes(mod.label));
        const allStatusesPresent = modules.every(mod =>
          badgeEls.some(el => el.classList.contains(`module-badge--${mod.status}`))
        );

        return allLabelsPresent && allStatusesPresent;
      }),
      { numRuns: 100 },
    );
  });

  test('P8 — calculateProgress retorna a porcentagem correta de módulos concluídos', () => {
    // Feature: github-pages-project-showcase, Property 8
    fc.assert(
      fc.property(fc.array(moduleConfigArb, { minLength: 1, maxLength: 20 }), (modules) => {
        const doneCount = modules.filter(m => m.status === 'done').length;
        const expected = (doneCount / modules.length) * 100;
        const result = calculateProgress(modules);
        return Math.abs(result - expected) < 0.0001;
      }),
      { numRuns: 100 },
    );
  });

  test('P9 — status manual tem prioridade absoluta no Progress_Tracker', () => {
    // Feature: github-pages-project-showcase, Property 9
    fc.assert(
      fc.property(moduleConfigArb, (mod) => {
        setupDOM();
        renderProgressTracker([mod]);
        const html = document.getElementById('progress-container').innerHTML;
        // O badge deve conter a classe correspondente ao status configurado
        return html.includes(`module-badge--${mod.status}`);
      }),
      { numRuns: 100 },
    );
  });

  test('calculateProgress retorna 0 para array vazio', () => {
    expect(calculateProgress([])).toBe(0);
  });

  test('calculateProgress retorna 100 quando todos os módulos estão done', () => {
    const modules = [
      { id: 'a', label: 'A', status: 'done' },
      { id: 'b', label: 'B', status: 'done' },
    ];
    expect(calculateProgress(modules)).toBe(100);
  });
});
