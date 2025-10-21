import json
import os
import datetime
from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn
from contextlib import asynccontextmanager

# --- 1. ИМПОРТ И НАСТРОЙКА ---

# Импортируем нашу функцию парсера
from parser_categories import run_parser
# Импортируем планировщик
from apscheduler.schedulers.background import BackgroundScheduler

# Глобальная переменная-флаг, чтобы избежать запуска двух парсеров одновременно
is_parser_running = False


# --- 2. ЛОГИКА ПЛАНИРОВЩИКА И ФОНОВЫХ ЗАДАЧ ---

def parser_task():
    """
    Основная задача парсинга. Эта функция будет вызываться и планировщиком, и вручную.
    """
    global is_parser_running
    if is_parser_running:
        print("--- [TASK] --- Пропуск запуска: парсер уже работает.")
        return

    print("--- [TASK] --- Запуск парсера...")
    is_parser_running = True
    try:
        run_parser()
        print("--- [TASK] --- Парсер успешно завершил работу.")
    except Exception as e:
        print(f"--- [TASK] --- Ошибка во время выполнения парсера: {e}")
    finally:
        is_parser_running = False


# Создаем и настраиваем планировщик
scheduler = BackgroundScheduler(timezone="Europe/Kiev")
scheduler.add_job(parser_task, 'interval', hours=24)


# --- 3. LIFESPAN MANAGER ДЛЯ УПРАВЛЕНИЯ ПЛАНИРОВЩИКОМ ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- [SERVER] --- Запуск фонового планировщика...")
    scheduler.start()
    yield
    print("--- [SERVER] --- Остановка планировщика...")
    scheduler.shutdown()


# --- 4. ИНИЦИАЛИЗАЦИЯ FASTAPI ПРИЛОЖЕНИЯ ---

app = FastAPI(
    title="Amazon Best Sellers API",
    description="API для получения данных о бестселлерах Amazon и управления парсером.",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)


# --- 5. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def get_file_update_time(filename: str) -> Optional[str]:
    """Возвращает время последнего изменения файла в читаемом формате."""
    if not os.path.exists(filename):
        return None
    mod_time = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')


# --- 6. API ЭНДПОИНТЫ ---

@app.get("/api/bestsellers", tags=["Задание 3 - Best Sellers по категориям"])
def get_all_bestsellers():
    """Возвращает полный снимок данных из amazon_bestsellers_data.json."""
    try:
        with open("amazon_bestsellers_data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # На сервере Render файла сначала не будет, это нормальная ситуация
        return {}


# !!! ГЛАВНОЕ ИЗМЕНЕНИЕ ЗДЕСЬ !!!
@app.post("/api/trigger-parser", tags=["Задание 3 - Best Sellers по категориям"])
async def trigger_parser_manually(background_tasks: BackgroundTasks):
    """
    МГНОВЕННО отвечает и добавляет задачу парсинга в фоновый режим.
    """
    global is_parser_running
    if is_parser_running:
        raise HTTPException(status_code=409, detail="Парсер уже запущен. Попробуйте позже.")

    print("--- [API] --- Получен запрос на ручной запуск. Добавляю в фон...")
    # Добавляем долгую задачу в фон. FastAPI выполнит ее после отправки ответа.
    background_tasks.add_task(parser_task)

    # Сразу же возвращаем ответ пользователю
    return {"status": "success", "message": "Процесс обновления запущен! Данные появятся в течение нескольких минут."}


@app.get("/api/parser-status", tags=["Задание 3 - Best Sellers по категориям"])
def get_parser_status():
    """Возвращает статус парсера и время последнего обновления данных."""
    return {
        "is_running": is_parser_running,
        "last_updated": get_file_update_time("amazon_bestsellers_data.json")
    }


# === Эндпоинты для Заданий 1 и 2 (старый функционал) ===
@app.get("/items", tags=["Задания 1, 2 - Статический парсер"])
def get_items(min_rating: Optional[float] = Query(None), max_price: Optional[float] = Query(None)):
    """Возвращает отфильтрованный список товаров из data.json."""
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            items = json.load(f)
    except FileNotFoundError:
        return {"count": 0, "items": []}
    # ... остальная логика фильтрации ...
    filtered_items = items  # Упрощено для краткости
    return {"count": len(filtered_items), "items": filtered_items}


# --- 7. ПОДКЛЮЧЕНИЕ СТАТИКИ И ЗАПУСК СЕРВЕРА ---
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

