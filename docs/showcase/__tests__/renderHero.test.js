// Feature: github-pages-project-showcase, Property 10: renderHero exibe todos os campos da hero section

import { describe, test, beforeEach } from 'vitest';
import * as fc from 'fast-check';
import { renderHero } from '../components/hero.js';

function setupDOM() {
  document.body.innerHTML = `
    <h1 id="hero-title"></h1>
    <p class="hero-tagline"></p>
    <ul id="problems-list"></ul>
    <div id="pipeline-container"></div>
  `;
}

const appConfigArb = fc.record({
  projectName: fc.string({ minLength: 1, maxLength: 30 }),
  tagline:     fc.string({ minLength: 1, maxLength: 80 }),
  problems:    fc.array(fc.string({ minLength: 1, maxLength: 50 }), { minLength: 1, maxLength: 5 }),
  pipeline:    fc.array(fc.string({ minLength: 1, maxLength: 30 }), { minLength: 2, maxLength: 5 }),
});

describe('renderHero', () => {
  beforeEach(setupDOM);

  test('P10 — exibe todos os campos de conteúdo da hero section', () => {
    // Feature: github-pages-project-showcase, Property 10
    fc.assert(
      fc.property(appConfigArb, (config) => {
        setupDOM();
        renderHero(config);

        // Usa textContent dos elementos para evitar falsos negativos com escape HTML
        const titleText    = document.getElementById('hero-title')?.textContent ?? '';
        const taglineText  = document.querySelector('.hero-tagline')?.textContent ?? '';
        const problemTexts = [...document.querySelectorAll('#problems-list li')].map(el => el.textContent);
        const pipelineTexts = [...document.querySelectorAll('#pipeline-container .pipeline-step')].map(el => el.textContent);

        const hasProjectName = titleText === config.projectName;
        const hasTagline     = taglineText === config.tagline;
        const hasAllProblems = config.problems.every(p => problemTexts.includes(p));
        const hasAllSteps    = config.pipeline.every(s => pipelineTexts.includes(s));

        return hasProjectName && hasTagline && hasAllProblems && hasAllSteps;
      }),
      { numRuns: 100 },
    );
  });
});
