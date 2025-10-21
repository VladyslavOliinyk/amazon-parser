# 1. Используем официальный образ Python
FROM python:3.11-slim

# 2. Устанавливаем рабочую директорию
WORKDIR /app

# 3. Копируем файл с зависимостями и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Копируем все остальные файлы проекта
COPY . .

# 5. Открываем порт, на котором будет работать наше приложение
EXPOSE 8000

# 6. Команда для запуска Uvicorn сервера
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]

