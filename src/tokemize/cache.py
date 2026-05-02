"""Sistema de cache incremental local baseado em hash de arquivos."""

import hashlib
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class FileCache:
    """Gerencia cache incremental local de arquivos processados."""

    def __init__(self, cache_dir=".cache/tokemize"):
        """Inicializa o gerenciador de cache."""
        self.cache_dir = Path(cache_dir)
        self.cache_file = self.cache_dir / "file_cache.json"
        self._cache = {}
        self._ensure_cache_dir()
        self._load_cache()

    def _ensure_cache_dir(self):
        """Cria o diretório de cache se não existir."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Diretório de cache garantido: {self.cache_dir}")

    def _load_cache(self):
        """Carrega o cache do disco."""
        if not self.cache_file.exists():
            logger.debug("Arquivo de cache não encontrado, iniciando com cache vazio")
            return

        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                self._cache = json.load(f)
            logger.info(f"Cache carregado com {len(self._cache)} entradas")
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.warning(f"Falha ao carregar cache, iniciando novo: {e}")
            self._cache = {}

    def save_cache(self):
        """Persiste o cache atual em disco."""
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)
            logger.debug(f"Cache salvo com {len(self._cache)} entradas")
        except (OSError, TypeError) as e:
            logger.error(f"Falha ao salvar cache: {e}")

    def calculate_file_hash(self, file_path):
        """Calcula o hash SHA-256 do conteúdo de um arquivo."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)

        return hasher.hexdigest()

    def get_cached_file(self, file_path):
        """Recupera um arquivo do cache se existir e estiver válido."""
        path_str = str(Path(file_path).resolve())

        if path_str not in self._cache:
            logger.debug(f"Cache miss: {file_path}")
            return None

        try:
            current_hash = self.calculate_file_hash(file_path)
            cached_entry = self._cache[path_str]

            if current_hash == cached_entry.get("content_hash"):
                logger.debug(f"Cache hit: {file_path}")
                return cached_entry
            else:
                logger.debug(f"Cache invalidado (hash diferente): {file_path}")
                return None

        except (FileNotFoundError, OSError) as e:
            logger.warning(f"Erro ao verificar cache para {file_path}: {e}")
            return None

    def update_cached_file(self, file_path, symbols=None, imports=None, 
                          summary="", token_estimate=0, metadata=None):
        """Atualiza ou cria uma entrada no cache para um arquivo."""
        path_str = str(Path(file_path).resolve())
        content_hash = self.calculate_file_hash(file_path)

        cached_data = {
            "file_path": path_str,
            "content_hash": content_hash,
            "symbols": symbols or [],
            "imports": imports or [],
            "summary": summary,
            "token_estimate": token_estimate,
            "metadata": metadata or {},
        }

        self._cache[path_str] = cached_data
        logger.debug(f"Cache atualizado: {file_path}")

        return cached_data

    def clear(self):
        """Limpa todo o cache em memória e no disco."""
        self._cache.clear()
        if self.cache_file.exists():
            self.cache_file.unlink()
        logger.info("Cache limpo")

    def get_stats(self):
        """Retorna estatísticas do cache."""
        total_symbols = sum(len(entry.get("symbols", [])) for entry in self._cache.values())
        total_imports = sum(len(entry.get("imports", [])) for entry in self._cache.values())

        return {
            "total_entries": len(self._cache),
            "total_symbols": total_symbols,
            "total_imports": total_imports,
        }
