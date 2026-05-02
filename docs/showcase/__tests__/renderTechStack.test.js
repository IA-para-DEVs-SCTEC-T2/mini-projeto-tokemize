// Feature: github-pages-project-showcase, Property 11: renderTechStack exibe nome e link de cada tecnologia

import { describe, test, beforeEach } from 'vitest';
import * as fc from 'fast-check';
import { renderTechStack } from '../components/techStack.js';

function setupDOM() {
  document.body.innerHTML = '<ul id="tech-stack-list"></ul>';
}

const techItemArb = fc.record({
  name: fc.string({ minLength: 1, maxLength: 30 }),
  url:  fc.webUrl(),
});

describe('renderTechStack', () => {
  beforeEach(setupDOM);

  test('P11 — exibe nome e link de cada tecnologia', () => {
    // Feature: github-pages-project-showcase, Property 11
    fc.assert(
      fc.property(
        fc.array(techItemArb, { minLength: 1, maxLength: 8 }),
        (techStack) => {
          setupDOM();
          renderTechStack({ techStack });

          const anchors = [...document.querySelectorAll('#tech-stack-list a')];

          return techStack.every(tech => {
            return anchors.some(a =>
              a.textContent === tech.name && a.getAttribute('href') === tech.url
            );
          });
        },
      ),
      { numRuns: 100 },
    );
  });
});
