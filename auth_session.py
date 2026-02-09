"""
Одноразовый скрипт авторизации Telegram на сервере.

Запуск (после docker compose --profile prod up -d):

    docker compose --profile prod exec celery-worker python auth_session.py

Скрипт попросит ввести номер телефона и код из Telegram.
Session-файл сохранится в корне проекта (ai_news_parser.session),
который примонтирован в контейнер через bind mount.
Перезапуск worker после авторизации НЕ требуется — следующий таск
подхватит сессию автоматически.
"""

import asyncio
import os
import sys

from telethon import TelegramClient

from dotenv import load_dotenv
from pathlib import Path

# Загрузка переменных окружения из .env
dotenv_path = Path(__file__).resolve().parent / '.env'
if dotenv_path.exists():
    load_dotenv(dotenv_path)
    print(f"Загружены переменные окружения из {dotenv_path}")
else:
    print(f"Внимание: файл .env не найден в {dotenv_path}")


async def main():
    api_id = os.environ.get("TELEGRAM_API_ID")
    api_hash = os.environ.get("TELEGRAM_API_HASH")
    session_name = os.environ.get("TELEGRAM_SESSION_NAME", "ai_news_parser")

    if not api_id or not api_hash:
        print("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in environment")
        sys.exit(1)

    print(f"Session path: {session_name}.session")
    print("Starting Telegram authorization...")
    print()

    client = TelegramClient(session_name, int(api_id), api_hash)

    await client.start()

    me = await client.get_me()
    print()
    print(f"Authorized as: {me.first_name} {me.last_name or ''} (ID: {me.id})")
    print(f"Phone: {me.phone}")
    print()
    print("Session saved. Telegram parsing is now ready to work.")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
