# ═══════════════════════════════════════════════════════════════
# STAGE 1: Dependencies
# ═══════════════════════════════════════════════════════════════
FROM node:20-alpine as deps

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# ═══════════════════════════════════════════════════════════════
# STAGE 2: Builder
# ═══════════════════════════════════════════════════════════════
FROM node:20-alpine as builder

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ .

# Build Next.js
RUN npm run build

# ═══════════════════════════════════════════════════════════════
# STAGE 3: Production — Serve with nginx
# ═══════════════════════════════════════════════════════════════
FROM nginx:alpine as production

# Copy nginx config
COPY infra/frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built Next.js app
COPY --from=builder /app/out /usr/share/nginx/html

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
