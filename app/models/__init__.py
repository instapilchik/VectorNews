from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Импортируем все модели чтобы они были зарегистрированы
from app.models.news import NewsPost