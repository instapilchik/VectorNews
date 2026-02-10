-- Миграция: Кросс-канальная дедупликация
-- Дата: 2026-02-10
-- Описание: Добавляет поля skip_reason и duplicate_of в таблицу news_posts
-- Документация: docs/cross_channel_deduplication.md

-- 1. Новые колонки
ALTER TABLE news_posts ADD COLUMN IF NOT EXISTS skip_reason VARCHAR;
ALTER TABLE news_posts ADD COLUMN IF NOT EXISTS duplicate_of INTEGER REFERENCES news_posts(id);

-- 2. Индекс для быстрой фильтрации по skip_reason
CREATE INDEX IF NOT EXISTS ix_news_posts_skip_reason ON news_posts (skip_reason);

-- 3. Проверка
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'news_posts' AND column_name IN ('skip_reason', 'duplicate_of');