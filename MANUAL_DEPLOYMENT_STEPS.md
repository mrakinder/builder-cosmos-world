# 🚀 MANUAL DEPLOYMENT STEPS

**Проблема**: Автоматичне виконання `bash deploy_api.sh` обмежене policies  
**Рішення**: Покрокове виконання команд вручну

---

## 📋 КРОК ЗА КРОКОМ

### 1. **Встановити Fly CLI** (якщо ще не встановлений)
```bash
curl -L https://fly.io/install.sh | sh
export PATH="$HOME/.fly/bin:$PATH"
```

### 2. **Логін в Fly.dev**
```bash
fly auth login
```

### 3. **Створити Fly app**
```bash
fly apps create glow-nest-api --generate-name false
```

### 4. **Створити volume для БД**
```bash
fly volumes create glow_nest_data --region fra --size 1 -a glow-nest-api
```

### 5. **Встановити environment variables**
```bash
fly secrets set -a glow-nest-api \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    API_HOST=0.0.0.0 \
    API_PORT=8080
```

### 6. **Задеплоїти застосунок**
```bash
fly deploy -c fly.api.toml -a glow-nest-api
```

### 7. **Перевірити статус**
```bash
fly status -a glow-nest-api
fly logs -a glow-nest-api
```

### 8. **Тестувати deployment**
```bash
# Health check
curl https://glow-nest-api.fly.dev/health

# Routes check  
curl https://glow-nest-api.fly.dev/__debug/routes

# Scraper test
curl -X POST https://glow-nest-api.fly.dev/scraper/start \
     -H "Content-Type: application/json" \
     -d '{"listing_type":"sale","max_pages":1}'
```

---

## 🔍 ОЧІКУВАНІ РЕЗУЛЬТАТИ

### Health Check:
```json
{
  "ok": true,
  "status": "healthy",
  "pid": 123,
  "timestamp": "2024-12-...",
  "version": "abc123f",
  "host": "0.0.0.0:8080",
  "runtime": "FastAPI + Uvicorn"
}
```

### Routes Check:
```json
{
  "ok": true,
  "total_routes": 25,
  "critical_check": {
    "scraper_start": true,
    "api_scraper_start": true,
    "health": true
  }
}
```

### Scraper Start:
```json
{
  "ok": true,
  "task": "scrape:1703123456",
  "status": "running"
}
```

---

## 🎯 ПІСЛЯ УСПІШНОГО DEPLOYMENT

1. **Відкрийте admin panel**: https://dea706f0b3dd454188742d996e9d262a-58026be633ce45519cb96963e.fly.dev
2. **Натисніть "🔍 Self-Test API"** в секції Botasaurus
3. **Перевірте що всі тести пройшли**
4. **Натисніть "Запустити парсинг"** для повного тесту

---

## 🚨 TROUBLESHOOTING

### Якщо `fly apps create` видає помилку:
```bash
# App вже існує, просто продовжуйте з кроку 4
```

### Якщо volume вже існує:
```bash
# Перевірте: fly volumes list -a glow-nest-api
# Якщо є glow_nest_data, продовжуйте з кроку 5
```

### Якщо deployment не вдається:
```bash
# Перевірте логи
fly logs -a glow-nest-api

# Перевірте статус
fly status -a glow-nest-api

# Restart app
fly apps restart glow-nest-api
```

### Якщо health check не працює:
```bash
# Зачекайте 1-2 хвилини після deployment
# Перевірте internal health
fly ssh console -a glow-nest-api
curl localhost:8080/health
```

---

## ✅ ФАЙЛИ ГОТОВІ ДО DEPLOYMENT

Всі необхідні файли вже створені:
- ✅ `Dockerfile.api` - Docker контейнер
- ✅ `fly.api.toml` - Fly.dev конфігурація  
- ✅ `requirements.txt` - Python залежності
- ✅ `cli/server.py` - FastAPI з CORS та endpoints
- ✅ `test_api_deployment.py` - Acceptance тести

**Просто виконайте кроки 1-8 вище!**
