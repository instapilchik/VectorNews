from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.models import Base


class NewsPost(Base):
    __tablename__ = "news_posts"

    # Основные поля
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, nullable=False)  # ID сообщения в ТГ
    source_channel = Column(String(255), nullable=False, index=True)
    channel_title = Column(String(255), nullable=True)
    original_text = Column(Text, nullable=False)
    processed_text = Column(Text, nullable=True)

    # Даты
    published_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # Telegram метрики
    tg_link = Column(String(500), nullable=True)
    views_count = Column(Integer, nullable=True)
    forwards_count = Column(Integer, nullable=True)
    reactions_count = Column(Integer, default=0)

    # Медиа и контент
    media_type = Column(String(50), nullable=True)  # photo, video, document, etc.
    has_links = Column(Boolean, default=False)

    # Классификация (заготовка для этапа 3)
    is_processed = Column(Boolean, default=False, index=True)
    is_spam = Column(Boolean, default=False)
    is_advertisement = Column(Boolean, default=False)
    is_humor = Column(Boolean, default=False)
    is_financial_relevant = Column(Boolean, default=True)

    # --- Поля обогащения (заполняются LLM-классификатором) ---
    category = Column(String, nullable=True, index=True)
    summary = Column(Text, nullable=True)
    keywords = Column(JSONB, nullable=True)
    entities = Column(JSONB, nullable=True)
    importance_score = Column(Float, nullable=True, index=True)

    # Категоризация
    sector = Column(String(50), nullable=True, index=True)  # currency, commodities, stocks, crypto, geopolitics
    sentiment = Column(String(20), nullable=True)  # positive, negative, neutral
    classification_confidence = Column(Float, nullable=True)
    tags = Column(JSONB, nullable=True)  # ["рубль", "нефть", "санкции"]

    # Базовая категория из парсера (keyword-matching при импорте из TG)
    estimated_category = Column(String(100), nullable=True)
    language = Column(String(10), default='ru')

    # Индексы для оптимизации
    __table_args__ = (
        Index('idx_telegram_unique', 'telegram_id', 'source_channel', unique=True),
        Index('idx_published_at', 'published_at'),
        Index('idx_classification', 'is_processed', 'is_spam'),
        Index('idx_sector_importance', 'sector', 'importance_score'),
    )

    def __repr__(self):
        return f"<NewsPost(id={self.id}, tg_id={self.telegram_id}, source='{self.source_channel}', published={self.published_at})>"
