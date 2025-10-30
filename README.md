# NewsEdge

Персональный новостной аналитик для трейдеров с AI-powered поиском и анализом.

## Описание

Сервис автоматически собирает финансовые новости из Telegram-каналов, обрабатывает их с помощью LLM, и позволяет задавать вопросы на естественном языке. Использует RAG-архитектуру для точного поиска релевантной информации.

**Основные возможности:**
- Автоматический парсинг новостей из Telegram
- Классификация и оценка важности событий
- Векторный поиск по семантике
- Персонализированные ответы на вопросы
- Готовые дашборды (горячие темы, тематические подборки)

## Стек технологий

- **Backend:** FastAPI, Celery
- **Database:** PostgreSQL, Redis, Qdrant (vector DB)
- **AI:** OpenRouter API, sentence-transformers
- **Parsing:** Telethon

## Быстрый старт

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Создайте `.env` файл с конфигурацией:
```bash
cp .env.example .env
# Заполните необходимые переменные
```

3. Запустите инфраструктуру:
```bash
docker-compose up -d
```

4. Запустите API:
```bash
uvicorn app.main:app --reload
```

5. Запустите Celery worker:
```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

## API Endpoints

- `POST /api/agent/chat` - Задать вопрос по новостям
- `GET /api/dashboards/hot-topics` - Горячие темы
- `GET /api/dashboards/daily-briefing` - Сводка за день
- `GET /api/dashboards/thematic` - Новости по категориям

## Документация

Swagger UI доступен по адресу: `http://localhost:8000/api/docs`

## Архитектура

```
Telegram → Parser → PostgreSQL → Classifier (LLM) → Vector DB (Qdrant)
                                                              ↓
User Query → Query Expansion (LLM) → Semantic Search → Answer Synthesis (LLM)
```