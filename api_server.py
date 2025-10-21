import json
import os
import datetime
from fastapi import FastAPI, Query, HTTPException
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


# --- 2. ЛОГИКА ПЛАНИРОВЩИКА ---

def scheduled_parser_job():
    """Задача, которую планировщик будет запускать раз в сутки."""
    global is_parser_running
    if not is_parser_running:
        print("--- [SCHEDULER] --- Запуск парсера по расписанию...")
        is_parser_running = True
        try:
            run_parser()
            print("--- [SCHEDULER] --- Парсер успешно завершил работу.")
        except Exception as e:
            print(f"--- [SCHEDULER] --- Ошибка во время выполнения парсера: {e}")
        finally:
            is_parser_running = False
    else:
        print("--- [SCHEDULER] --- Пропуск запуска: парсер уже работает.")


# Создаем и настраиваем планировщик
scheduler = BackgroundScheduler(timezone="Europe/Kiev")
scheduler.add_job(scheduled_parser_job, 'interval', hours=24)  # hours=24 для запуска раз в сутки


# --- 3. LIFESPAN MANAGER ДЛЯ УПРАВЛЕНИЯ ПЛАНИРОВЩИКОМ ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код, который выполнится при старте сервера
    print("--- [SERVER] --- Запуск фонового планировщика...")
    scheduler.start()
    yield
    # Код, который выполнится при остановке сервера
    print("--- [SERVER] --- Остановка планировщика...")
    scheduler.shutdown()


# --- 4. ИНИЦИАЛИЗАЦИЯ FASTAPI ПРИЛОЖЕНИЯ ---

app = FastAPI(
    title="Amazon Best Sellers API",
    description="API для получения данных о бестселлерах Amazon и управления парсером.",
    lifespan=lifespan
)

# Настройка CORS для разрешения запросов с фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 5. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def get_file_update_time(filename: str) -> Optional[str]:
    """Возвращает время последнего изменения файла в читаемом формате."""
    if not os.path.exists(filename):
        return None
    mod_time = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')


# --- 6. API ЭНДПОИНТЫ ---

# === Эндпоинты для Задания 3 (НОВЫЙ ФУНКЦИОНАЛ) ===

@app.get("/api/bestsellers", tags=["Задание 3 - Best Sellers по категориям"])
def get_all_bestsellers():
    """Возвращает полный снимок данных из amazon_bestsellers_data.json."""
    try:
        with open("amazon_bestsellers_data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


@app.post("/api/trigger-parser", tags=["Задание 3 - Best Sellers по категориям"])
async def trigger_parser_manually():
    """Запускает парсер бестселлеров вручную."""
    global is_parser_running
    if is_parser_running:
        raise HTTPException(status_code=409, detail="Парсер уже запущен. Попробуйте позже.")

    print("--- [API] --- Получен запрос на ручной запуск парсера...")
    is_parser_running = True
    try:
        success = run_parser()
        if success:
            return {"status": "success", "message": "Парсер успешно завершил работу."}
        else:
            raise HTTPException(status_code=500, detail="Во время работы парсера произошла ошибка.")
    finally:
        is_parser_running = False


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

    filtered_items = items
    if min_rating is not None:
        filtered_items = [it for it in filtered_items if float(it.get("rating", "0").split()[0] or 0) >= min_rating]
    if max_price is not None:
        filtered_items = [it for it in filtered_items if
                          it.get("price") and float(str(it["price"]).replace("$", "").replace(",", "")) <= max_price]

    return {"count": len(filtered_items), "items": filtered_items}


# --- 7. ПОДКЛЮЧЕНИЕ СТАТИКИ И ЗАПУСК СЕРВЕРА ---

# Подключаем папку 'static' для отдачи HTML, CSS, JS
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# Блок для удобного запуска сервера командой `python api_server.py`
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

