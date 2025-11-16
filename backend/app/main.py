"""Главный файл приложения FastAPI"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router

app = FastAPI(
    title="Умный планировщик дня",
    description="Приложение для умного планирования дня с использованием LLM",
    version="1.0.0"
)

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

