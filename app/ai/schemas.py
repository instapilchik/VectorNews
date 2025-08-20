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

class EntitiesSchema(BaseModel):
    persons: Optional[List[str]] = Field(default=[], description="Список ключевых персон")
    companies: Optional[List[str]] = Field(default=[], description="Список упомянутых компаний")
    locations: Optional[List[str]] = Field(default=[], description="Список ключевых локаций")

class NewsMetadataSchema(BaseModel):
    category: NewsCategory = Field(description="Наиболее подходящая категория для новости")
    keywords: List[str] = Field(description="Список из 3-5 ключевых слов или фраз")
    summary: str = Field(description="Краткая суть новости в одном-двух предложениях")
    entities: EntitiesSchema = Field(description="Извлеченные сущности: персоны, компании, локации")
    importance_score: float = Field(
        description="Оценка важности новости для финансового рынка от 0.0 (неважно) до 1.0 (очень важно)",
        ge=0.0,
        le=1.0
    )

# --- СХЕМА ДЛЯ РАСШИРЕНИЯ ЗАПРОСА ---
class StructuredQuerySchema(BaseModel):
    search_query: str = Field(description="Переформулированный и очищенный от мусора запрос для семантического поиска.")
    filter_categories: Optional[List[NewsCategory]] = Field(default=None, description="Список релевантных категорий для фильтрации поиска.")
    time_range_days: int = Field(default=7, description="Предполагаемая глубина поиска в днях (например, 1, 3, 7, 30).")
