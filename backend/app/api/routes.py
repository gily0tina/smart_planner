"""API маршруты"""
from fastapi import APIRouter, HTTPException
from typing import List

from ..models import TaskCreate, PlanRequest, DayPlan, PlanUpdate, Source, UserProfile
from ..domain.planner_service import PlannerService

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
        # Используем существующие задачи из базы, не создаем новые
        # Это предотвращает дублирование
        all_tasks = planner.get_all_tasks()
        task_ids = [t.id for t in all_tasks if t.id]
        
        # Если задач нет в базе, но есть в запросе, создаем их
        if not task_ids and request.tasks:
            for task_data in request.tasks:
                try:
                    task = planner.create_task(task_data)
                    if task and task.id:
                        task_ids.append(task.id)
                except Exception as e:
                    # Пропускаем ошибки создания отдельных задач
                    continue
        
        if not task_ids:
            raise HTTPException(status_code=400, detail="Нет задач для генерации плана")
        
        # Генерируем план для всех существующих задач
        plan = planner.generate_plan(task_ids)
        return plan
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


@router.post("/plan/regenerate", response_model=DayPlan)
async def regenerate_plan():
    """Перегенерировать план на основе существующих задач"""
    try:
        plan = planner.generate_plan()
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/plan/update", response_model=dict)
async def update_plan(update: PlanUpdate):
    """Обновить время задачи в плане"""
    try:
        from ..models import TimeBlock
        planner.update_task_time(update.task_id, TimeBlock(update.new_time_block))
        return {"message": "План обновлен"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


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

