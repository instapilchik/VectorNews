"""
# AI News Manager - Этап 1

## Запуск

1. Создайте .env файл:
```bash
cp .env.example .env
```

2. Запустите зависимости:
```bash
docker-compose up -d
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Запустите приложение:
```bash
uvicorn app.main:app --reload
```

## Проверка

- Health check: http://localhost:8000/health
- Docs: http://localhost:8000/docs
- Test auth: http://localhost:8000/api/test (с headers)

## Тест аутентификации

```bash
curl -X GET "http://localhost:8000/api/test" \
  -H "X-API-Token: super_secret_api_token_xyz123" \
  -H "X-User-ID: 123" \
  -H "X-User-Data: {\"name\": \"Test User\"}"
```