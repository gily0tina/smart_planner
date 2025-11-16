"""Сервис для работы с Polza AI API - поиск статей"""
import os
import requests
import json
import re
from typing import List, Optional
import logging

from ..models import Source

logger = logging.getLogger(__name__)


class PolzaService:
    """Сервис для поиска статей через Polza AI API"""
    
    def __init__(self):
        self.api_key = os.getenv("POLZA_AI_API_KEY", "")
        self.api_base = os.getenv("POLZA_AI_API_BASE", "https://api.polza.ai/api/v1")
        self.model = os.getenv("POLZA_AI_MODEL", "perplexity/sonar")
        self.timeout = int(os.getenv("POLZA_AI_TIMEOUT", "30"))
        
        logger.info(f"Инициализация PolzaService: API_BASE={self.api_base}, MODEL={self.model}, TIMEOUT={self.timeout}")
        
        if not self.api_key:
            logger.warning("POLZA_AI_API_KEY не установлен. Поиск статей будет использовать демо-данные.")
        else:
            logger.info(f"POLZA_AI_API_KEY установлен (длина: {len(self.api_key)} символов)")
    
    def search_articles(self, query: str, limit: int = 3) -> List[Source]:
        """
        Поиск статей по запросу через Polza AI API с использованием модели perplexity/sonar
        
        Args:
            query: Поисковый запрос (название задачи)
            limit: Максимальное количество статей
            
        Returns:
            Список источников (статей)
        """
        logger.info(f"[POLZA AI] Начало поиска статей: query='{query}', limit={limit}, model={self.model}")
        
        if not self.api_key:
            logger.warning(f"[POLZA AI] API ключ не установлен, возвращаем пустой список для запроса '{query}'")
            return []
        
        try:
            # Используем стандартный эндпойнт chat/completions
            url = f"{self.api_base}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Системный промпт для поиска статей
            system_prompt = self._build_system_prompt(limit)
            
            # Пользовательский запрос
            user_message = f"Найди релевантные статьи и источники по теме: {query}"
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            logger.info(f"[POLZA AI] Отправка запроса: URL={url}, model={self.model}")
            logger.debug(f"[POLZA AI] System prompt: {system_prompt[:200]}...")
            logger.debug(f"[POLZA AI] User message: {user_message}")
            logger.debug(f"[POLZA AI] Headers: Authorization=Bearer ***, Content-Type={headers.get('Content-Type')}")
            
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            logger.info(f"[POLZA AI] Получен ответ: status_code={response.status_code}")
            logger.debug(f"[POLZA AI] Response headers: {dict(response.headers)}")
            
            # Принимаем успешные статусы (200, 201, и другие 2xx)
            if response.ok:  # response.ok проверяет статусы 200-299
                try:
                    data = response.json()
                    logger.info(f"[POLZA AI] Успешный ответ (status {response.status_code}), парсим данные. Структура ответа: {list(data.keys())}")
                    logger.debug(f"[POLZA AI] Полный ответ: {json.dumps(data, ensure_ascii=False, indent=2)[:1000]}")
                    
                    sources = self._parse_llm_response(data, query, limit)
                    logger.info(f"[POLZA AI] Найдено статей: {len(sources)}")
                    for idx, source in enumerate(sources):
                        logger.info(f"[POLZA AI] Статья {idx+1}: {source.title} -> {source.link}")
                    
                    return sources
                except (ValueError, KeyError, json.JSONDecodeError) as e:
                    logger.error(f"[POLZA AI] Ошибка парсинга JSON ответа: {e}")
                    logger.error(f"[POLZA AI] Текст ответа: {response.text[:1000]}")
                    return []
            else:
                logger.error(f"[POLZA AI] Ошибка API: status_code={response.status_code}")
                logger.error(f"[POLZA AI] Текст ответа: {response.text[:500]}")
                return []
                
        except requests.exceptions.Timeout as e:
            logger.error(f"[POLZA AI] Таймаут запроса (>{self.timeout}с): {e}")
            return []
        except requests.exceptions.ConnectionError as e:
            logger.error(f"[POLZA AI] Ошибка подключения к API: {e}")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"[POLZA AI] Ошибка HTTP запроса: {e}")
            logger.exception(e)
            return []
        except Exception as e:
            logger.error(f"[POLZA AI] Неожиданная ошибка при поиске статей: {e}")
            logger.exception(e)
            return []
    
    def _build_system_prompt(self, limit: int = 3) -> str:
        """
        Создает системный промпт для поиска статей
        
        Args:
            limit: Максимальное количество статей
            
        Returns:
            Системный промпт
        """
        return f"""Ты помощник для поиска релевантных статей и источников информации.

Твоя задача:
1. Найти {limit} наиболее релевантных и авторитетных статей/источников по заданной теме
2. Вернуть результат в строгом JSON формате

Формат ответа (обязательно JSON):
{{
  "sources": [
    {{
      "title": "Название статьи",
      "url": "https://ссылка-на-статью.com",
      "description": "Краткое описание статьи"
    }}
  ]
}}

Требования:
- Найди реальные, существующие статьи и источники
- Используй авторитетные источники (научные статьи, проверенные сайты, известные издания)
- Верни ТОЛЬКО валидный JSON, без дополнительного текста
- Если не можешь найти статьи, верни пустой массив sources: []
- Все URL должны быть полными и валидными"""
    
    def _parse_llm_response(self, data: dict, query: str, limit: int = 3) -> List[Source]:
        """
        Парсит ответ от LLM модели и извлекает список источников
        
        Args:
            data: Ответ от API в формате chat completions
            query: Исходный запрос
            limit: Максимальное количество источников
            
        Returns:
            Список источников
        """
        logger.info(f"[POLZA AI] Парсинг ответа LLM для запроса '{query}'")
        logger.debug(f"[POLZA AI] Структура данных: {list(data.keys())}")
        
        sources = []
        
        try:
            # Извлекаем текст ответа из структуры chat completions
            choices = data.get("choices", [])
            if not choices:
                logger.warning(f"[POLZA AI] Нет choices в ответе. Структура: {list(data.keys())}")
                return []
            
            # Берем первый выбор
            message = choices[0].get("message", {})
            content = message.get("content", "")
            
            if not content:
                logger.warning(f"[POLZA AI] Нет content в ответе")
                return []
            
            logger.debug(f"[POLZA AI] Content ответа (первые 500 символов): {content[:500]}")
            
            # Пытаемся извлечь JSON из ответа
            sources_data = self._extract_json_from_response(content)
            
            if not sources_data:
                logger.warning(f"[POLZA AI] Не удалось извлечь JSON из ответа")
                # Пытаемся извлечь ссылки напрямую из текста
                sources_data = self._extract_sources_from_text(content, query)
            
            # Парсим источники
            if sources_data and "sources" in sources_data:
                articles = sources_data["sources"]
                logger.info(f"[POLZA AI] Найдено {len(articles)} источников в JSON")
                
                for idx, article in enumerate(articles[:limit]):
                    title = article.get("title", article.get("name", f"Статья по теме: {query}"))
                    url = article.get("url", article.get("link", article.get("href", "")))
                    
                    if url:
                        source_id = article.get("id", f"polza_{query}_{idx}")
                        sources.append(Source(
                            id=source_id,
                            title=title,
                            link=url,
                            trust=True
                        ))
                        logger.info(f"[POLZA AI] Добавлена статья: '{title}' -> {url}")
                    else:
                        logger.warning(f"[POLZA AI] Статья {idx+1} пропущена: нет URL. Данные: {article}")
            
            if not sources:
                logger.warning(f"[POLZA AI] Не удалось извлечь источники из ответа, возвращаем пустой список")
                return []
            
            logger.info(f"[POLZA AI] Успешно извлечено {len(sources)} статей")
            return sources
            
        except Exception as e:
            logger.error(f"[POLZA AI] Ошибка парсинга ответа LLM: {e}")
            logger.exception(e)
            return []
    
    def _extract_json_from_response(self, content: str) -> Optional[dict]:
        """
        Извлекает JSON из текстового ответа модели
        
        Args:
            content: Текст ответа
            
        Returns:
            Распарсенный JSON или None
        """
        try:
            # Пытаемся найти JSON блок в тексте
            # Ищем паттерн ```json ... ```
            json_pattern = r'```json\s*(\{.*?\})\s*```'
            match = re.search(json_pattern, content, re.DOTALL)
            if match:
                json_str = match.group(1)
                logger.debug(f"[POLZA AI] Найден JSON в блоке ```json: {json_str[:200]}")
                return json.loads(json_str)
            
            # Ищем JSON объект, начинающийся с {
            # Находим первую { и последнюю }
            start_idx = content.find('{')
            if start_idx != -1:
                # Находим соответствующую закрывающую скобку
                brace_count = 0
                end_idx = start_idx
                for i in range(start_idx, len(content)):
                    if content[i] == '{':
                        brace_count += 1
                    elif content[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break
                
                if end_idx > start_idx:
                    json_str = content[start_idx:end_idx]
                    logger.debug(f"[POLZA AI] Извлечен JSON из текста: {json_str[:200]}")
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        pass
            
            # Пытаемся распарсить весь контент как JSON
            return json.loads(content)
            
        except json.JSONDecodeError as e:
            logger.debug(f"[POLZA AI] Ошибка парсинга JSON: {e}")
            return None
    
    def _extract_sources_from_text(self, content: str, query: str) -> Optional[dict]:
        """
        Извлекает источники из текста, если JSON не найден
        Пытается найти URL и названия статей
        
        Args:
            content: Текст ответа
            query: Исходный запрос
            
        Returns:
            Словарь с источниками или None
        """
        import uuid
        
        # Ищем URL в тексте
        url_pattern = r'https?://[^\s\)]+'
        urls = re.findall(url_pattern, content)
        
        if not urls:
            return None
        
        sources = []
        for idx, url in enumerate(urls[:3]):
            # Пытаемся найти название статьи рядом с URL
            # Ищем текст перед URL
            title_match = re.search(r'([^\n]+?)\s+' + re.escape(url), content)
            title = title_match.group(1).strip() if title_match else f"Статья по теме: {query}"
            
            # Очищаем название от лишних символов
            title = re.sub(r'^[-•*]\s*', '', title)
            title = title[:200]  # Ограничиваем длину
            
            sources.append({
                "id": f"extracted_{uuid.uuid4().hex[:8]}",
                "title": title,
                "url": url
            })
        
        return {"sources": sources} if sources else None
    
    def search_articles_for_tasks(self, tasks: List) -> List[Source]:
        """
        Поиск статей для списка задач
        
        Args:
            tasks: Список задач (объекты Task)
            
        Returns:
            Список всех найденных источников
        """
        logger.info(f"[POLZA AI] Начало поиска статей для {len(tasks)} задач")
        
        all_sources = []
        seen_links = set()  # Для избежания дубликатов
        
        for idx, task in enumerate(tasks):
            logger.info(f"[POLZA AI] Обработка задачи {idx+1}/{len(tasks)}: '{task.title}' (категория: {task.category})")
            
            # Формируем поисковый запрос на основе названия задачи
            query = task.title
            
            # Можно добавить категорию для более точного поиска
            if task.category:
                query = f"{task.title} {task.category}"
            
            logger.info(f"[POLZA AI] Поисковый запрос для задачи '{task.title}': '{query}'")
            
            articles = self.search_articles(query, limit=2)
            
            logger.info(f"[POLZA AI] Для задачи '{task.title}' найдено {len(articles)} статей")
            
            # Добавляем только уникальные источники
            for article in articles:
                if article.link not in seen_links:
                    all_sources.append(article)
                    seen_links.add(article.link)
                    logger.debug(f"[POLZA AI] Добавлен уникальный источник: {article.title}")
                else:
                    logger.debug(f"[POLZA AI] Источник уже существует, пропускаем: {article.link}")
        
        logger.info(f"[POLZA AI] Итого найдено уникальных источников: {len(all_sources)}")
        return all_sources
    
    def rank_task_by_time(self, task_keyword: str) -> dict:
        """
        Определяет оптимальное время суток для выполнения задачи на основе научных источников
        
        Args:
            task_keyword: Ключевое слово задачи (название задачи)
            
        Returns:
            Словарь с полями:
            - answer: "morning", "afternoon" или "evening" (на английском для консистентности)
            - sources: список словарей с полями url, title, summarize
            - justification: обоснование на русском
        """
        logger.info(f"[POLZA AI] Ранжирование задачи по времени суток: keyword='{task_keyword}'")
        
        if not self.api_key:
            logger.warning(f"[POLZA AI] API ключ не установлен, возвращаем дефолтное значение для '{task_keyword}'")
            return {
                "answer": "afternoon",
                "sources": [],
                "justification": "Не удалось определить оптимальное время из-за отсутствия API ключа"
            }
        
        try:
            # Формируем промпт с подстановкой keyword
            user_prompt = self._build_time_ranking_prompt(task_keyword)
            
            url = f"{self.api_base}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 3000
            }
            
            logger.info(f"[POLZA AI] Отправка запроса для ранжирования задачи '{task_keyword}'")
            logger.debug(f"[POLZA AI] Промпт: {user_prompt[:300]}...")
            
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            logger.info(f"[POLZA AI] Получен ответ для ранжирования: status_code={response.status_code}")
            
            if response.ok:
                try:
                    data = response.json()
                    result = self._parse_time_ranking_response(data, task_keyword)
                    logger.info(f"[POLZA AI] Результат ранжирования для '{task_keyword}': {result.get('answer')}, источников: {len(result.get('sources', []))}")
                    return result
                except (ValueError, KeyError, json.JSONDecodeError) as e:
                    logger.error(f"[POLZA AI] Ошибка парсинга JSON ответа для ранжирования: {e}")
                    logger.error(f"[POLZA AI] Текст ответа: {response.text[:1000]}")
                    return {
                        "answer": "afternoon",
                        "sources": [],
                        "justification": f"Ошибка при определении оптимального времени: {str(e)}"
                    }
            else:
                logger.error(f"[POLZA AI] Ошибка API при ранжировании: status_code={response.status_code}")
                logger.error(f"[POLZA AI] Текст ответа: {response.text[:500]}")
                return {
                    "answer": "afternoon",
                    "sources": [],
                    "justification": "Не удалось определить оптимальное время из-за ошибки API"
                }
                
        except requests.exceptions.Timeout as e:
            logger.error(f"[POLZA AI] Таймаут запроса для ранжирования (>{self.timeout}с): {e}")
            return {
                "answer": "afternoon",
                "sources": [],
                "justification": "Таймаут при определении оптимального времени"
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"[POLZA AI] Ошибка HTTP запроса для ранжирования: {e}")
            return {
                "answer": "afternoon",
                "sources": [],
                "justification": f"Ошибка подключения: {str(e)}"
            }
        except Exception as e:
            logger.error(f"[POLZA AI] Неожиданная ошибка при ранжировании: {e}")
            logger.exception(e)
            return {
                "answer": "afternoon",
                "sources": [],
                "justification": f"Неожиданная ошибка: {str(e)}"
            }
    
    def _build_time_ranking_prompt(self, keyword: str) -> str:
        """
        Создает промпт для ранжирования задачи по времени суток
        
        Args:
            keyword: Ключевое слово задачи
            
        Returns:
            Промпт с подстановкой keyword
        """
        prompt = f"""в какое время суток лучшего всего выполнять {keyword} (можно выбрать только из утро, обед и вечер)? Найди пять источников, которые подтверждают твой ответ, сделай summarize этих статей в контексте нашей задачи. Свой ответ дай в виде json. Структура ответа: {{ "answer": "morning", "sources": [ {{"url":"someurl", "title":"title", "summarize":"summarize"}}, {{"url":"someurl", "title":"title", "summarize":"summarize"}} ... etc ] }}

Важно:
- answer должен быть одним из: "morning" (для утра), "afternoon" (для обеда), "evening" (для вечера)
- sources должен содержать ровно 5 источников
- Каждый источник должен иметь url, title и summarize
- Верни ТОЛЬКО валидный JSON, без дополнительного текста"""
        return prompt
    
    def _parse_time_ranking_response(self, data: dict, keyword: str) -> dict:
        """
        Парсит ответ от LLM для ранжирования по времени суток
        
        Args:
            data: Ответ от API в формате chat completions
            keyword: Исходное ключевое слово
            
        Returns:
            Словарь с answer, sources и justification
        """
        logger.info(f"[POLZA AI] Парсинг ответа ранжирования для '{keyword}'")
        
        try:
            # Извлекаем текст ответа
            choices = data.get("choices", [])
            if not choices:
                logger.warning(f"[POLZA AI] Нет choices в ответе ранжирования")
                return {
                    "answer": "afternoon",
                    "sources": [],
                    "justification": "Не удалось получить ответ от модели"
                }
            
            message = choices[0].get("message", {})
            content = message.get("content", "")
            
            if not content:
                logger.warning(f"[POLZA AI] Нет content в ответе ранжирования")
                return {
                    "answer": "afternoon",
                    "sources": [],
                    "justification": "Пустой ответ от модели"
                }
            
            logger.debug(f"[POLZA AI] Content ответа ранжирования (первые 500 символов): {content[:500]}")
            
            # Извлекаем JSON из ответа
            ranking_data = self._extract_json_from_response(content)
            
            if not ranking_data:
                logger.warning(f"[POLZA AI] Не удалось извлечь JSON из ответа ранжирования")
                return {
                    "answer": "afternoon",
                    "sources": [],
                    "justification": "Не удалось распарсить ответ модели"
                }
            
            # Извлекаем answer
            answer = ranking_data.get("answer", "afternoon").lower()
            
            # Маппинг ответов: morning -> утро, afternoon -> день, evening -> вечер
            answer_mapping = {
                "morning": "утро",
                "afternoon": "день",
                "evening": "вечер"
            }
            
            # Нормализуем answer
            if answer not in answer_mapping:
                # Пытаемся найти похожий
                if "утро" in answer or "morning" in answer:
                    answer = "morning"
                elif "обед" in answer or "afternoon" in answer or "день" in answer:
                    answer = "afternoon"
                elif "вечер" in answer or "evening" in answer:
                    answer = "evening"
                else:
                    answer = "afternoon"  # Дефолт
            
            # Извлекаем sources
            sources = ranking_data.get("sources", [])
            
            # Формируем обоснование
            time_ru = answer_mapping.get(answer, "день")
            if sources:
                sources_count = len(sources)
                justification = f"На основе {sources_count} научных источников оптимальное время для '{keyword}' - {time_ru}."
            else:
                justification = f"Оптимальное время для '{keyword}' - {time_ru}."
            
            result = {
                "answer": answer,
                "sources": sources,
                "justification": justification
            }
            
            logger.info(f"[POLZA AI] Успешно распарсен ответ ранжирования: answer={answer}, sources={len(sources)}")
            return result
            
        except Exception as e:
            logger.error(f"[POLZA AI] Ошибка парсинга ответа ранжирования: {e}")
            logger.exception(e)
            return {
                "answer": "afternoon",
                "sources": [],
                "justification": f"Ошибка при обработке ответа: {str(e)}"
            }

