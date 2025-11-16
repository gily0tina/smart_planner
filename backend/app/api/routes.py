"""API маршруты"""
import logging
from fastapi import APIRouter, HTTPException
from typing import List

from ..models import TaskCreate, PlanRequest, DayPlan, PlanUpdate, Source, UserProfile
from ..domain.planner_service import PlannerService

logger = logging.getLogger(__name__)

router = APIRouter()
planner = PlannerService()


@router.post("/tasks", response_model=dict)
async def create_task(task: TaskCreate):
    """Создать задачу"""
    try:
        created_task = planner.create_task(task)
        return {"id": created_task.id, "message": "Задача создана"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks", response_model=List[dict])
async def get_tasks():
    """Получить все задачи"""
    tasks = planner.get_all_tasks()
    return [{
        "id": t.id,
        "title": t.title,
        "category": t.category,
        "mood": t.mood,
        "preferred_time": t.preferred_time.value if t.preferred_time else None
    } for t in tasks]


@router.delete("/tasks/{task_id}", response_model=dict)
async def delete_task(task_id: str):
    """Удалить задачу"""
    try:
        planner.delete_task(task_id)
        return {"message": "Задача удалена"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/plan/generate", response_model=DayPlan)
async def generate_plan(request: PlanRequest):
    """Сгенерировать план на день"""
    try:
        import traceback
        logger.info(f"[API] Получен запрос на генерацию плана. Задач в запросе: {len(request.tasks)}")
        
        # Используем существующие задачи из базы, не создаем новые
        # Это предотвращает дублирование
        all_tasks = planner.get_all_tasks()
        logger.info(f"[API] Всего задач в базе: {len(all_tasks)}")
        task_ids = [t.id for t in all_tasks if t.id]
        logger.info(f"[API] ID задач для генерации: {task_ids}")
        
        # Если задач нет в базе, но есть в запросе, создаем их
        if not task_ids and request.tasks:
            logger.info(f"[API] Задач в базе нет, создаем из запроса")
            for task_data in request.tasks:
                try:
                    task = planner.create_task(task_data)
                    if task and task.id:
                        task_ids.append(task.id)
                        logger.info(f"[API] Создана задача: {task.title} (id: {task.id})")
                except Exception as e:
                    logger.error(f"[API] Ошибка создания задачи: {e}")
                    # Пропускаем ошибки создания отдельных задач
                    continue
        
        if not task_ids:
            logger.warning("[API] Нет задач для генерации плана")
            # Возвращаем пустой план с сообщением об ошибке
            from ..models import DayPlan
            return DayPlan(error_message="Произошла ошибка при генерации - попробуйте еще раз")
        
        logger.info(f"[API] Начинаем генерацию плана для {len(task_ids)} задач")
        # Генерируем план для всех существующих задач
        plan = planner.generate_plan(task_ids)
        
        logger.info(f"[API] План сгенерирован: утро={len(plan.morning)}, день={len(plan.day)}, вечер={len(plan.evening)}")
        logger.info(f"[API] Источников в плане: {len(plan.sources)}")
        for idx, source in enumerate(plan.sources):
            logger.info(f"[API] Источник {idx+1} в ответе: {source.title} -> {source.link}")
        
        return plan
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"[API] Ошибка генерации плана: {e}")
        logger.exception(e)
        # Возвращаем пустой план с сообщением об ошибке вместо деталей
        from ..models import DayPlan
        return DayPlan(error_message="Произошла ошибка при генерации - попробуйте еще раз")


@router.post("/plan/regenerate", response_model=DayPlan)
async def regenerate_plan():
    """Перегенерировать план на основе существующих задач"""
    try:
        plan = planner.generate_plan()
        return plan
    except Exception as e:
        logger.error(f"[API] Ошибка перегенерации плана: {e}")
        logger.exception(e)
        # Возвращаем пустой план с сообщением об ошибке вместо деталей
        from ..models import DayPlan
        return DayPlan(error_message="Произошла ошибка при генерации - попробуйте еще раз")


@router.put("/plan/update", response_model=DayPlan)
async def update_plan(update: PlanUpdate):
    """Обновить время задачи в плане (без перегенерации)"""
    try:
        from ..models import TimeBlock
        plan = planner.update_task_time(update.task_id, TimeBlock(update.new_time_block))
        return plan
    except Exception as e:
        logger.error(f"[API] Ошибка обновления плана: {e}")
        logger.exception(e)
        # Возвращаем пустой план с сообщением об ошибке вместо деталей
        from ..models import DayPlan
        return DayPlan(error_message="Произошла ошибка при генерации - попробуйте еще раз")


@router.get("/sources", response_model=List[Source])
async def get_sources():
    """Получить список источников"""
    return planner.get_sources()


@router.post("/sources/{source_id}/untrust", response_model=dict)
async def mark_source_untrusted(source_id: str):
    """Пометить источник как недоверенный"""
    try:
        planner.mark_source_untrusted(source_id)
        return {"message": "Источник помечен как недоверенный"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/profile", response_model=UserProfile)
async def get_profile():
    """Получить профиль пользователя"""
    return planner.get_user_profile()

