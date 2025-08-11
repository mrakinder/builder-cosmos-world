#!/bin/bash

# Колири для виводу
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔧 Тестування збірки фронтенда...${NC}"

# Встановлюємо змінні оточення
export NODE_ENV=production
export PYTHON_API_URL=https://glow-nest-api.fly.dev

echo -e "${YELLOW}📦 Встановлення залежностей...${NC}"
if npm ci; then
    echo -e "${GREEN}✅ Залежності встановлено успішно${NC}"
else
    echo -e "${RED}❌ Помилка встановлення залежностей${NC}"
    exit 1
fi

echo -e "${YELLOW}🔨 Запуск збірки...${NC}"
if npm run build; then
    echo -e "${GREEN}✅ Збірка завершена успішно${NC}"
    
    # Перевіряємо чи існують файли збірки
    if [ -d "dist/spa" ] && [ -f "dist/spa/index.html" ]; then
        echo -e "${GREEN}✅ Статичні файли створено в dist/spa/${NC}"
        echo -e "${YELLOW}📁 Вміст dist/spa:${NC}"
        ls -la dist/spa/
        
        # Перевіряємо розмір файлів
        echo -e "${YELLOW}📊 Розміри основних файлів:${NC}"
        find dist/spa -name "*.js" -o -name "*.css" -o -name "*.html" | head -10 | xargs ls -lh
        
    else
        echo -e "${RED}❌ Файли збірки не знайдено${NC}"
        exit 1
    fi
    
    if [ -d "dist/server" ] && [ -f "dist/server/production.mjs" ]; then
        echo -e "${GREEN}✅ Серверні файли створено в dist/server/${NC}"
    else
        echo -e "${RED}❌ Серверні файли не знайдено${NC}"
        exit 1
    fi
    
else
    echo -e "${RED}❌ Помилка збірки${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 Тест збірки пройшов успішно!${NC}"
echo -e "${YELLOW}🚀 Готово до деплою на Fly.io${NC}"
