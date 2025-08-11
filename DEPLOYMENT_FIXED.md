# 🚀 Виправлений деплой Glow Nest

## Проблема була виправлена

**Симптом**: `Detected a Vite app → launch manifest was created for a app, but this is a Vite app`

**Причина**: Fly.io auto-launch механізм плутався між типами проектів

**Рішення**: Вимкнув auto-launch, використовую тільки явні конфігурації

---

## 📦 Структура файлів

- `fly.frontend.toml` - конфігурація для фронтенда (Vite + nginx)
- `fly.api.toml` - конфігурація для API (FastAPI + Python)
- `Dockerfile.frontend` - збірка React SPA
- `Dockerfile.api` - збірка Python API
- `deploy.sh` - master скрипт
- `test-build-fly.sh` - деплой фронте��да
- `deploy-api.sh` - деплой API

---

## 🚀 Команди деплою

### Опція 1: Master скрипт

```bash
# Тільки фронтенд
./deploy.sh frontend

# Тільки API
./deploy.sh api

# Все разом
./deploy.sh both
```

### Опція 2: Окремі скрипти

```bash
# Фронтенд
CONFIG=fly.frontend.toml ./test-build-fly.sh

# API
CONFIG=fly.api.toml ./deploy-api.sh
```

### Опція 3: Прямі команди

```bash
# Фронтенд
flyctl deploy --config fly.frontend.toml --remote-only

# API
flyctl deploy --config fly.api.toml --remote-only
```

---

## ✅ Виправлення

1. **Вимкнув auto-launch**: `export FLY_NO_LAUNCH=1`
2. **Прибрав конфлікти**: автоматично переміщує `fly.toml` → `fly.old.toml`
3. **Явні конфігурації**: використовую тільки `fly.frontend.toml` та `fly.api.toml`
4. **Правильний формат**: `app = "назва"` (без блоків `[app]`)
5. **Чиста збірка**: тільки `npm run build:client` без server частини

---

## 🔍 Acceptance criteria

✅ Локальна збірка працює: `npm run build`  
✅ Файли створюються в `dist/spa/`  
✅ Немає помилок з `./server` імпортами  
✅ Fly конфігурації валідні  
✅ Немає `launch plan generate` помилок

---

## 📋 Результат

- **Frontend**: https://glow-nest-frontend.fly.dev
- **API**: https://glow-nest-api.fly.dev
- **No more auto-launch conflicts**
- **Clean Vite SPA build**
- **Proper nginx proxy to API**

Готово до деплою! 🎉
