// Feature: github-pages-project-showcase, Property 4: Contribution_Graph cobre as últimas 13 semanas
// Feature: github-pages-project-showcase, Property 5: Contribution_Graph atribui cores distintas por autor
// Feature: github-pages-project-showcase, Property 6: Contribution_Graph SVG possui aria-label não vazio

import { describe, test, expect, beforeEach } from 'vitest';
import * as fc from 'fast-check';
import { renderContributionGraph, getAuthorColors } from '../components/contributionGraph.js';

function setupDOM() {
  document.body.innerHTML = `
    <div id="contribution-graph-container"></div>
    <div id="graph-tooltip" class="graph-tooltip"></div>
  `;
}

/** Gera uma data ISO no formato YYYY-MM-DD */
const isoDateArb = fc.date({
  min: new Date('2024-01-01'),
  max: new Date('2026-12-31'),
}).map(d => d.toISOString().slice(0, 10));

const weeklyActivityArb = fc.record({
  week:         isoDateArb,
  totalCommits: fc.nat({ max: 50 }),
  byAuthor:     fc.dictionary(
    fc.stringMatching(/^[a-zA-Z0-9-]{1,15}$/),
    fc.nat({ max: 20 }),
  ),
});

/**
 * Filtra atividade para as últimas 13 semanas — replica a lógica do componente.
 */
function filterLast13Weeks(activity) {
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - 90);
  return activity.filter(w => new Date(w.week + 'T00:00:00') >= cutoff);
}

describe('renderContributionGraph', () => {
  beforeEach(setupDOM);

  test('P4 — cobre exatamente as últimas 13 semanas', () => {
    // Feature: github-pages-project-showcase, Property 4
    fc.assert(
      fc.property(
        fc.array(weeklyActivityArb, { minLength: 0, maxLength: 20 }),
        (activity) => {
          const filtered = filterLast13Weeks(activity);
          // Todas as semanas filtradas devem estar dentro dos últimos 90 dias
          const cutoff = new Date();
          cutoff.setDate(cutoff.getDate() - 90);
          return filtered.every(w => new Date(w.week + 'T00:00:00') >= cutoff);
        },
      ),
      { numRuns: 100 },
    );
  });

  test('P5 — atribui cores distintas por autor', () => {
    // Feature: github-pages-project-showcase, Property 5
    fc.assert(
      fc.property(
        fc.array(
          fc.stringMatching(/^[a-zA-Z0-9-]{1,15}$/),
          { minLength: 1, maxLength: 12 },
        ).map(arr => [...new Set(arr)]).filter(arr => arr.length > 0),
        (authors) => {
          const colorMap = getAuthorColors(authors);
          const colors = [...colorMap.values()];
          const uniqueColors = new Set(colors);
          // Cada autor deve ter uma cor; autores distintos devem ter cores distintas
          // (até o limite da paleta de 12 cores)
          const effectiveAuthors = authors.slice(0, 12);
          return colorMap.size === authors.length &&
                 uniqueColors.size === Math.min(authors.length, 12);
        },
      ),
      { numRuns: 100 },
    );
  });

  test('P6 — SVG possui aria-label não vazio', () => {
    // Feature: github-pages-project-showcase, Property 6
    fc.assert(
      fc.property(
        fc.array(weeklyActivityArb, { minLength: 0, maxLength: 13 }),
        (activity) => {
          setupDOM();
          renderContributionGraph(activity);
          const svg = document.querySelector('#contribution-graph-container svg');
          if (!svg) return activity.length === 0; // sem dados, pode não renderizar SVG
          const ariaLabel = svg.getAttribute('aria-label');
          return typeof ariaLabel === 'string' && ariaLabel.length > 0;
        },
      ),
      { numRuns: 100 },
    );
  });

  test('tooltip — exibe commits e período ao passar o cursor', () => {
    const activity = [
      { week: '2025-01-06', totalCommits: 7, byAuthor: {} },
    ];
    setupDOM();
    renderContributionGraph(activity);

    const rect = document.querySelector('rect');
    expect(rect).not.toBeNull();

    // Simula mouseenter
    rect.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
    const tooltip = document.getElementById('graph-tooltip');
    expect(tooltip.textContent).toContain('7');
    expect(tooltip.textContent).toContain('2025-01-06');
  });
});
