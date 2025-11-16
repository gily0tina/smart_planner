# Настройка Polza AI API

## Обзор

Сервис `PolzaService` интегрирован в систему для поиска статей по задачам пользователя. Статьи используются для генерации обоснований и плана дня.

## Текущая реализация

Сервис находится в `backend/app/llm/polza_service.py` и настроен на работу с универсальным REST API форматом.

## Адаптация под ваш API

Если формат Polza AI API отличается от ожидаемого, вам нужно отредактировать следующие методы:

### 1. Метод `search_articles()`

Этот метод выполняет HTTP запрос к API. Адаптируйте:

- **URL endpoint**: Измените `f"{self.api_base}/search"` на ваш endpoint
- **Метод запроса**: Может быть GET вместо POST
- **Формат payload**: Адаптируйте структуру `payload` под ваш API
- **Заголовки**: Добавьте необходимые заголовки (например, `X-API-Key` вместо `Authorization`)

Пример для GET запроса:
```python
response = requests.get(
    f"{self.api_base}/articles",
    params={"q": query, "limit": limit},
    headers=headers,
    timeout=self.timeout
)
```

### 2. Метод `_parse_articles_response()`

Этот метод парсит ответ от API. Адаптируйте под структуру вашего ответа:

```python
def _parse_articles_response(self, data: dict, query: str) -> List[Source]:
    sources = []
    
    # Адаптируйте под структуру вашего API ответа
    articles = data.get("articles", [])  # Или data.get("results", []) и т.д.
    
    for idx, article in enumerate(articles[:3]):
        source_id = article.get("id", f"polza_{query}_{idx}")
        title = article.get("title", "")  # Адаптируйте поле названия
        link = article.get("url", "")      # Адаптируйте поле ссылки
        
        if link:
            sources.append(Source(
                id=source_id,
                title=title,
                link=link,
                trust=True
            ))
    
    return sources if sources else self._get_demo_sources(query)
```

## Переменные окружения

Убедитесь, что в `.env` файле установлены:

```bash
POLZA_AI_API_KEY=your_api_key_here
POLZA_AI_API_BASE=https://api.polza.ai/v1  # Ваш базовый URL
POLZA_AI_TIMEOUT=30  # Таймаут запроса в секундах
```

## Тестирование

После адаптации API, протестируйте:

1. Создайте задачу в приложении
2. Сгенерируйте план
3. Проверьте, что статьи найдены и отображаются в разделе "Источники"
4. Убедитесь, что обоснования плана ссылаются на найденные статьи

## Fallback режим

Если API ключ не установлен или API недоступен, система автоматически использует демо-источники для тестирования функциональности.

## Логирование

Проверьте логи приложения для отладки:
- Успешные запросы: `logger.info()`
- Ошибки API: `logger.error()`
- Предупреждения: `logger.warning()`

