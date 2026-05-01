// Feature: github-pages-project-showcase, Property 15: loadConfig faz round-trip completo de AppConfig
// Feature: github-pages-project-showcase, Property 16: loadConfig retorna DEFAULT_CONFIG para entradas inválidas

import { describe, test, expect, vi, afterEach } from 'vitest';
import * as fc from 'fast-check';
import { loadConfig, DEFAULT_CONFIG } from '../configLoader.js';

afterEach(() => {
  vi.restoreAllMocks();
});

/** Cria um mock de fetch que retorna o body fornecido */
function mockFetch(body, status = 200) {
  const response = {
    ok: status >= 200 && status < 300,
    status,
    json: async () => (typeof body === 'string' ? JSON.parse(body) : body),
  };
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response));
}

/** Cria um mock de fetch que retorna JSON malformado */
function mockFetchMalformed() {
  const response = {
    ok: true,
    status: 200,
    json: async () => { throw new SyntaxError('Unexpected token'); },
  };
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response));
}

const techItemArb = fc.record({
  name: fc.string({ minLength: 1 }),
  url:  fc.webUrl(),
});

const moduleArb = fc.record({
  id:     fc.string({ minLength: 1 }),
  label:  fc.string({ minLength: 1 }),
  status: fc.constantFrom('done', 'in_progress', 'planned'),
});

const teamMemberArb = fc.record({
  name:   fc.string({ minLength: 1 }),
  github: fc.string({ minLength: 1 }),
});

const appConfigArb = fc.record({
  projectName: fc.string({ minLength: 1 }),
  tagline:     fc.string({ minLength: 1 }),
  modules:     fc.array(moduleArb, { minLength: 1 }),
  team:        fc.array(teamMemberArb, { minLength: 1 }),
  links:       fc.record({ repo: fc.webUrl() }),
});

describe('ConfigLoader', () => {
  test('P15 — loadConfig faz round-trip completo de AppConfig', async () => {
    // Feature: github-pages-project-showcase, Property 15
    await fc.assert(
      fc.asyncProperty(appConfigArb, async (config) => {
        mockFetch(config);
        const result = await loadConfig();
        return (
          result.projectName === config.projectName &&
          result.tagline     === config.tagline &&
          result.modules.length === config.modules.length &&
          result.team.length    === config.team.length
        );
      }),
      { numRuns: 50 },
    );
  });

  test('P16 — loadConfig retorna DEFAULT_CONFIG para entradas inválidas', async () => {
    // Feature: github-pages-project-showcase, Property 16
    // Caso 1: HTTP 404
    mockFetch('', 404);
    let result = await loadConfig();
    expect(result).toEqual(DEFAULT_CONFIG);

    // Caso 2: JSON malformado
    mockFetchMalformed();
    result = await loadConfig();
    expect(result).toEqual(DEFAULT_CONFIG);

    // Caso 3: Campos obrigatórios faltando
    mockFetch({ projectName: 'X' }); // falta tagline, modules, team, links
    result = await loadConfig();
    expect(result).toEqual(DEFAULT_CONFIG);
  });

  test('loadConfig retorna DEFAULT_CONFIG quando fetch lança erro de rede', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Network error')));
    const result = await loadConfig();
    expect(result).toEqual(DEFAULT_CONFIG);
  });
});
