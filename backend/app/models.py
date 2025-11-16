"""Модели данных для приложения"""
from typing import Optional, List, Dict
from pydantic import BaseModel
from enum import Enum


class TimeBlock(str, Enum):
    """Временные блоки дня"""
    MORNING = "утро"
    DAY = "день"
    EVENING = "вечер"


class Chronotype(str, Enum):
    """Хронотип пользователя"""
    LARK = "lark"  # жаворонок
    OWL = "owl"    # сова


class Task(BaseModel):
    """Модель задачи"""
    id: Optional[str] = None
    title: str
    category: str
    mood: str
    preferred_time: Optional[TimeBlock] = None


class PlanItem(BaseModel):
    """Элемент плана"""
    task_id: str
    task_title: str
    task_category: str
    task_mood: str
    time_block: TimeBlock
    justification: str


class Source(BaseModel):
    """Источник информации"""
    id: str
    title: str
    link: str
    trust: bool = True


class DayPlan(BaseModel):
    """План на день"""
    morning: List[PlanItem] = []
    day: List[PlanItem] = []
    evening: List[PlanItem] = []
    sources: List[Source] = []
    error_message: Optional[str] = None  # Сообщение об ошибке, если план не удалось сгенерировать


class UserProfile(BaseModel):
    """Профиль пользователя"""
    chronotype: Optional[Chronotype] = None
    task_shifting_history: Dict[str, List[str]] = {}
    disliked_sources: List[str] = []


class TaskCreate(BaseModel):
    """Создание задачи"""
    title: str
    category: str
    mood: str


class PlanRequest(BaseModel):
    """Запрос на генерацию плана"""
    tasks: List[TaskCreate]


class PlanUpdate(BaseModel):
    """Обновление плана"""
    task_id: str
    new_time_block: TimeBlock

