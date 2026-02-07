import logging
from typing import List, Tuple
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)


class RerankerService:
    """
    Переранжирование результатов поиска с помощью cross-encoder.
    Cross-encoder точнее bi-encoder (embedding), т.к. оценивает пару (query, document) целиком.
    """
    _model = None
    _model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def __init__(self):
        if RerankerService._model is None:
            logger.info(f"Loading reranker model '{self._model_name}'...")
            RerankerService._model = CrossEncoder(self._model_name, max_length=512)
            logger.info("Reranker model loaded.")

    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 10
    ) -> List[Tuple[int, float]]:
        """
        Переранжирует документы по релевантности к запросу.
        Возвращает список (original_index, score), отсортированный по score desc.
        """
        if not documents:
            return []

        pairs = [(query, doc) for doc in documents]
        scores = self._model.predict(pairs)

        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)

        return indexed_scores[:top_k]


reranker_service = RerankerService()
