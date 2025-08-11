# 🚀 Інструкції для деплою фронтенда на Fly.io

## Передумови

1. **Встановлений flyctl CLI:**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Авторизація в Fly.io:**
   ```bash
   fly auth login
   ```

## Кроки деплою

### 1. Тестування збірки локально

```bash
# Встановлення залежностей
npm ci

# Тестування збірки
NODE_ENV=production PYTHON_API_URL=https://glow-nest-api.fly.dev npm run build

# Перевірка файлів збірки
ls -la dist/spa/
ls -la dist/server/
```

### 2. Ініціалізація Fly.io застосунку

```bash
# Створення нового застосунку (виконати один раз)
fly apps create glow-nest-frontend --region fra
```

### 3. Деплой

```bash
# Деплой фронтенда
fly deploy

# Перевірка статусу
fly status

# Перегляд логів
fly logs
```

### 4. Налаштування домену (опціонально)

```bash
# Додавання кастомного домену
fly certs create your-domain.com

# Перевірка сертифікату
fly certs show your-domain.com
```

## Структура файлів

- `Dockerfile` - Конфігурація для збірки Docker образу
- `fly.toml` - Конфігурація Fly.io для фронтенда
- `nginx.conf` - Налаштування Nginx для SPA та проксування API

## Важливі моменти

### Змінні оточення

Проєкт використовує наступні змінні:
- `NODE_ENV=production` - для production збірки
- `PYTHON_API_URL=https://glow-nest-api.fly.dev` - URL Python API

### API Проксування

Nginx налаштований для:
- Обслуговування статичних файлів React SPA
- Проксування `/api/*` запитів до Python backend
- Проксування прямих API маршрутів (`/health`, `/scraper/*`, тощо)

### Кеш стратегія

- Статичні ресурси кешуються на 1 рік
- API запити не кешуються
- SPA маршрутизація підтримується через fallback до `index.html`

## Перевірка деплою

1. **Перевірка фронтенда:**
   ```bash
   curl https://glow-nest-frontend.fly.dev/
   ```

2. **Перевірка API проксування:**
   ```bash
   curl https://glow-nest-frontend.fly.dev/health
   ```

3. **Перевірка в браузері:**
   - Відкрийте https://glow-nest-frontend.fly.dev
   - Перевірте консоль розробника на помилки
   - Протестуйте функціональність адмін панелі

## Troubleshooting

### Проблема з збіркою

```bash
# Очистка та повторна збірка
rm -rf node_modules dist
npm ci
npm run build
```

### Проблема з API

1. Перевірте, що Python API працює: https://glow-nest-api.fly.dev/health
2. Перевірте логи фронтенда: `fly logs`
3. Перевірте nginx конфігурацію в контейнері

### Проблема з маршрутизацією

Всі маршрути SPA повинні повертати `index.html`. Якщо отримуєте 404:
1. Перевірте nginx конфігурацію
2. Перевірте, що файл `index.html` існує в `/usr/share/nginx/html`

## Корисні команди

```bash
# Перегляд поточного статусу
fly status

# SSH до контейнера
fly ssh console

# Масштабування
fly scale count 1

# Перегляд метрик
fly metrics

# Перезапуск
fly restart
```
