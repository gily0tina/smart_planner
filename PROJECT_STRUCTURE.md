# Структура проекта

```
smart_planner/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # Точка входа FastAPI
│   │   ├── models.py          # Модели данных (Pydantic)
│   │   ├── api/               # API Layer
│   │   │   ├── __init__.py
│   │   │   └── routes.py      # API endpoints
│   │   ├── domain/            # Domain Layer (бизнес-логика)
│   │   │   ├── __init__.py
│   │   │   └── planner_service.py  # Главный сервис планирования
│   │   ├── llm/               # LLM Layer
│   │   │   ├── __init__.py
│   │   │   └── llm_service.py # Сервис работы с LLM
│   │   └── data/              # Data Layer
│   │       ├── __init__.py
│   │       └── database.py    # Работа с SQLite
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── App.jsx            # Главный компонент
│   │   ├── main.jsx           # Точка входа React
│   │   └── index.css          # Стили
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js         # Конфигурация Vite
│   └── Dockerfile
│
├── docker-compose.yml          # Docker Compose конфигурация
├── .gitignore
├── .dockerignore
├── README.md                   # Основная документация
├── README_SETUP.md             # Инструкция по установке
├── QUICKSTART.md               # Быстрый старт
└── PROJECT_STRUCTURE.md        # Этот файл
```

## Архитектура модулей

### Backend (FastAPI)

- **API Layer** (`app/api/`) - REST API endpoints
- **Domain Layer** (`app/domain/`) - Бизнес-логика приложения
- **LLM Layer** (`app/llm/`) - Работа с LLM моделями
- **Data Layer** (`app/data/`) - Работа с базой данных SQLite

### Frontend (React + Vite)

- **App.jsx** - Главный компонент с формой задач и отображением плана
- **index.css** - Стили приложения
- Прокси настроен для работы с backend через Docker сеть

## Основные функции

✅ Все функции из README.md реализованы:
- Ввод задач (название, категория, эмоциональный окрас)
- Генерация плана с LLM
- Распределение по биоритмам (утро/день/вечер)
- Обоснование рекомендаций
- Ручная коррекция плана
- Перегенерация плана
- Просмотр источников
- Отметка источников как недоверенных
- Определение хронотипа

## Технологии

- **Backend**: Python 3.11, FastAPI, SQLite
- **Frontend**: React 18, Vite, Axios
- **Containerization**: Docker, Docker Compose

