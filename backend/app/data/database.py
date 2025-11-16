"""Модуль работы с базой данных"""
import sqlite3
import json
from typing import List, Optional, Dict
from pathlib import Path
from datetime import datetime

from ..models import Task, PlanItem, UserProfile, Source, Chronotype, TimeBlock


class Database:
    """Класс для работы с SQLite базой данных"""
    
    def __init__(self, db_path: str = "/app/data/data.db"):
        import os
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        """Получить соединение с БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Инициализация базы данных"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица задач
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                mood TEXT NOT NULL,
                preferred_time TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица планов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                time_block TEXT NOT NULL,
                justification TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        """)
        
        # Индекс для быстрого поиска планов
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_plans_plan_id ON plans(plan_id)
        """)
        
        # Таблица профиля пользователя
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chronotype TEXT,
                task_shifting_history TEXT,
                disliked_sources TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица источников
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                link TEXT NOT NULL,
                trust INTEGER DEFAULT 1
            )
        """)
        
        # История правок
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS edit_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                old_time_block TEXT,
                new_time_block TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_task(self, task: Task) -> str:
        """Сохранить задачу"""
        if not task.id:
            import uuid
            task.id = str(uuid.uuid4())
        
        # Убеждаемся, что ID не пустой
        if not task.id or not task.id.strip():
            import uuid
            task.id = str(uuid.uuid4())
        
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO tasks (id, title, category, mood, preferred_time)
                VALUES (?, ?, ?, ?, ?)
            """, (task.id, task.title, task.category, task.mood, 
                  task.preferred_time.value if task.preferred_time else None))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise ValueError(f"Ошибка сохранения задачи: {str(e)}")
        finally:
            conn.close()
        return task.id
    
    def get_tasks(self) -> List[Task]:
        """Получить все задачи"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        
        tasks = []
        for row in rows:
            tasks.append(Task(
                id=row['id'],
                title=row['title'],
                category=row['category'],
                mood=row['mood'],
                preferred_time=TimeBlock(row['preferred_time']) if row['preferred_time'] else None
            ))
        return tasks
    
    def save_plan(self, plan_items: List[PlanItem]):
        """Сохранить план"""
        import uuid
        plan_id = str(uuid.uuid4())
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Удаляем старые планы для этих задач (чтобы избежать дублирования)
            task_ids = [item.task_id for item in plan_items]
            if task_ids:
                placeholders = ','.join(['?'] * len(task_ids))
                cursor.execute(f"""
                    DELETE FROM plans WHERE task_id IN ({placeholders})
                """, task_ids)
            
            # Сохраняем новый план
            for item in plan_items:
                try:
                    # Убеждаемся, что time_block это enum и получаем его значение
                    time_block_value = item.time_block.value if hasattr(item.time_block, 'value') else str(item.time_block)
                    cursor.execute("""
                        INSERT INTO plans (plan_id, task_id, time_block, justification)
                        VALUES (?, ?, ?, ?)
                    """, (plan_id, item.task_id, time_block_value, item.justification))
                except Exception as e:
                    conn.rollback()
                    conn.close()
                    raise ValueError(f"Ошибка сохранения элемента плана: {str(e)}, task_id: {item.task_id}, time_block: {item.time_block}")
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_user_profile(self) -> UserProfile:
        """Получить профиль пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_profile ORDER BY updated_at DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return UserProfile(
                chronotype=Chronotype(row['chronotype']) if row['chronotype'] else None,
                task_shifting_history=json.loads(row['task_shifting_history'] or '{}'),
                disliked_sources=json.loads(row['disliked_sources'] or '[]')
            )
        return UserProfile()
    
    def update_user_profile(self, profile: UserProfile):
        """Обновить профиль пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO user_profile (id, chronotype, task_shifting_history, disliked_sources)
            VALUES (1, ?, ?, ?)
        """, (
            profile.chronotype.value if profile.chronotype else None,
            json.dumps(profile.task_shifting_history),
            json.dumps(profile.disliked_sources)
        ))
        conn.commit()
        conn.close()
    
    def save_edit_history(self, task_id: str, old_time: Optional[str], new_time: str):
        """Сохранить историю правок"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO edit_history (task_id, old_time_block, new_time_block)
            VALUES (?, ?, ?)
        """, (task_id, old_time, new_time))
        conn.commit()
        conn.close()
    
    def save_source(self, source: Source):
        """Сохранить источник"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO sources (id, title, link, trust)
            VALUES (?, ?, ?, ?)
        """, (source.id, source.title, source.link, 1 if source.trust else 0))
        conn.commit()
        conn.close()
    
    def get_sources(self) -> List[Source]:
        """Получить все источники"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sources")
        rows = cursor.fetchall()
        conn.close()
        
        sources = []
        for row in rows:
            sources.append(Source(
                id=row['id'],
                title=row['title'],
                link=row['link'],
                trust=bool(row['trust'])
            ))
        return sources
    
    def delete_task(self, task_id: str):
        """Удалить задачу"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Проверяем существование задачи
        cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
        if not cursor.fetchone():
            conn.close()
            raise ValueError(f"Задача {task_id} не найдена")
        
        # Удаляем связанные записи в планах
        cursor.execute("DELETE FROM plans WHERE task_id = ?", (task_id,))
        # Удаляем задачу
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        
        conn.commit()
        conn.close()

