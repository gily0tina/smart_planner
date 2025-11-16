"""Модуль работы с LLM"""
import os
from typing import List, Optional, Tuple
import json

from ..models import Task, PlanItem, TimeBlock, Source, UserProfile, Chronotype


class LLMService:
    """Сервис для работы с LLM API"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        
        # Демо-источники для MVP
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
        Генерирует план на день с помощью LLM
        
        Для MVP использует простую логику распределения,
        в продакшене здесь будет вызов LLM API
        """
        plan_items = []
        
        # Простая логика распределения для MVP
        # В реальной версии здесь будет вызов LLM API
        
        for i, task in enumerate(tasks):
            # Определяем временной блок на основе категории и настроения
            if task.category.lower() in ["спорт", "зарядка", "йога"]:
                time_block = TimeBlock.MORNING
                justification = "Физическая активность лучше всего подходит для утра, когда организм полон энергии"
            elif task.category.lower() in ["работа", "встречи", "проекты"]:
                time_block = TimeBlock.DAY
                justification = "Рабочие задачи оптимальны в дневное время, когда концентрация на пике"
            elif task.category.lower() in ["отдых", "чтение", "хобби"]:
                time_block = TimeBlock.EVENING
                justification = "Спокойные занятия идеальны для вечера, помогают расслабиться"
            else:
                # Распределяем по порядку
                if i % 3 == 0:
                    time_block = TimeBlock.MORNING
                    justification = "Задача размещена в утренний блок для оптимального распределения нагрузки"
                elif i % 3 == 1:
                    time_block = TimeBlock.DAY
                    justification = "Задача размещена в дневной блок для оптимального распределения нагрузки"
                else:
                    time_block = TimeBlock.EVENING
                    justification = "Задача размещена в вечерний блок для оптимального распределения нагрузки"
            
            # Учитываем предпочтения пользователя
            if task.preferred_time:
                time_block = task.preferred_time
                justification = f"Размещено согласно вашему предпочтению ({time_block.value})"
            
            # Учитываем историю правок из профиля
            if user_profile and task.id in user_profile.task_shifting_history:
                history = user_profile.task_shifting_history[task.id]
                if history:
                    # Берем последнее предпочтение
                    last_pref = history[-1]
                    try:
                        time_block = TimeBlock(last_pref)
                        justification = f"Учтено ваше предыдущее предпочтение ({time_block.value})"
                    except:
                        pass
            
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
        
        return plan_items, self.demo_sources
    
    async def generate_plan_with_llm(self, tasks: List[Task], user_profile: Optional[UserProfile] = None) -> Tuple[List[PlanItem], List[Source]]:
        """
        Генерирует план с использованием реального LLM API
        
        Для MVP пока использует простую логику, но структура готова для интеграции
        """
        # TODO: Реализовать вызов OpenAI/OpenRouter API
        # Пример структуры запроса:
        # prompt = f"""Ты - помощник по планированию дня. Распредели следующие задачи по времени суток (утро/день/вечер):
        # Задачи: {json.dumps([{"title": t.title, "category": t.category, "mood": t.mood} for t in tasks], ensure_ascii=False)}
        # Учти хронотип пользователя: {user_profile.chronotype if user_profile and user_profile.chronotype else "не определен"}
        # Верни JSON с распределением задач и обоснованием для каждой."""
        
        return self.generate_plan(tasks, user_profile)

