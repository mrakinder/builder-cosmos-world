# 🎯 DEPLOY BACKEND - ACCEPTANCE TEST

## ✅ **ACCEPTANCE CHECKLIST:**

### 1. **Deploy Backend тест**
- [ ] Натиснути "🚀 Deploy Backend" в admin панелі
- [ ] Очікувана відповідь: "Deploy workflow dispatched successfully"
- [ ] GitHub Actions має запуститись з `deploy-api.yml`
- [ ] Логи: "✅ Backend deployment workflow dispatched successfully"

### 2. **API Health Check через 1-2 хвилини**
- [ ] Браузер: https://glow-nest-api.fly.dev/health → `{"ok":true,"status":"healthy"}`
- [ ] Сервер test: GET /diag/api-check → всі перевірки ✅
- [ ] Логи: "✅ Health check passed: healthy"

### 3. **Routes verification**
- [ ] https://glow-nest-api.fly.dev/__debug/routes містить:
  - `POST /scraper/start` ✅
  - `POST /api/scraper/start` ✅ (alias)
  - `GET /health` ✅

### 4. **Self-test кнопки**
- [ ] Admin панель → "Діагностика API"
- [ ] Server-side test → ✅ All tests passed
- [ ] Client-side test → ✅ All endpoints working

### 5. **Scraper startup test**
- [ ] Натиснути "Запустити парсинг"
- [ ] Pre-flight health check → ✅ Health check passed
- [ ] Відповідь: 202 + JSON `{"ok":true,"task":"...","status":"running"}`
- [ ] SSE прогрес біжить в реальному часі
- [ ] Журнал подій оновлюється live

### 6. **Final verification**
- [ ] Логи містять: "✅ API alive; Start OK; SSE OK"
- [ ] ConnectTimeout помилки зникли
- [ ] Backend deployment працює через GitHub Actions
- [ ] Система повністю функціональна

---

## 🚨 **TROUBLESHOOTING:**

### Якщо Deploy Backend не працює:
1. Перевірити GH_TOKEN в environment variables
2. Перевірити FLY_API_TOKEN в GitHub Secrets
3. Перевірити deployment logs в GitHub Actions

### Якщо Health Check падає:
1. Перевірити deployment status: `fly status -a glow-nest-api`
2. Перевірити логи: `fly logs -a glow-nest-api`
3. Restart app: `fly machine restart -a glow-nest-api`

### Якщо Scraper startup падає:
1. Перевірити pre-flight health check логи
2. Перевірити API URL configuration
3. Перевірити CORS налаштування

---

## 🎉 **SUCCESS CRITERIA:**

**✅ PASSED коли:**
- Deploy Backend кнопка запускає GitHub Actions
- Health check проходить з браузера і сервера  
- Scraper запускається без ConnectTimeout
- SSE streams працюють в реальному часі
- Self-test показує всі ✅

**🚀 РЕЗУЛЬТАТ: Повна система з працюючим backend deployment!**
