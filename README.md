# VibeSync — Коллективные музыкальные плейлисты

Сервис для создания сбалансированных музыкальных плейлистов совместно с друзьями. VibeSync решает проблему «музыкальных споров» на вечеринках: каждый участник может предложить треки и проголосовать за понравившиеся. Идеально для мероприятий, где важно учесть вкусы всех гостей!

**Демо-версия:** https://SaintMaksim.pythonanywhere.com

## Технологии
* **Backend**: Python 3.10, Django 4.2
* **База данных**: SQLite (разработка)
* **Аналитика**: Pandas (балансировка плейлиста по жанрам)
* **API**: Last.fm (поиск треков и получение тегов)
* **Frontend**: Bootstrap 5.3, Chart.js (визуализация распределения жанров)

## Скриншоты

**Главная страница** <img width="1920" height="908" alt="image" src="https://github.com/user-attachments/assets/5e599dba-12ce-45a6-8e2f-a5e0cc19ddf0" />
*Главная страница: вход по коду мероприятия и создание своего мероприятия*

**Страница регистрации** <img width="1920" height="908" alt="image" src="https://github.com/user-attachments/assets/8be42a82-770d-4fcb-9cf9-33cbc8a83964" />
*Страница регистрации: регистрация без пароля*

**Страница мероприятия** <img width="1885" height="915" alt="image" src="https://github.com/user-attachments/assets/b7b5f7b0-d4d2-4539-b96a-e52569a14ede" />

*Страница мероприятия: поиск треков, предложения и голосование с визуальной обратной связью*

**Финальный плейлист**
<img width="1849" height="899" alt="image" src="https://github.com/user-attachments/assets/a8136c39-ae0d-4013-8f24-13dc343fb4dd" />
<img width="1840" height="893" alt="image" src="https://github.com/user-attachments/assets/386f822d-0409-4c59-aeb5-90166e6ff2cd" />

*Сбалансированный плейлист с графиком распределения жанров*

## Как запустить проект локально

1. **Клонируйте репозиторий:**
   ```bash
   git clone https://github.com/SaintMaksim/VibeSync.git
   cd VibeSync
   ```
2. **Создайте и активируйте виртуальное окружение:**
   ```bash
   python -m venv venv
   source venv/bin/activate    # Linux / macOS  
   venv\Scripts\activate       # Windows
   ```
3. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Настройте переменные окружения:**
   ```bash
   cp .env.example .env # Создайте файл .env на основе примера
   ```
5. **Примените миграции:**
   ```bash
   python manage.py migrate
   ```
6. **Запустите сервер:**
   ```bash
   python manage.py runserver
   ```
7. **Откройте в браузере:**
   Перейдите по адресу: http://127.0.0.1:8000
