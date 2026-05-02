"""Seletor inteligente de contexto para LLMs."""

import logging

logger = logging.getLogger(__name__)


class ContextSelector:
    """Seleciona e ranqueia arquivos relevantes respeitando o budget de tokens."""

    def __init__(self, indexer, embeddings_client, relevance_threshold=0.75, top_k=20):
        """Inicializa o ContextSelector."""
        if not 0.0 <= relevance_threshold <= 1.0:
            raise ValueError(
                f"relevance_threshold deve estar em [0.0, 1.0], recebido {relevance_threshold}"
            )

        self.indexer = indexer
        self.embeddings_client = embeddings_client
        self.relevance_threshold = relevance_threshold
        self.top_k = top_k

        logger.debug(
            f"ContextSelector inicializado: threshold={relevance_threshold}, top_k={top_k}"
        )

    def select(self, request, token_budget):
        """Seleciona os arquivos mais relevantes dentro do budget de tokens."""
        logger.info(f"Iniciando seleção de contexto: budget={token_budget} tokens")

        # 1. Gera embedding da requisição
        query_vector = self.embeddings_client.embed_text(request)
        logger.debug(f"Embedding da query gerado: dim={len(query_vector)}")

        # 2. Busca candidatos no FAISS
        candidates = self.indexer.search(query_vector, top_k=self.top_k)
        logger.debug(f"Recuperados {len(candidates)} candidatos do FAISS")

        # 3. Filtra por relevance_threshold
        filtered = [
            (item, score)
            for item, score in candidates
            if score >= self.relevance_threshold
        ]

        if not filtered:
            logger.warning(
                f"Nenhum arquivo acima do limiar de relevância {self.relevance_threshold}"
            )
            return {
                "files_complete": [],
                "files_summary": [],
                "files_ignored": [item for item, _ in candidates],
                "total_tokens": 0,
                "formatted_text": "",
            }

        logger.debug(
            f"Filtrados {len(filtered)} arquivos acima do limiar {self.relevance_threshold}"
        )

        # 4. Ordena por score decrescente, desempata por menor token_count
        ranked = self._rank_items(filtered)

        # 5. Acumula arquivos até atingir token_budget
        selected, ignored = self._accumulate_within_budget(ranked, token_budget)

        # 6. Formata contexto final
        total_tokens = sum(item.get("token_count", 0) for item in selected)
        formatted_text = self._format_context(selected)

        logger.info(
            f"Seleção de contexto completa: {len(selected)} arquivos, {total_tokens} tokens"
        )

        return {
            "files_complete": selected,
            "files_summary": [],
            "files_ignored": ignored,
            "total_tokens": total_tokens,
            "formatted_text": formatted_text,
        }

    def _rank_items(self, candidates):
        """Ranqueia arquivos por score de relevância e token_count."""
        ranked = sorted(
            candidates,
            key=lambda x: (-x[1], x[0].get("token_count", 0)),
        )

        logger.debug(f"Ranqueados {len(ranked)} arquivos por relevância e tamanho")
        return ranked

    def _accumulate_within_budget(self, ranked_items, token_budget):
        """Acumula arquivos em ordem de relevância até o budget ser atingido."""
        selected = []
        ignored = []
        accumulated_tokens = 0

        for item, score in ranked_items:
            item_tokens = item.get("token_count", 0)
            item_name = item.get("name", "unknown")

            if accumulated_tokens + item_tokens <= token_budget:
                selected.append(item)
                accumulated_tokens += item_tokens
                logger.debug(
                    f"Selecionado '{item_name}': "
                    f"{item_tokens} tokens (score={score:.3f})"
                )
            else:
                ignored.append(item)
                logger.debug(
                    f"Ignorado '{item_name}': "
                    f"excederia budget ({accumulated_tokens + item_tokens} > {token_budget})"
                )

        if ignored:
            logger.debug(
                f"Ignorados {len(ignored)} arquivos devido ao limite de tokens"
            )

        return selected, ignored

    def _format_context(self, items):
        """Formata os arquivos selecionados em um bloco de texto estruturado."""
        if not items:
            return ""

        formatted_parts = []

        for item in items:
            name = item.get("name", "unknown")
            language = item.get("language", "text")
            content = item.get("content", "")

            header = f"### [{language}] — {name}"
            code_block = f"```{language}\n{content}\n```"
            formatted_parts.append(f"{header}\n{code_block}")

        return "\n\n".join(formatted_parts)
