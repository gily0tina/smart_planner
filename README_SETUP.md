# Инструкция по запуску MVP проекта

## Требования

- Docker и Docker Compose установлены на вашей системе
- (Опционально) OpenAI API ключ для использования реального LLM

## Быстрый старт

1. **Клонируйте репозиторий** (если еще не сделано)

2. **Создайте файл `.env`** на основе `.env.example`:
   ```bash
   cp .env.example .env
   ```
   
   Отредактируйте `.env` и добавьте ваш OpenAI API ключ (опционально, для MVP можно оставить пустым)

3. **Запустите проект через Docker Compose**:
   ```bash
   docker-compose up --build
   ```

4. **Откройте в браузере**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API документация: http://localhost:8000/docs

## Структура проекта

```
smart_planner/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── domain/      # Бизнес-логика
│   │   ├── llm/         # LLM сервис
│   │   ├── data/        # Работа с БД
│   │   └── models.py    # Модели данных
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/            # React frontend
│   ├── src/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Основные функции MVP

✅ Добавление задач (название, категория, эмоциональный окрас)
✅ Генерация плана на день с распределением по времени (утро/день/вечер)
✅ Обоснование каждой рекомендации
✅ Ручная коррекция плана (перемещение задач)
✅ Перегенерация плана
✅ Просмотр источников информации
✅ Отметка источников как недоверенных
✅ Определение хронотипа на основе поведения пользователя

## API Endpoints

- `POST /api/tasks` - Создать задачу
- `GET /api/tasks` - Получить все задачи
- `POST /api/plan/generate` - Сгенерировать план
- `POST /api/plan/regenerate` - Перегенерировать план
- `PUT /api/plan/update` - Обновить время задачи
- `GET /api/sources` - Получить источники
- `POST /api/sources/{id}/untrust` - Пометить источник как недоверенный
- `GET /api/profile` - Получить профиль пользователя

## Примечания

- Для MVP используется простая логика распределения задач (без реального LLM)
- База данных SQLite сохраняется в Docker volume
- Для использования реального LLM API добавьте `OPENAI_API_KEY` в `.env`

## Остановка проекта

```bash
docker-compose down
```

Для полной очистки (включая volumes):
```bash
docker-compose down -v
```

