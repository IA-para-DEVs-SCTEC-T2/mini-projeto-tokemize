// Feature: github-pages-project-showcase, Property 3: CacheStore.isStale respeita o TTL de 1 hora

import { describe, test, expect, beforeEach, vi } from 'vitest';
import * as fc from 'fast-check';
import { CacheStore, DEFAULT_TTL } from '../cacheStore.js';

describe('CacheStore', () => {
  let store;

  beforeEach(() => {
    store = new CacheStore();
    localStorage.clear();
  });

  test('P3 — isStale respeita o TTL de 1 hora', () => {
    // Feature: github-pages-project-showcase, Property 3: isStale retorna true sse (Date.now() - t) > maxAgeMs
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: DEFAULT_TTL * 2 }),
        (ageMs) => {
          const now = Date.now();
          const timestamp = now - ageMs;

          // Inserir entrada manualmente no localStorage com timestamp controlado
          const key = 'tokemize_cache_test_p3';
          localStorage.setItem(key, JSON.stringify({ data: 'x', timestamp }));

          const result = store.isStale('test_p3', DEFAULT_TTL);
          const expected = ageMs > DEFAULT_TTL;

          return result === expected;
        },
      ),
      { numRuns: 100 },
    );
  });

  test('get retorna null para chave inexistente', () => {
    expect(store.get('nao_existe')).toBeNull();
  });

  test('set e get fazem round-trip', () => {
    store.set('chave', { valor: 42 });
    expect(store.get('chave')).toEqual({ valor: 42 });
  });

  test('isStale retorna true para chave inexistente', () => {
    expect(store.isStale('nao_existe', DEFAULT_TTL)).toBe(true);
  });

  test('isStale retorna false para entrada recém-criada', () => {
    store.set('recente', 'dado');
    expect(store.isStale('recente', DEFAULT_TTL)).toBe(false);
  });
});
