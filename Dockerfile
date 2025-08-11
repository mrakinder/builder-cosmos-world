# Multi-stage build для фронтенда
FROM node:18-bullseye AS builder

# Встановлюємо робочу директорію
WORKDIR /app

# Копіюємо package.json і package-lock.json (якщо є)
COPY package*.json ./

# Встановлюємо залежності
RUN npm ci --only=production --silent

# Копіюємо весь код
COPY . .

# Збираємо проєкт
RUN npm run build

# Production stage з nginx
FROM nginx:alpine

# Копіюємо збудовані статичні файли
COPY --from=builder /app/dist/spa /usr/share/nginx/html

# Копіюємо кастомну конфігурацію nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Відкриваємо порт 80
EXPOSE 80

# Запускаємо nginx
CMD ["nginx", "-g", "daemon off;"]
