```text
PriceAnalytics_Diplom/
├── backend/                               # Серверна частина проєкту (FastAPI)
│   ├── api/
│   │   └── routes.py                     # Маршрутизатори REST API (ендпоінти)
│   ├── db/
│   │   └── database.py                   # Налаштування підключення до PostgreSQL
│   ├── models/
│   │   └── models.py                     # ORM-моделі таблиць бази даних
│   ├── schemas/
│   │   └── schemas.py                    # Pydantic-схеми валідації даних
│   ├── services/                         # Бізнес-логіка системи
│   │   ├── auth.py                       # Авторизація та управління сесіями
│   │   ├── notifications.py              # Email- та Telegram-сповіщення
│   │   ├── parser.py                     # Веб-скрапінг через Playwright
│   │   └── tasks.py                      # Планувальник автоматичної перевірки цін
│   │
│   ├── Dockerfile                        # Docker-конфігурація бекенду
│   ├── main.py                           # Точка входу FastAPI-додатку
│   ├── requirements.txt                  # Python-залежності проєкту
│   └── test_price_change.py              # Локальне тестування тригерів зміни цін
│
├── frontend/                             # Клієнтська частина проєкту (React)
│   ├── public/                           # Статичні ресурси та SVG-іконки
│   │   ├── favicon.svg
│   │   ├── icons.svg
│   │   └── priceflow-icon.svg
│   ├── src/                              # Вихідний код React-додатку
│   │   ├── assets/                       # Медіафайли та зображення
│   │   ├── components/                   # UI-компоненти інтерфейсу
│   │   │   ├── tabs/                     # Вкладки панелі керування
│   │   │   │   ├── AnalyticsTab.jsx     # Аналітика, графіки та статистика
│   │   │   │   ├── ProductsTab.jsx      # Список товарів для моніторингу
│   │   │   │   └── TrackingTab.jsx      # Налаштування парсингу та тригерів
│   │   │   └── AuthScreen.jsx           # Авторизація та реєстрація користувачів
│   │   │
│   │   ├── App.css                       # Глобальні стилі React-додатку
│   │   ├── App.jsx                       # Основний компонент маршрутизації
│   │   ├── index.css                     # Базові стилі HTML-сторінки
│   │   └── main.jsx                      # Монтування React у DOM
│   │
│   ├── Dockerfile                        # Docker-конфігурація фронтенду
│   └── eslint.config.js                  # Налаштування ESLint
└── docker-compose.yml                    # Оркестрація контейнерів системи
```
