from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum

class NewsCategory(str, Enum):
    GEOPOLITICS = "Геополитика"
    ECONOMY = "Экономика"
    RAW_MATERIALS = "Сырье"
    CRYPTO = "Криптовалюты"
    CORPORATE = "Корпоративное"
    MACROECONOMICS = "Макроэкономика"
    GENERAL = "Общее"

class NewsSector(str, Enum):
    CURRENCY = "currency"
    COMMODITIES = "commodities"
    STOCKS = "stocks"
    CRYPTO = "crypto"
    GEOPOLITICS = "geopolitics"
    MACRO = "macro"
    OTHER = "other"

class NewsSentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class EntitiesSchema(BaseModel):
    persons: Optional[List[str]] = Field(default=[], description="Список ключевых персон")
    companies: Optional[List[str]] = Field(default=[], description="Список упомянутых компаний")
    locations: Optional[List[str]] = Field(default=[], description="Список ключевых локаций")

class NewsMetadataSchema(BaseModel):
    # --- Классификация контента ---
    is_spam: bool = Field(description="Технический спам, бессмысленные сообщения")
    is_advertisement: bool = Field(description="Реклама брокеров, курсов, торговых сигналов, призывы к действию")
    is_humor: bool = Field(description="Мемы, шутки, развлекательный контент")
    is_financial_relevant: bool = Field(description="Имеет отношение к финансам, экономике или трейдингу")

    # --- Основные метаданные ---
    category: NewsCategory = Field(description="Наиболее подходящая тематическая категория для новости")
    sector: NewsSector = Field(description="Рыночный сектор, к которому относится новость")
    sentiment: NewsSentiment = Field(description="Тональность новости для рынка")
    importance_score: float = Field(
        description="Оценка важности новости для финансового рынка от 0.0 (неважно) до 1.0 (очень важно)",
        ge=0.0,
        le=1.0
    )
    classification_confidence: float = Field(
        description="Уверенность в корректности классификации от 0.0 до 1.0",
        ge=0.0,
        le=1.0
    )

    # --- Извлечённый контент ---
    summary: str = Field(description="Краткая суть новости в одном-двух предложениях")
    keywords: List[str] = Field(description="Список из 3-5 ключевых слов или фраз")
    tags: List[str] = Field(default=[], description="Ключевые теги для быстрого поиска, например: рубль, нефть, ЦБ, санкции")
    entities: EntitiesSchema = Field(description="Извлеченные сущности: персоны, компании, локации")

# --- СХЕМА ДЛЯ РАСШИРЕНИЯ ЗАПРОСА ---
class StructuredQuerySchema(BaseModel):
    search_query: str = Field(description="Переформулированный и очищенный от мусора запрос для семантического поиска.")
    filter_categories: Optional[List[NewsCategory]] = Field(default=None, description="Список релевантных категорий для фильтрации поиска.")
    time_range_days: int = Field(default=7, description="Предполагаемая глубина поиска в днях (например, 1, 3, 7, 30).")
