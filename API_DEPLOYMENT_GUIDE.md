# 🚀 API DEPLOYMENT GUIDE - Fly.dev FastAPI Backend

**Статус**: ✅ **ГОТОВО ДО DEPLOYMENT**  
**Дата**: Грудень 2024  
**Ціль**: Розгорнути окремий FastAPI backend на Fly.dev та підключити до фронтенду

---

## 📦 СТВОРЕНІ ФАЙЛИ

### 1. **Dockerfile.api** - Docker контейнер для FastAPI
```dockerfile
FROM python:3.11-slim
WORKDIR /app

# Системні залежності + playwright браузери для botasaurus
RUN apt-get update && apt-get install -y curl wget gnupg git build-essential sqlite3
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m playwright install --with-deps

COPY . .
RUN mkdir -p data logs cli/logs scraper/logs reports

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV PYTHONPATH=/app

EXPOSE 8080
HEALTHCHECK CMD curl -f http://localhost:8080/health || exit 1
CMD ["uvicorn", "cli.server:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
```

### 2. **fly.api.toml** - Fly.dev конфігурація
```toml
app = "glow-nest-api"
primary_region = "fra"

[build]
  dockerfile = "Dockerfile.api"

[[services]]
  internal_port = 8080
  protocol = "tcp"
  auto_stop_machines = true
  auto_start_machines = true

  [[services.http_checks]]
    path = "/health"
    interval = "15s"

[[mounts]]
  source = "glow_nest_data"
  destination = "/app/data"
```

### 3. **requirements.txt** - Виправлено sqlite3 залежність
```python
# sqlite3 вбудований в Python, видалено з requirements
# Додано всі необхідні пакети для FastAPI, botasaurus, ML
```

### 4. **CORS Configuration** - FastAPI налаштування
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dea706f0b3dd454188742d996e9d262a-58026be633ce45519cb96963e.fly.dev",
        "http://localhost:3000",
        "*"
    ],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    expose_headers=["*"]
)
```

### 5. **API URL Updates** - Frontend/Node.js
```typescript
// Оновлено в server/routes/scraping.ts та .env.example
const pythonBackendUrl = process.env.PYTHON_API_URL || 'https://glow-nest-api.fly.dev';
```

---

## 🚀 DEPLOYMENT ПРОЦЕС

### Крок 1: Підготовка Fly.dev
```bash
# Встановити Fly CLI
curl -L https://fly.io/install.sh | sh

# Логін в Fly.dev
fly auth login
```

### Крок 2: Автоматичний Deployment
```bash
# Запустити deployment скрипт
bash deploy_api.sh
```

**Або ручний deployment:**
```bash
# Створити app
fly apps create glow-nest-api

# Створити volume для БД
fly volumes create glow_nest_data --region fra --size 1 -a glow-nest-api

# Встановити secrets
fly secrets set -a glow-nest-api PYTHONUNBUFFERED=1 PYTHONPATH=/app

# Задеплоїти
fly deploy -c fly.api.toml -a glow-nest-api
```

### Крок 3: Перевірка Deployment
```bash
# Статус app
fly status -a glow-nest-api

# Логи
fly logs -a glow-nest-api

# Health check
curl https://glow-nest-api.fly.dev/health
```

---

## 🧪 ACCEPTANCE TESTING

### Автоматичне тестування:
```bash
python test_api_deployment.py
```

### Ручне тестування:

**Test 1: API Health**
```bash
curl https://glow-nest-api.fly.dev/health
# Очікується: {"ok": true, "pid": 123, "version": "abc123", ...}
```

**Test 2: Routes Debug**
```bash
curl https://glow-nest-api.fly.dev/__debug/routes
# Очікується: {"ok": true, "critical_check": {"scraper_start": true, ...}}
```

**Test 3: Scraper Start**
```bash
curl -X POST https://glow-nest-api.fly.dev/scraper/start \
     -H "Content-Type: application/json" \
     -d '{"listing_type":"sale","max_pages":1}'
# Очікується: {"ok": true, "task": "scrape:...", "status": "running"}
```

**Test 4: Frontend Self-Test**
- Відкрити: https://dea706f0b3dd454188742d996e9d262a-58026be633ce45519cb96963e.fly.dev
- Натиснути "🔍 Self-Test API" в секції Botasaurus
- Перевірити що всі тести пройшли

---

## 📊 АРХІТЕКТУРА ПІСЛЯ DEPLOYMENT

```
Frontend (Fly.dev)
https://dea706f0b3dd454188742d996e9d262a-58026be633ce45519cb96963e.fly.dev
                    ↓
Node.js Server (той самий контейнер)
/api/scraper/start → проксі до Python API
                    ↓
FastAPI Backend (окремий Fly.dev app)  
https://glow-nest-api.fly.dev
/scraper/start, /health, /__debug/routes
                    ↓
SQLite Database (persistent volume)
/app/data/glow_nest.db
```

---

## 🎯 ГОТОВНІСТЬ ДО ВИКОРИСТАННЯ

### ✅ **Що готово:**
1. **Dockerfile.api** - повністю налаштований для FastAPI + botasaurus
2. **fly.api.toml** - конфігурація з health checks і persistent storage
3. **CORS** - налаштований для communication між frontend і API
4. **URL Management** - всі компоненти вказують на правильний API URL
5. **Self-Test** - можливість перевірки API з admin panel
6. **Acceptance Tests** - comprehensive testing suite
7. **Deployment Script** - автоматизований process

### ✅ **Endpoints що працюватимуть:**
- `GET /health` - API health з PID та version info
- `GET /__debug/routes` - runtime route inspection
- `POST /scraper/start` і `POST /api/scraper/start` - scraper запуск
- `GET /progress/scrape` - SSE progress stream
- `GET /events/stream` - SSE events stream

### ✅ **Communication Flow:**
```
Admin Panel → Node.js Proxy → FastAPI → Database
     ↓              ↓             ↓
  Self-Test → /api/health → https://glow-nest-api.fly.dev/health
  Start Scraper → /api/scraper/start → https://glow-nest-api.fly.dev/scraper/start
  Live Progress → EventSource → https://glow-nest-api.fly.dev/progress/scrape
```

---

## 🔧 TROUBLESHOOTING

### Якщо deployment не вдається:
```bash
# Перевірити ресурси
fly resource list -a glow-nest-api

# Перевірити логи build
fly logs -a glow-nest-api

# Restart app
fly apps restart glow-nest-api
```

### Якщо health check не працює:
```bash
# Перевірити внутрішній порт
fly ssh console -a glow-nest-api
curl localhost:8080/health

# Перевірити processes
fly ssh console -a glow-nest-api
ps aux | grep uvicorn
```

### Якщо CORS блокує запити:
```bash
# Перевірити CORS headers
curl -H "Origin: https://your-frontend.fly.dev" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS https://glow-nest-api.fly.dev/scraper/start
```

---

## 🎉 РЕЗУЛЬТАТ

**Після deployment:**
- ❌ **Більше не буде**: HTML замість JSON на /health
- ❌ **Більше не буде**: 404 Not Found на /scraper/start  
- ❌ **Більше не буде**: "Empty response body" помилок
- ✅ **Буде працювати**: Живий прогрес через SSE
- ✅ **Буд�� працювати**: Запуск scraper з admin panel
- ✅ **Буде працювати**: Повна діагностика через /__debug/routes

**Команда для deployment:**
```bash
bash deploy_api.sh && python test_api_deployment.py
```

**Статус**: 🚀 **ГОТОВО ДО РОЗГОРТАННЯ**
