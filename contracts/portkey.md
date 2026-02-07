# Portkey Configuration Contract

**Version:** 1.0.0  
**Owner:** Team A  
**Last Updated:** Sprint 1

---

## Overview

Portkey Cloud acts as the **AI Gateway** for Sathya Nishta. It provides:
- **Semantic caching** (90% hit rate target)
- **Model routing** (Gemini 1.5 Flash primary)
- **Virtual keys** (security abstraction)
- **Failover** (automatic backup provider switching)

---

## Semantic Cache Configuration

### Cache Policy

**Cache Type:** Semantic (embedding-based similarity)  
**Similarity Threshold:** 0.95 (cosine similarity)  
**TTL (Time-to-Live):** 7 days  
**Max Cache Size:** 10,000 entries

**How it works:**
1. Incoming query is embedded using Portkey's internal embedding model
2. Embedding is compared against cached query embeddings
3. If similarity ≥ 0.95 → cache hit (return cached response)
4. If similarity < 0.95 → cache miss (forward to model)

**Portkey config:**
```json
{
  "cache": {
    "mode": "semantic",
    "max_age": 604800,
    "similarity_threshold": 0.95,
    "force_refresh": false
  }
}
```

**Expected hit rate:** 90% (based on repeated investigations of same companies)

---

## Model Routing

### Primary Model

**Provider:** Google Gemini  
**Model:** `gemini-1.5-flash`  
**Tier:** Free (15 RPM, 1500 RPD)

**Portkey virtual key:** `pk-sathya-gemini-primary`

**Config:**
```json
{
  "provider": "google",
  "model": "gemini-1.5-flash",
  "api_key": "{{ GEMINI_API_KEY }}",
  "virtual_key": "pk-sathya-gemini-primary",
  "retry": {
    "attempts": 3,
    "on_status_codes": [429, 500, 502, 503, 504]
  }
}
```

---

### Backup Model (Failover)

**Provider:** Together AI  
**Model:** `meta-llama/Llama-3-70b-chat-hf`  
**Tier:** Paid (fallback only)

**Portkey virtual key:** `pk-sathya-together-backup`

**Config:**
```json
{
  "provider": "together",
  "model": "meta-llama/Llama-3-70b-chat-hf",
  "api_key": "{{ TOGETHER_API_KEY }}",
  "virtual_key": "pk-sathya-together-backup"
}
```

---

## Failover Policy

**Trigger conditions:**
- Primary model returns HTTP 429 (rate limit exceeded)
- Primary model returns HTTP 503 (service unavailable)
- Primary model timeout (> 30 seconds)

**Failover behavior:**
- Automatically route request to backup model
- Log failover event to audit trail
- Return response with `X-Portkey-Fallback: true` header

**Portkey config:**
```json
{
  "fallbacks": [
    {
      "targets": [
        {"virtual_key": "pk-sathya-gemini-primary"},
        {"virtual_key": "pk-sathya-together-backup"}
      ],
      "on_status_codes": [429, 503, 504]
    }
  ]
}
```

---

## Virtual Keys

Virtual keys abstract the real API keys from the application.

**Mapping:**
| Virtual Key | Real Provider | Real Model | Real API Key |
|---|---|---|---|
| `pk-sathya-gemini-primary` | Google Gemini | `gemini-1.5-flash` | `{{ GEMINI_API_KEY }}` |
| `pk-sathya-together-backup` | Together AI | `Llama-3-70b-chat-hf` | `{{ TOGETHER_API_KEY }}` |

**Application usage:**
```python
import portkey

client = portkey.Portkey(
    api_key="pk-sathya-gemini-primary",  # Virtual key
    base_url="https://api.portkey.ai/v1"
)

response = client.chat.completions.create(
    model="gemini-1.5-flash",
    messages=[{"role": "user", "content": "Investigate Adani"}]
)
```

**Security benefit:** If the application is compromised, the attacker only gets the virtual key, not the real Gemini API key.

---

## Request Logging

Portkey logs all requests for observability:

**Logged fields:**
- Request ID (unique identifier)
- Timestamp
- Model used (primary or backup)
- Cache hit/miss
- Latency (ms)
- Token usage (input + output)
- Cost (if paid model)

**Example log entry:**
```json
{
  "request_id": "req_abc123",
  "timestamp": "2024-02-04T12:00:00Z",
  "model": "gemini-1.5-flash",
  "cache_hit": true,
  "latency_ms": 45,
  "tokens": {"input": 0, "output": 0},
  "cost": 0.0
}
```

---

## Cost Tracking

Portkey tracks costs per request:

**Free tier (Gemini):**
- Cost per request: ₹0
- Monthly quota: 1500 requests/day × 30 days = 45,000 requests

**Paid tier (Together AI fallback):**
- Cost per 1M input tokens: $0.60
- Cost per 1M output tokens: $0.80
- Average investigation: ~10,000 tokens → ~$0.014 per request

**Monthly budget alert:** If total cost > $50, send alert to Team A lead.

---

## Environment Variables

```bash
# Portkey API key (for authentication)
PORTKEY_API_KEY=pk_live_xxxxxxxxxxxxxxxx

# Virtual keys (used in application)
PORTKEY_VIRTUAL_KEY_PRIMARY=pk-sathya-gemini-primary
PORTKEY_VIRTUAL_KEY_BACKUP=pk-sathya-together-backup

# Real API keys (stored in Portkey dashboard, NOT in application)
# GEMINI_API_KEY=xxxxxxxxxxxxxxxx
# TOGETHER_API_KEY=xxxxxxxxxxxxxxxx
```

---

## Testing

### Test Semantic Cache
```bash
# First request (cache miss)
curl -X POST https://api.portkey.ai/v1/chat/completions \
  -H "x-portkey-api-key: $PORTKEY_API_KEY" \
  -H "x-portkey-virtual-key: pk-sathya-gemini-primary" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-1.5-flash",
    "messages": [{"role": "user", "content": "Investigate Adani for circular trading"}]
  }'

# Second request (same query, should be cache hit)
curl -X POST https://api.portkey.ai/v1/chat/completions \
  -H "x-portkey-api-key: $PORTKEY_API_KEY" \
  -H "x-portkey-virtual-key: pk-sathya-gemini-primary" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-1.5-flash",
    "messages": [{"role": "user", "content": "Investigate Adani for circular trading"}]
  }'

# Check response headers for cache status
# X-Portkey-Cache-Status: HIT
```

### Test Failover
```bash
# Simulate Gemini rate limit by sending 20 requests/min (exceeds 15 RPM)
for i in {1..20}; do
  curl -X POST https://api.portkey.ai/v1/chat/completions \
    -H "x-portkey-api-key: $PORTKEY_API_KEY" \
    -H "x-portkey-virtual-key: pk-sathya-gemini-primary" \
    -H "Content-Type: application/json" \
    -d '{
      "model": "gemini-1.5-flash",
      "messages": [{"role": "user", "content": "Test request '$i'"}]
    }' &
done

# Check response headers for failover
# X-Portkey-Fallback: true
# X-Portkey-Model-Used: meta-llama/Llama-3-70b-chat-hf
```
