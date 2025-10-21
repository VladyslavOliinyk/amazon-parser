# 1. Используем официальный образ Python
FROM python:3.11-slim

# 2. Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# 3. Устанавливаем системные зависимости и Google Chrome (НОВЫЙ, ИСПРАВЛЕННЫЙ МЕТОД)
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    unzip \
    --no-install-recommends \
    # Устанавливаем ключ Google безопасным способом
    && curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/google.gpg \
    # Добавляем репозиторий Chrome
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    # Устанавливаем сам браузер
    && apt-get update && apt-get install -y \
    google-chrome-stable \
    --no-install-recommends \
    # Очищаем кэш для уменьшения размера образа
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 4. Копируем файл с зависимостями и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Копируем все остальные файлы проекта в контейнер
COPY . .

# 6. Открываем порт, на котором будет работать наше приложение
EXPOSE 8000

# 7. Команда для запуска Uvicorn сервера
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]

