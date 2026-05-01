// Feature: github-pages-project-showcase — Unit tests para ApiClient

import { describe, test, expect, vi, afterEach } from 'vitest';
import { fetchRepoStats, fetchAvatarUrl, ApiError } from '../apiClient.js';

afterEach(() => {
  vi.restoreAllMocks();
});

/** Cria um mock de fetch que retorna dados com Link header para paginação */
function mockFetchWithLink(data, total = 1) {
  const linkHeader = total > 1
    ? `<https://api.github.com/resource?page=${total}>; rel="last"`
    : null;

  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    headers: {
      get: (name) => name === 'Link' ? linkHeader : null,
    },
    json: async () => data,
  }));
}

describe('ApiClient', () => {
  test('fetchRepoStats — resposta bem-sucedida retorna RepoStats corretamente mapeado', async () => {
    // Mock: 5 commits, 2 open PRs, 3 closed PRs, 4 contributors, 6 branches
    const lastCommitDate = '2025-04-01T10:00:00Z';
    let callCount = 0;

    vi.stubGlobal('fetch', vi.fn().mockImplementation((url) => {
      callCount++;
      let total = 1;
      if (url.includes('/commits')) total = 5;
      if (url.includes('state=open')) total = 2;
      if (url.includes('state=closed')) total = 3;
      if (url.includes('/contributors')) total = 4;
      if (url.includes('/branches')) total = 6;

      const linkHeader = total > 1
        ? `<https://api.github.com/resource?page=${total}>; rel="last"`
        : null;

      const data = url.includes('/commits') && url.includes('sha=main')
        ? [{ commit: { author: { date: lastCommitDate } } }]
        : [];

      return Promise.resolve({
        ok: true,
        status: 200,
        headers: { get: (name) => name === 'Link' ? linkHeader : null },
        json: async () => data,
      });
    }));

    const stats = await fetchRepoStats('owner', 'repo', 8000);

    expect(stats.totalCommits).toBe(5);
    expect(stats.openPRs).toBe(2);
    expect(stats.closedPRs).toBe(3);
    expect(stats.contributors).toBe(4);
    expect(stats.activeBranches).toBe(6);
    expect(stats.lastCommitAt).toBe(lastCommitDate);
  });

  test('fetchRepoStats — HTTP 4xx lança ApiError com status e endpoint corretos', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 403,
      headers: { get: () => null },
      json: async () => ({ message: 'Forbidden' }),
    }));

    await expect(fetchRepoStats('owner', 'repo', 8000)).rejects.toThrow(ApiError);
    await expect(fetchRepoStats('owner', 'repo', 8000)).rejects.toMatchObject({ status: 403 });
  });

  test('fetchAvatarUrl — retorna avatar_url do usuário', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: { get: () => null },
      json: async () => ({ avatar_url: 'https://avatars.githubusercontent.com/u/123' }),
    }));

    const url = await fetchAvatarUrl('testuser', 8000);
    expect(url).toBe('https://avatars.githubusercontent.com/u/123');
  });
});
