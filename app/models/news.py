from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Index
from sqlalchemy.sql import func
from app.models import Base


class NewsPost(Base):
    __tablename__ = "news_posts"

    id = Column(Integer, primary_key=True, index=True)
    source_channel = Column(String(255), nullable=False, index=True)
    original_text = Column(Text, nullable=False)
    processed_text = Column(Text, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    tg_link = Column(String(500), nullable=True)
    importance_score = Column(Float, default=0.0, index=True)
    category = Column(String(100), nullable=True, index=True)
    language = Column(String(10), default='ru')

    def __repr__(self):
        return f"<NewsPost(id={self.id}, source='{self.source_channel}', published={self.published_at})>"