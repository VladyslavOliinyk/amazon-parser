# 1. Используем официальный образ Python
FROM python:3.11-slim

# 2. Устанавливаем системные зависимости, включая wget и Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    --no-install-recommends

# 3. Скачиваем и устанавливаем Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update && apt-get install -y google-chrome-stable \
    --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 4. Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# 5. Копируем файл с зависимостями и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Копируем все остальные файлы проекта в контейнер
COPY . .

# 7. Открываем порт, на котором будет работать наше приложение
EXPOSE 8000

# 8. Команда для запуска Uvicorn сервера, когда контейнер стартует
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]

