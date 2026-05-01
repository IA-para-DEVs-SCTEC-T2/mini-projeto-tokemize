// Feature: github-pages-project-showcase, Property 1: Stats_Widget renderiza todos os campos de RepoStats
// Feature: github-pages-project-showcase, Property 2: Indicador de dados desatualizados é exibido quando stale=true

import { describe, test, expect, beforeEach } from 'vitest';
import * as fc from 'fast-check';
import { renderStats } from '../components/stats.js';

function setupDOM() {
  document.body.innerHTML = '<div id="stats-grid"></div>';
}

const repoStatsArb = fc.record({
  totalCommits:   fc.nat(),
  openPRs:        fc.nat(),
  closedPRs:      fc.nat(),
  contributors:   fc.nat(),
  activeBranches: fc.nat(),
  lastCommitAt:   fc.date({ min: new Date('2020-01-01'), max: new Date('2026-12-31') })
                    .map(d => d.toISOString()),
});

describe('renderStats', () => {
  beforeEach(setupDOM);

  test('P1 — renderiza todos os campos de RepoStats', () => {
    // Feature: github-pages-project-showcase, Property 1
    fc.assert(
      fc.property(repoStatsArb, (stats) => {
        setupDOM();
        renderStats(stats, false);
        const html = document.getElementById('stats-grid').innerHTML;

        return (
          html.includes(String(stats.totalCommits)) &&
          html.includes(String(stats.openPRs)) &&
          html.includes(String(stats.closedPRs)) &&
          html.includes(String(stats.contributors)) &&
          html.includes(String(stats.activeBranches))
        );
      }),
      { numRuns: 100 },
    );
  });

  test('P2 — indicador de dados desatualizados é exibido quando stale=true', () => {
    // Feature: github-pages-project-showcase, Property 2
    fc.assert(
      fc.property(repoStatsArb, (stats) => {
        setupDOM();
        renderStats(stats, true);
        const grid = document.getElementById('stats-grid');
        const staleEl = grid.querySelector('[data-stale="true"]');
        return staleEl !== null;
      }),
      { numRuns: 100 },
    );
  });

  test('renderStats(null) exibe estado de erro', () => {
    renderStats(null, false);
    const html = document.getElementById('stats-grid').innerHTML;
    expect(html).toContain('stats-error');
  });

  test('stale=false não exibe indicador de desatualização', () => {
    renderStats({ totalCommits: 1, openPRs: 0, closedPRs: 0, contributors: 1, activeBranches: 1, lastCommitAt: new Date().toISOString() }, false);
    const staleEl = document.querySelector('[data-stale="true"]');
    expect(staleEl).toBeNull();
  });
});
