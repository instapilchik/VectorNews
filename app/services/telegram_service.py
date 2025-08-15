import asyncio
import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from telethon import TelegramClient
from telethon.tl.types import Message
from app.config import settings
from app.services.news_service import NewsService
import logging

logger = logging.getLogger(__name__)


class TelegramService:
    def __init__(self):
        self.client = TelegramClient(
            settings.telegram_session_name,
            settings.telegram_api_id,
            settings.telegram_api_hash
        )
        self.news_service = NewsService()

        # Базовые категории (заглушка для этапа 3)
        self.basic_categories = {
            'экономика': [
                'рубль', 'доллар', 'евро', 'инфляция', 'биржа', 'ВВП', 'банк',
                'экономика', 'финансы', 'инвестиции', 'бюджет', 'налог', 'ЦБ'
            ],
            'геополитика': [
                'санкции', 'правительство', 'президент', 'дума', 'министр',
                'закон', 'депутат', 'партия', 'выборы', 'власть', 'война'
            ],
            'сырье': [
                'нефть', 'газ', 'золото', 'серебро', 'медь', 'алюминий',
                'пшеница', 'уголь', 'урал', 'brent'
            ],
            'криптовалюты': [
                'биткоин', 'bitcoin', 'эфириум', 'ethereum', 'криптовалюта',
                'блокчейн', 'майнинг', 'defi'
            ]
        }

    async def connect(self):
        """Подключение к Telegram"""
        try:
            await self.client.start()
            logger.info("Connected to Telegram successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Telegram: {e}")
            raise e

    async def disconnect(self):
        """Отключение от Telegram"""
        try:
            await self.client.disconnect()
            logger.info("Disconnected from Telegram")
        except Exception as e:
            logger.error(f"Error disconnecting from Telegram: {e}")

    def clean_text(self, text: str) -> str:
        """Очистка текста от лишних символов (из твоего кода)"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text).strip()
        emoji_pattern = re.compile("["
                                   u"\U0001F600-\U0001F64F"
                                   u"\U0001F300-\U0001F5FF"
                                   u"\U0001F680-\U0001F6FF"
                                   u"\U0001F1E0-\U0001F1FF"
                                   "]+", flags=re.UNICODE)
        return emoji_pattern.sub(r'', text)

    def categorize_news_basic(self, text: str) -> Optional[str]:
        """Базовая категоризация (заглушка для этапа 3)"""
        text_lower = text.lower()
        category_scores = {
            category: sum(1 for keyword in keywords if keyword.lower() in text_lower)
            for category, keywords in self.basic_categories.items()
        }
        category_scores = {k: v for k, v in category_scores.items() if v > 0}

        if category_scores:
            return max(category_scores, key=category_scores.get)
        return 'общее'

    def has_links(self, text: str) -> bool:
        """Проверка наличия ссылок в тексте"""
        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        return bool(url_pattern.search(text))

    def get_media_type(self, message: Message) -> Optional[str]:
        """Определение типа медиа в сообщении"""
        if message.photo: return 'photo'
        if message.video: return 'video'
        if message.document: return 'document'
        if message.audio: return 'audio'
        if message.voice: return 'voice'
        if message.sticker: return 'sticker'
        if message.poll: return 'poll'
        return None

    async def parse_channel_messages(
            self,
            channel_username: str,
            limit_count: Optional[int] = None,
            stop_at_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Парсинг сообщений из канала (адаптированный твой код)"""

        if not limit_count and not stop_at_date:
            logger.error("Must specify either limit_count or stop_at_date")
            return []

        if stop_at_date and stop_at_date.tzinfo is None:
            stop_at_date = stop_at_date.replace(tzinfo=timezone.utc)

        logger.info(f"Parsing channel: {channel_username}")
        logger.info(f"Limit count: {limit_count or 'not set'}")
        logger.info(f"Stop at date: {stop_at_date.strftime('%Y-%m-%d') if stop_at_date else 'not set'}")

        try:
            entity = await self.client.get_entity(channel_username)
            channel_title = getattr(entity, 'title', channel_username)
            news_items = []
            processed_count = 0

            async for message in self.client.iter_messages(entity, limit=limit_count):
                # Проверка по дате
                if stop_at_date and message.date < stop_at_date:
                    logger.info(f"Reached date limit ({stop_at_date.strftime('%Y-%m-%d')}). Stopping.")
                    break

                if not message.text:
                    continue

                cleaned_text = self.clean_text(message.text)
                if not cleaned_text or len(cleaned_text) < 10:  # Минимальная длина
                    continue

                # Создаем запись для БД
                news_item = {
                    'telegram_id': message.id,
                    'source_channel': channel_username,
                    'channel_title': channel_title,
                    'original_text': cleaned_text,
                    'published_at': message.date,
                    'views_count': getattr(message, 'views', None),
                    'forwards_count': getattr(message.forwards, 'replies', None) if message.forwards else None,
                    'reactions_count': len(message.reactions.results) if message.reactions else 0,
                    'media_type': self.get_media_type(message),
                    'has_links': self.has_links(cleaned_text),
                    'estimated_category': self.categorize_news_basic(cleaned_text),
                    'tg_link': f"https://t.me/{channel_username.lstrip('@')}/{message.id}",
                    # Поля для классификации (заглушки)
                    'is_processed': False,
                    'is_spam': False,  # Заглушка
                    'is_advertisement': False,  # Заглушка
                    'is_humor': False,  # Заглушка
                    'is_financial_relevant': True,  # По умолчанию релевантно
                    'importance_score': 0.5,  # Заглушка
                }

                news_items.append(news_item)
                processed_count += 1

                if processed_count % 100 == 0:
                    logger.info(f"Processed {processed_count} messages...")

            logger.info(f"Parsing completed. Got {len(news_items)} news items.")
            return news_items

        except Exception as e:
            logger.error(f"Error parsing channel {channel_username}: {e}")
            return []

    async def parse_with_overlap(self, channel_username: str) -> int:
        """Парсинг канала с нахлестом для регулярного обновления"""
        try:
            # Получаем время последней записи
            last_parsed = await self.news_service.get_last_parsed_time(channel_username)

            if last_parsed:
                # С нахлестом
                stop_date = last_parsed - timedelta(hours=settings.parse_overlap_hours)
                logger.info(f"Parsing {channel_username} since {stop_date} (with overlap)")
            else:
                # Первый раз - берем последние 7 дней
                stop_date = datetime.utcnow() - timedelta(days=7)
                logger.info(f"First time parsing {channel_username}, going back 7 days")

            # Парсим новые сообщения
            news_items = await self.parse_channel_messages(
                channel_username=channel_username,
                stop_at_date=stop_date
            )

            if news_items:
                saved_count = await self.news_service.save_news_batch(news_items)
                logger.info(f"Saved {saved_count} new items from {channel_username}")
                return saved_count
            else:
                logger.info(f"No new items found in {channel_username}")
                return 0

        except Exception as e:
            logger.error(f"Error in parse_with_overlap for {channel_username}: {e}")
            raise e
