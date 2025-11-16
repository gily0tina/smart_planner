# Инструкция по запуску MVP проекта

## Требования

- Docker и Docker Compose установлены на вашей системе
- (Опционально) OpenAI API ключ для использования реального LLM
- (Опционально) Polza AI API ключ для поиска статей по задачам

## Быстрый старт

1. **Клонируйте репозиторий** (если еще не сделано)

2. **Создайте файл `.env`** в корне проекта:
   ```bash
   # OpenAI API (опционально)
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_API_BASE=https://api.openai.com/v1
   LLM_MODEL=gpt-3.5-turbo
   
   # Polza AI API (опционально, для поиска статей)
   POLZA_AI_API_KEY=your_polza_ai_api_key_here
   POLZA_AI_API_BASE=https://api.polza.ai/api/v1
   POLZA_AI_MODEL=perplexity/sonar
   POLZA_AI_TIMEOUT=30
   ```
   
   **Примечание:** Если API ключи не указаны, система будет использовать демо-данные для тестирования.

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
✅ **Поиск статей через Polza AI по каждой задаче**
✅ **Генерация плана на основе найденных статей**
✅ Генерация плана на день с распределением по времени (утро/день/вечер)
✅ Обоснование каждой рекомендации с указанием использованных статей
✅ Ручная коррекция плана (перемещение задач)
✅ Перегенерация плана
✅ Просмотр источников информации (статей)
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

- Система автоматически ищет статьи через Polza AI по названию каждой задачи
- Найденные статьи используются для генерации обоснований и плана
- Если Polza AI API ключ не указан, используются демо-источники
- База данных SQLite сохраняется в Docker volume
- Для использования реального LLM API добавьте `OPENAI_API_KEY` в `.env`
- Для поиска реальных статей добавьте `POLZA_AI_API_KEY` в `.env`

## Настройка Polza AI

1. Получите API ключ от Polza AI
2. Добавьте его в `.env` файл:
   ```
   POLZA_AI_API_KEY=your_api_key_here
   POLZA_AI_API_BASE=https://api.polza.ai/api/v1
   POLZA_AI_MODEL=perplexity/sonar
   POLZA_AI_TIMEOUT=30
   ```

## Как работает поиск статей

Система использует модель **perplexity/sonar** через стандартный эндпойнт Polza AI `/chat/completions`:

1. **Системный промпт** инструктирует модель найти релевантные статьи
2. **Модель** ищет информацию в интернете и возвращает источники
3. **Парсинг ответа** извлекает JSON с источниками или URL из текста
4. **Результат** - список статей с названиями и ссылками

Модель perplexity/sonar специально разработана для поиска информации в интернете и автоматически предоставляет источники.

## Остановка проекта

```bash
docker-compose down
```

Для полной очистки (включая volumes):
```bash
docker-compose down -v
```

