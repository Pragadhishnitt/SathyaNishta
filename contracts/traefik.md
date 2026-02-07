# Traefik Configuration Contract

**Version:** 1.0.0  
**Owner:** Team A  
**Last Updated:** Sprint 1

---

## Overview

Traefik acts as the **edge reverse proxy** for Sathya Nishta. It enforces rate limiting, authentication, and routes requests to the backend service.

---

## Middleware Definitions

### 1. Rate Limiting Middleware

**Name:** `rate-limit-api`

**Policy:**
- **Rate:** 100 requests per minute
- **Burst:** 50 requests (allows short bursts above the rate)
- **Scope:** Per source IP address
- **Response on breach:** HTTP 429 Too Many Requests

**Traefik config:**
```yaml
http:
  middlewares:
    rate-limit-api:
      rateLimit:
        average: 100
        period: 1m
        burst: 50
        sourceCriterion:
          ipStrategy:
            depth: 0
```

**Error response:**
```json
{
  "error": "Rate Limit Exceeded",
  "message": "You have exceeded 100 requests per minute. Please try again later.",
  "code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 45
}
```

---

### 2. Authentication Middleware

**Name:** `api-key-auth`

**Policy:**
- Validates `X-API-Key` header
- Rejects requests with missing or invalid API key
- Response on failure: HTTP 401 Unauthorized

**Traefik config:**
```yaml
http:
  middlewares:
    api-key-auth:
      forwardAuth:
        address: "http://backend:8000/auth/validate"
        authResponseHeaders:
          - "X-User-ID"
```

**Error response:**
```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing API key",
  "code": "UNAUTHORIZED"
}
```

---

## Routing Rules

### Route: API Endpoints

**Path:** `/api/v1/*`  
**Target:** `http://backend:8000`  
**Middlewares:** `rate-limit-api`, `api-key-auth`

**Traefik config:**
```yaml
http:
  routers:
    api-router:
      rule: "PathPrefix(`/api/v1`)"
      service: backend-service
      middlewares:
        - rate-limit-api
        - api-key-auth
      entryPoints:
        - web

  services:
    backend-service:
      loadBalancer:
        servers:
          - url: "http://backend:8000"
```

---

### Route: Health Check

**Path:** `/health`  
**Target:** `http://backend:8000/health`  
**Middlewares:** None (public endpoint)

**Traefik config:**
```yaml
http:
  routers:
    health-router:
      rule: "Path(`/health`)"
      service: backend-service
      entryPoints:
        - web
```

---

## Entry Points

**Port 80 (HTTP):**
```yaml
entryPoints:
  web:
    address: ":80"
```

**Port 443 (HTTPS) — Future:**
```yaml
entryPoints:
  websecure:
    address: ":443"
    http:
      tls:
        certResolver: letsencrypt
```

---

## Health Checks

Traefik monitors backend service health:

```yaml
http:
  services:
    backend-service:
      loadBalancer:
        healthCheck:
          path: /health
          interval: 10s
          timeout: 3s
```

**Expected response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-02-04T12:00:00Z"
}
```

---

## Docker Compose Integration

```yaml
services:
  traefik:
    image: traefik:v2.10
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
    ports:
      - "80:80"
      - "8080:8080"  # Traefik dashboard
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - sathya-network

  backend:
    image: sathya-backend:latest
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api-router.rule=PathPrefix(`/api/v1`)"
      - "traefik.http.routers.api-router.middlewares=rate-limit-api,api-key-auth"
      - "traefik.http.routers.health-router.rule=Path(`/health`)"
    networks:
      - sathya-network
```

---

## Testing

### Test Rate Limiting
```bash
# Send 150 requests in 1 minute (should trigger 429 after 100)
for i in {1..150}; do
  curl -X POST http://localhost/api/v1/investigate \
    -H "X-API-Key: test-key" \
    -H "Content-Type: application/json" \
    -d '{"query": "test"}' &
done
```

### Test Authentication
```bash
# Missing API key (should return 401)
curl -X POST http://localhost/api/v1/investigate \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'

# Valid API key (should return 202)
curl -X POST http://localhost/api/v1/investigate \
  -H "X-API-Key: valid-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "Investigate Adani"}'
```

### Test Health Check
```bash
# Should return 200 without API key
curl http://localhost/health
```
