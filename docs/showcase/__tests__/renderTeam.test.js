// Feature: github-pages-project-showcase, Property 12: renderTeam exibe nome e link GitHub de cada membro
// Feature: github-pages-project-showcase, Property 13: Avatar do membro é exibido quando disponível
// Feature: github-pages-project-showcase, Property 14: Avatar padrão é exibido quando API não está disponível

import { describe, test, expect, beforeEach } from 'vitest';
import * as fc from 'fast-check';
import { renderTeam } from '../components/team.js';

const DEFAULT_AVATAR = './assets/default-avatar.svg';

function setupDOM() {
  document.body.innerHTML = '<ul id="team-list"></ul>';
}

const teamMemberArb = fc.record({
  name:   fc.string({ minLength: 1, maxLength: 40 }),
  github: fc.stringMatching(/^[a-zA-Z0-9-]{1,20}$/),
});

describe('renderTeam', () => {
  beforeEach(setupDOM);

  test('P12 — exibe nome e link GitHub de cada membro', () => {
    // Feature: github-pages-project-showcase, Property 12
    fc.assert(
      fc.property(
        fc.array(teamMemberArb, { minLength: 1, maxLength: 6 }),
        (members) => {
          setupDOM();
          renderTeam(members, new Map());

          const nameEls = [...document.querySelectorAll('.team-name')].map(el => el.textContent);
          const linkEls = [...document.querySelectorAll('.team-github-link')];

          return members.every(m => {
            const hasName = nameEls.includes(m.name);
            const hasLink = linkEls.some(a =>
              a.getAttribute('href') === `https://github.com/${m.github}`
            );
            return hasName && hasLink;
          });
        },
      ),
      { numRuns: 100 },
    );
  });

  test('P13 — avatar do membro é exibido quando disponível', () => {
    // Feature: github-pages-project-showcase, Property 13
    fc.assert(
      fc.property(
        teamMemberArb,
        fc.webUrl(),
        (member, avatarUrl) => {
          setupDOM();
          const avatars = new Map([[member.github, avatarUrl]]);
          renderTeam([member], avatars);

          const img = document.querySelector('.team-avatar');
          return img !== null && img.getAttribute('src') === avatarUrl;
        },
      ),
      { numRuns: 100 },
    );
  });

  test('P14 — avatar padrão é exibido quando API não está disponível', () => {
    // Feature: github-pages-project-showcase, Property 14
    fc.assert(
      fc.property(teamMemberArb, (member) => {
        setupDOM();
        renderTeam([member], new Map());

        const img = document.querySelector('.team-avatar');
        return img !== null && img.getAttribute('src') === DEFAULT_AVATAR;
      }),
      { numRuns: 100 },
    );
  });

  test('renderTeam com lista vazia não lança erro', () => {
    expect(() => renderTeam([], new Map())).not.toThrow();
  });
});
