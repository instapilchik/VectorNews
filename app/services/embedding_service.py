import logging
from sentence_transformers import SentenceTransformer
from typing import List

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Сервис для преобразования текста в векторные представления (embeddings).
    Использует 'singleton' паттерн для кэширования модели в памяти.
    """
    _model = None
    _model_name = "intfloat/multilingual-e5-base"

    def __init__(self):
        if EmbeddingService._model is None:
            logger.info(f"Loading embedding model '{self._model_name}'...")
            # TODO: Для production можно указать cache_folder, чтобы модель не скачивалась каждый раз при рестарте пода
            EmbeddingService._model = SentenceTransformer(self._model_name)
            logger.info("Embedding model loaded successfully.")

    def get_embedding(self, text: str) -> List[float]:
        """
        Получает вектор для одного текста.
        Добавляет префикс 'passage:' для улучшения качества, как рекомендовано для e5 моделей.
        """
        if not self._model:
            raise Exception("Embedding model is not loaded.")

        # Префикс 'passage:' используется для документов, которые будут индексироваться
        prefixed_text = f"passage: {text}"

        vector = self._model.encode(prefixed_text, convert_to_tensor=False)
        return vector.tolist()


# Singleton instance
embedding_service = EmbeddingService()
