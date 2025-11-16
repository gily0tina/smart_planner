"""Главный файл приложения FastAPI"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Умный планировщик дня",
    description="Приложение для умного планирования дня с использованием LLM",
    version="1.0.0"
)

logger.info("Приложение запущено")

# CORS для работы с фронтендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api", tags=["api"])


@app.get("/")
async def root():
    """Корневой endpoint"""
    return {"message": "Умный планировщик дня API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok"}

