"""
Одноразовый скрипт авторизации Telegram на сервере.

Запуск (после docker compose --profile prod up -d):

    docker compose --profile prod exec celery-worker python auth_session.py

Скрипт попросит ввести номер телефона и код из Telegram.
Session-файл сохранится в Docker volume и переживёт рестарты контейнеров.
Перезапуск worker после авторизации НЕ требуется — следующий таск
подхватит сессию автоматически.
"""

import asyncio
import os
import sys

from telethon import TelegramClient


async def main():
    api_id = os.environ.get("TELEGRAM_API_ID")
    api_hash = os.environ.get("TELEGRAM_API_HASH")
    session_name = os.environ.get("TELEGRAM_SESSION_NAME", "ai_news_parser")

    if not api_id or not api_hash:
        print("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in environment")
        sys.exit(1)

    # Убедимся что директория для session-файла существует
    session_dir = os.path.dirname(session_name)
    if session_dir:
        os.makedirs(session_dir, exist_ok=True)

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
