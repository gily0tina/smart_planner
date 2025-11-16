"""Модуль работы с LLM"""
import os
from typing import List, Optional, Tuple
import json
import logging
import requests
import uuid

from ..models import Task, PlanItem, TimeBlock, Source, UserProfile, Chronotype
from .polza_service import PolzaService

logger = logging.getLogger(__name__)


class LLMService:
    """Сервис для работы с LLM API"""
    
    def __init__(self):
        # Используем настройки Polza AI вместо OpenAI
        self.api_key = os.getenv("POLZA_AI_API_KEY", "")
        self.api_base = os.getenv("POLZA_AI_API_BASE", "https://api.polza.ai/api/v1")
        self.model = os.getenv("POLZA_AI_MODEL", "perplexity/sonar")
        self.timeout = int(os.getenv("POLZA_AI_TIMEOUT", "30"))
        
        # Инициализируем сервис Polza AI для поиска статей
        self.polza_service = PolzaService()
        
        # Демо-источники для MVP (используются как fallback)
        self.demo_sources = [
            Source(
                id="source1",
                title="Биоритмы и продуктивность",
                link="https://example.com/biorhythms",
                trust=True
            ),
            Source(
                id="source2",
                title="Хронотипы и планирование дня",
                link="https://example.com/chronotypes",
                trust=True
            )
        ]
    
    def generate_plan(self, tasks: List[Task], user_profile: Optional[UserProfile] = None) -> Tuple[List[PlanItem], List[Source]]:
        """
        Генерирует план на день с помощью LLM на основе статей из Polza AI
        
        Процесс:
        1. Ищет статьи по каждой задаче через Polza AI
        2. Генерирует план на основе найденных статей и задач
        3. Возвращает план и список источников (статей)
        """
        # Шаг 1: Поиск статей по задачам через Polza AI
        logger.info(f"[LLM] Начало генерации плана для {len(tasks)} задач")
        logger.info(f"[LLM] Список задач: {[f'{t.title} ({t.category})' for t in tasks]}")
        
        logger.info(f"[LLM] Поиск статей для {len(tasks)} задач через Polza AI...")
        sources = self.polza_service.search_articles_for_tasks(tasks)
        logger.info(f"[LLM] Найдено {len(sources)} статей от Polza AI")
        
        # Логируем найденные источники
        for idx, source in enumerate(sources):
            logger.info(f"[LLM] Источник {idx+1}: {source.title} -> {source.link}")
        
        # Если статей не найдено, возвращаем пустой список
        if not sources:
            logger.warning("[LLM] Статьи не найдены, возвращаем пустой список источников")
        
        # Шаг 2: Генерация плана на основе статей и задач
        plan_items = []
        
        # Формируем информацию о статьях для использования в генерации
        articles_info = "\n".join([f"- {s.title}: {s.link}" for s in sources])
        
        # Генерируем план для каждой задачи
        for i, task in enumerate(tasks):
            # Ищем статьи, связанные с этой задачей
            task_articles = [
                s for s in sources 
                if task.title.lower() in s.title.lower() or 
                   task.category.lower() in s.title.lower()
            ]
            
            # Если нет специфичных статей, берем общие
            if not task_articles:
                task_articles = sources[:2] if sources else []
            
            # Генерируем обоснование на основе статей
            if task_articles:
                articles_titles = ", ".join([a.title for a in task_articles])
                justification_base = f"На основе статей: {articles_titles}. "
            else:
                justification_base = ""
            
            # Определяем временной блок на основе ранжирования через Polza AI
            time_block, time_justification, ranking_sources = self._determine_time_block(
                task, user_profile, task_articles
            )
            
            # Добавляем источники из ранжирования к общему списку источников
            if ranking_sources:
                sources.extend(ranking_sources)
            
            justification = justification_base + time_justification
            
            # Убеждаемся, что task.id установлен
            if not task.id:
                import uuid
                task.id = str(uuid.uuid4())
            
            plan_items.append(PlanItem(
                task_id=task.id,
                task_title=task.title,
                task_category=task.category,
                task_mood=task.mood,
                time_block=time_block,
                justification=justification
            ))
            
            logger.debug(f"[LLM] Создан план для задачи '{task.title}': {time_block.value}")
        
        logger.info(f"[LLM] Генерация плана завершена: создано {len(plan_items)} элементов плана, {len(sources)} источников")
        logger.info(f"[LLM] Возвращаемые источники: {[s.title for s in sources]}")
        
        return plan_items, sources
    
    def _determine_time_block(
        self, 
        task: Task, 
        user_profile: Optional[UserProfile],
        articles: List[Source]
    ) -> Tuple[TimeBlock, str, List[Source]]:
        """
        Определяет временной блок для задачи на основе:
        - Предпочтений пользователя (приоритет 1)
        - Истории правок (приоритет 2)
        - Ранжирования через Polza AI с научными источниками (приоритет 3)
        
        Returns:
            Кортеж (TimeBlock, обоснование, список источников из ранжирования)
        """
        # Приоритет 1: Предпочтения пользователя
        if task.preferred_time:
            return task.preferred_time, f"Размещено согласно вашему предпочтению ({task.preferred_time.value})", []
        
        # Приоритет 2: История правок из профиля
        if user_profile and task.id in user_profile.task_shifting_history:
            history = user_profile.task_shifting_history[task.id]
            if history:
                last_pref = history[-1]
                try:
                    time_block = TimeBlock(last_pref)
                    return time_block, f"Учтено ваше предыдущее предпочтение ({time_block.value})", []
                except:
                    pass
        
        # Приоритет 3: Ранжирование через Polza AI с использованием нового промпта
        logger.info(f"[LLM] Использование ранжирования через Polza AI для задачи '{task.title}'")
        ranking_result = self.polza_service.rank_task_by_time(task.title)
        
        # Маппинг ответа на TimeBlock
        answer = ranking_result.get("answer", "afternoon").lower()
        answer_to_timeblock = {
            "morning": TimeBlock.MORNING,
            "afternoon": TimeBlock.DAY,
            "evening": TimeBlock.EVENING
        }
        
        time_block = answer_to_timeblock.get(answer, TimeBlock.DAY)
        justification = ranking_result.get("justification", f"Задача размещена в {time_block.value}.")
        
        # Преобразуем источники из ранжирования в формат Source
        ranking_sources = []
        sources_data = ranking_result.get("sources", [])
        
        for idx, source_data in enumerate(sources_data):
            source_id = f"ranking_{task.id}_{idx}" if task.id else f"ranking_{idx}"
            url = source_data.get("url", "")
            title = source_data.get("title", f"Источник {idx+1}")
            
            if url:  # Добавляем только если есть URL
                ranking_sources.append(Source(
                    id=source_id,
                    title=title,
                    link=url,
                    trust=True
                ))
                logger.debug(f"[LLM] Добавлен источник из ранжирования: {title} -> {url}")
        
        logger.info(f"[LLM] Ранжирование завершено: {time_block.value}, источников: {len(ranking_sources)}")
        
        return time_block, justification, ranking_sources
    
    async def generate_plan_with_llm(self, tasks: List[Task], user_profile: Optional[UserProfile] = None) -> Tuple[List[PlanItem], List[Source]]:
        """
        Генерирует план с использованием Polza AI API
        
        Использует LLM для генерации плана на основе задач и профиля пользователя
        """
        logger.info(f"[LLM] Начало генерации плана через Polza AI для {len(tasks)} задач")
        
        if not self.api_key:
            logger.warning("[LLM] POLZA_AI_API_KEY не установлен, используем fallback метод")
            return self.generate_plan(tasks, user_profile)
        
        if not tasks:
            logger.warning("[LLM] Список задач пуст")
            return [], []
        
        try:
            # Формируем промпт для генерации плана
            prompt = self._build_plan_generation_prompt(tasks, user_profile)
            
            # Вызываем Polza AI API
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
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 3000
            }
            
            logger.info(f"[LLM] Отправка запроса к Polza AI: URL={url}, model={self.model}")
            logger.debug(f"[LLM] Промпт (первые 500 символов): {prompt[:500]}...")
            
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            logger.info(f"[LLM] Получен ответ от Polza AI: status_code={response.status_code}")
            
            if not response.ok:
                logger.error(f"[LLM] Ошибка API: status_code={response.status_code}, текст: {response.text[:500]}")
                # Fallback на обычный метод
                return self.generate_plan(tasks, user_profile)
            
            # Парсим ответ
            data = response.json()
            plan_items, sources = self._parse_plan_response(data, tasks, user_profile)
            
            logger.info(f"[LLM] Генерация плана через Polza AI завершена: создано {len(plan_items)} элементов плана")
            
            return plan_items, sources
            
        except requests.exceptions.Timeout as e:
            logger.error(f"[LLM] Таймаут запроса к Polza AI: {e}")
            return self.generate_plan(tasks, user_profile)
        except requests.exceptions.RequestException as e:
            logger.error(f"[LLM] Ошибка HTTP запроса к Polza AI: {e}")
            return self.generate_plan(tasks, user_profile)
        except Exception as e:
            logger.error(f"[LLM] Неожиданная ошибка при генерации плана через Polza AI: {e}")
            logger.exception(e)
            return self.generate_plan(tasks, user_profile)
    
    def _build_plan_generation_prompt(self, tasks: List[Task], user_profile: Optional[UserProfile] = None) -> str:
        """
        Создает промпт для генерации плана через LLM
        
        Args:
            tasks: Список задач
            user_profile: Профиль пользователя
            
        Returns:
            Промпт для LLM
        """
        tasks_json = json.dumps(
            [{"title": t.title, "category": t.category, "mood": t.mood} for t in tasks],
            ensure_ascii=False,
            indent=2
        )
        
        chronotype_info = "не определен"
        if user_profile and user_profile.chronotype:
            chronotype_info = "жаворонок" if user_profile.chronotype == Chronotype.LARK else "сова"
        
        prompt = f"""Ты - помощник по планированию дня. Распредели следующие задачи по времени суток (утро, день, вечер):

Задачи:
{tasks_json}

Хронотип пользователя: {chronotype_info}

Для каждой задачи определи оптимальное время суток на основе:
1. Категории и настроения задачи
2. Хронотипа пользователя
3. Научных данных о продуктивности в разное время суток
4. ЛОГИЧЕСКОЙ СОГЛАСОВАННОСТИ между задачами

ВАЖНО - учитывай логические связи между задачами:
- Задачи, связанные с транспортом (машина в гараж, поездка куда-то) логичнее ставить на вечер
- Медицинские процедуры (массаж, косметолог, диетолог) обычно днем
- Физические активности (йога, спорт) - утром или вечером в зависимости от типа
- Распределяй задачи так, чтобы они логично сочетались друг с другом в течение дня
- Учитывай последовательность: например, если есть несколько задач в одном месте, группируй их вместе

Верни ответ в виде JSON со следующей структурой:
{{
  "plan": [
    {{
      "task_title": "название задачи",
      "time_block": "утро" | "день" | "вечер",
      "justification": "обоснование размещения задачи в это время с учетом согласованности с другими задачами"
    }}
  ],
  "sources": [
    {{
      "title": "название источника",
      "url": "ссылка на источник",
      "description": "описание источника"
    }}
  ]
}}

Важно:
- time_block должен быть одним из: "утро", "день", "вечер"
- Верни ТОЛЬКО валидный JSON, без дополнительного текста
- sources должен содержать релевантные научные источники о планировании дня и продуктивности
- Обязательно учитывай логическую согласованность задач между собой"""
        
        return prompt
    
    def _parse_plan_response(self, data: dict, tasks: List[Task], user_profile: Optional[UserProfile] = None) -> Tuple[List[PlanItem], List[Source]]:
        """
        Парсит ответ от LLM и создает план
        
        Args:
            data: Ответ от API в формате chat completions
            tasks: Исходный список задач
            user_profile: Профиль пользователя
            
        Returns:
            Кортеж (список PlanItem, список Source)
        """
        logger.info("[LLM] Парсинг ответа от Polza AI")
        
        plan_items = []
        sources = []
        
        try:
            # Извлекаем текст ответа
            choices = data.get("choices", [])
            if not choices:
                logger.warning("[LLM] Нет choices в ответе, используем fallback")
                return self.generate_plan(tasks, user_profile)
            
            message = choices[0].get("message", {})
            content = message.get("content", "")
            
            if not content:
                logger.warning("[LLM] Пустой ответ, используем fallback")
                return self.generate_plan(tasks, user_profile)
            
            logger.debug(f"[LLM] Content ответа (первые 500 символов): {content[:500]}")
            
            # Извлекаем JSON из ответа
            plan_data = self._extract_json_from_response(content)
            
            if not plan_data:
                logger.warning("[LLM] Не удалось извлечь JSON из ответа, используем fallback")
                return self.generate_plan(tasks, user_profile)
            
            # Парсим план
            plan_items_data = plan_data.get("plan", [])
            sources_data = plan_data.get("sources", [])
            
            # Создаем словарь задач по названию для быстрого поиска
            tasks_dict = {task.title: task for task in tasks}
            
            # Создаем PlanItem'ы
            for item_data in plan_items_data:
                task_title = item_data.get("task_title", "")
                task = tasks_dict.get(task_title)
                
                if not task:
                    # Пытаемся найти задачу по частичному совпадению
                    for t in tasks:
                        if task_title.lower() in t.title.lower() or t.title.lower() in task_title.lower():
                            task = t
                            break
                
                if not task:
                    logger.warning(f"[LLM] Не найдена задача '{task_title}', пропускаем")
                    continue
                
                # Убеждаемся, что task.id установлен
                if not task.id:
                    task.id = str(uuid.uuid4())
                
                # Маппинг time_block
                time_block_str = item_data.get("time_block", "день").lower()
                time_block_mapping = {
                    "утро": TimeBlock.MORNING,
                    "день": TimeBlock.DAY,
                    "обед": TimeBlock.DAY,
                    "вечер": TimeBlock.EVENING
                }
                time_block = time_block_mapping.get(time_block_str, TimeBlock.DAY)
                
                justification = item_data.get("justification", f"Задача размещена в {time_block.value}.")
                
                plan_items.append(PlanItem(
                    task_id=task.id,
                    task_title=task.title,
                    task_category=task.category,
                    task_mood=task.mood,
                    time_block=time_block,
                    justification=justification
                ))
                
                logger.debug(f"[LLM] Создан PlanItem для задачи '{task.title}': {time_block.value}")
            
            # Создаем Source'ы
            for idx, source_data in enumerate(sources_data):
                source_id = f"llm_{idx}"
                title = source_data.get("title", f"Источник {idx+1}")
                url = source_data.get("url", source_data.get("link", ""))
                
                if url:
                    sources.append(Source(
                        id=source_id,
                        title=title,
                        link=url,
                        trust=True
                    ))
                    logger.debug(f"[LLM] Добавлен источник: {title} -> {url}")
            
            # Если план пустой, используем fallback
            if not plan_items:
                logger.warning("[LLM] План пустой после парсинга, используем fallback")
                return self.generate_plan(tasks, user_profile)
            
            logger.info(f"[LLM] Успешно распарсен план: {len(plan_items)} элементов, {len(sources)} источников")
            return plan_items, sources
            
        except Exception as e:
            logger.error(f"[LLM] Ошибка парсинга ответа: {e}")
            logger.exception(e)
            return self.generate_plan(tasks, user_profile)
    
    def _extract_json_from_response(self, content: str) -> Optional[dict]:
        """
        Извлекает JSON из текстового ответа модели
        
        Args:
            content: Текст ответа
            
        Returns:
            Распарсенный JSON или None
        """
        import re
        
        try:
            # Пытаемся найти JSON блок в тексте
            # Ищем паттерн ```json ... ```
            json_pattern = r'```json\s*(\{.*?\})\s*```'
            match = re.search(json_pattern, content, re.DOTALL)
            if match:
                json_str = match.group(1)
                logger.debug(f"[LLM] Найден JSON в блоке ```json: {json_str[:200]}")
                return json.loads(json_str)
            
            # Ищем JSON объект, начинающийся с {
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
                    logger.debug(f"[LLM] Извлечен JSON из текста: {json_str[:200]}")
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        pass
            
            # Пытаемся распарсить весь контент как JSON
            return json.loads(content)
            
        except json.JSONDecodeError as e:
            logger.debug(f"[LLM] Ошибка парсинга JSON: {e}")
            return None

