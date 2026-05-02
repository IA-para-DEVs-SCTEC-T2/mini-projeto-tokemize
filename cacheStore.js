/**
 * CacheStore — camada de cache sobre localStorage.
 *
 * Cada entrada é armazenada como:
 *   { "data": <T>, "timestamp": <number ms> }
 *
 * Todas as chaves são prefixadas com `tokemize_cache_` para evitar colisões.
 */

/** TTL padrão: 1 hora em milissegundos. */
export const DEFAULT_TTL = 3600000;

const KEY_PREFIX = 'tokemize_cache_v2_';

export class CacheStore {
  /**
   * Recupera o dado armazenado para a chave informada.
   * Retorna `null` se a entrada não existir ou se o localStorage estiver indisponível.
   *
   * @template T
   * @param {string} key
   * @returns {T | null}
   */
  get(key) {
    try {
      const raw = localStorage.getItem(KEY_PREFIX + key);
      if (raw === null) return null;
      const entry = JSON.parse(raw);
      return entry.data ?? null;
    } catch {
      return null;
    }
  }

  /**
   * Armazena `data` associado à `key` com o timestamp atual.
   * Não faz nada se o localStorage estiver indisponível.
   *
   * @template T
   * @param {string} key
   * @param {T} data
   * @returns {void}
   */
  set(key, data) {
    try {
      const entry = { data, timestamp: Date.now() };
      localStorage.setItem(KEY_PREFIX + key, JSON.stringify(entry));
    } catch {
      // localStorage indisponível (modo privado / SSR) — falha silenciosa
    }
  }

  /**
   * Verifica se a entrada para `key` está desatualizada em relação a `maxAgeMs`.
   *
   * Retorna `true` se:
   *   - a entrada não existir no cache, ou
   *   - `(Date.now() - entry.timestamp) > maxAgeMs`
   *
   * @param {string} key
   * @param {number} maxAgeMs
   * @returns {boolean}
   */
  isStale(key, maxAgeMs) {
    try {
      const raw = localStorage.getItem(KEY_PREFIX + key);
      if (raw === null) return true;
      const entry = JSON.parse(raw);
      if (typeof entry.timestamp !== 'number') return true;
      return (Date.now() - entry.timestamp) > maxAgeMs;
    } catch {
      return true;
    }
  }
}
