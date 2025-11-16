"""Domain модуль - основная бизнес-логика"""
from typing import List, Optional
from ..models import Task, PlanItem, DayPlan, UserProfile, TimeBlock, TaskCreate, Chronotype
from ..data.database import Database
from ..llm.llm_service import LLMService


class PlannerService:
    """Сервис планирования - главный модуль бизнес-логики"""
    
    def __init__(self):
        self.db = Database()
        self.llm = LLMService()
    
    def create_task(self, task_data: TaskCreate) -> Task:
        """Создать задачу"""
        import uuid
        task = Task(
            id=str(uuid.uuid4()),
            title=task_data.title,
            category=task_data.category,
            mood=task_data.mood
        )
        self.db.save_task(task)
        return task
    
    def get_all_tasks(self) -> List[Task]:
        """Получить все задачи"""
        return self.db.get_tasks()
    
    def generate_plan(self, task_ids: Optional[List[str]] = None) -> DayPlan:
        """Сгенерировать план на день"""
        # Получаем задачи
        all_tasks = self.db.get_tasks()
        tasks = all_tasks if not task_ids else [t for t in all_tasks if t.id in task_ids]
        
        if not tasks:
            return DayPlan()
        
        # Получаем профиль пользователя
        user_profile = self.db.get_user_profile()
        
        # Генерируем план через LLM
        plan_items, sources = self.llm.generate_plan(tasks, user_profile)
        
        # Сохраняем план
        self.db.save_plan(plan_items)
        
        # Сохраняем источники
        for source in sources:
            self.db.save_source(source)
        
        # Группируем по временным блокам
        # Используем сравнение по значению для надежности
        morning = [item for item in plan_items if item.time_block.value == TimeBlock.MORNING.value]
        day = [item for item in plan_items if item.time_block.value == TimeBlock.DAY.value]
        evening = [item for item in plan_items if item.time_block.value == TimeBlock.EVENING.value]
        
        return DayPlan(
            morning=morning,
            day=day,
            evening=evening,
            sources=sources
        )
    
    def update_task_time(self, task_id: str, new_time_block: TimeBlock):
        """Обновить время задачи (ручная правка)"""
        tasks = self.db.get_tasks()
        task = next((t for t in tasks if t.id == task_id), None)
        
        if not task:
            raise ValueError(f"Задача {task_id} не найдена")
        
        # Сохраняем историю правок
        user_profile = self.db.get_user_profile()
        
        if task_id not in user_profile.task_shifting_history:
            user_profile.task_shifting_history[task_id] = []
        
        # Получаем текущее время задачи из последнего плана
        # Для упрощения MVP просто добавляем новое время
        user_profile.task_shifting_history[task_id].append(new_time_block.value)
        
        # Обновляем предпочтение задачи
        task.preferred_time = new_time_block
        self.db.save_task(task)
        
        # Сохраняем историю
        self.db.save_edit_history(task_id, None, new_time_block.value)
        
        # Обновляем профиль
        self.db.update_user_profile(user_profile)
        
        # Определяем хронотип на основе истории
        self._update_chronotype(user_profile)
    
    def _update_chronotype(self, profile: UserProfile):
        """Обновить хронотип на основе истории"""
        # Простая логика: если пользователь часто переносит задачи на утро - жаворонок
        # Если на вечер - сова
        morning_count = sum(1 for history in profile.task_shifting_history.values() 
                          for time in history if time == TimeBlock.MORNING.value)
        evening_count = sum(1 for history in profile.task_shifting_history.values() 
                          for time in history if time == TimeBlock.EVENING.value)
        
        if morning_count > evening_count + 2:
            profile.chronotype = Chronotype.LARK
        elif evening_count > morning_count + 2:
            profile.chronotype = Chronotype.OWL
        
        self.db.update_user_profile(profile)
    
    def mark_source_untrusted(self, source_id: str):
        """Пометить источник как недоверенный"""
        user_profile = self.db.get_user_profile()
        if source_id not in user_profile.disliked_sources:
            user_profile.disliked_sources.append(source_id)
        self.db.update_user_profile(user_profile)
    
    def get_sources(self) -> List:
        """Получить все источники"""
        return self.db.get_sources()
    
    def get_user_profile(self) -> UserProfile:
        """Получить профиль пользователя"""
        return self.db.get_user_profile()
    
    def delete_task(self, task_id: str):
        """Удалить задачу"""
        self.db.delete_task(task_id)

