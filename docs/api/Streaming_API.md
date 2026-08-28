# AIDA Enterprise API Foundation
## Streaming API Guide

**Versiya:** 1.0.0
**Sana:** 2026-07-03
**Muallif:** AIDA API Team

---

## 1. STREAMING ARXITEKTURASI

AIDA AI javoблari uchun **Server-Sent Events (SSE)** protokoli ishlatiladi.

```
Nima uchun SSE (WebSocket emas AI streaming uchun):
  ✅ Bir tomonlama (server → client) — AI javob uchun ideal
  ✅ HTTP/1.1 bilan ishlaydi (proxy/CDN muammosi yo'q)
  ✅ Avtomatik reconnect (browser built-in)
  ✅ Load balancer friendly
  ✅ Oddiy — EventSource API bilan ishlash oson
  WebSocket ikki tomonlama kerak bo'lganda ishlatiladi (agent events, notifications)
```

```
┌──────────────────────────────────────────────────────┐
│                  STREAMING FLOW                      │
│                                                      │
│  Client                          Server              │
│    │                               │                 │
│    │  POST /messages/stream/       │                 │
│    │  Accept: text/event-stream ──▶│                 │
│    │                               │ Auth check      │
│    │                               │ Validation      │
│    │                               │ AI API call     │
│    │◀── HTTP 200 ──────────────────│                 │
│    │    Content-Type:              │                 │
│    │    text/event-stream          │                 │
│    │                               │                 │
│    │◀── event: token ─────────────│ token 1         │
│    │◀── event: token ─────────────│ token 2         │
│    │◀── event: token ─────────────│ token 3 ...     │
│    │◀── event: done ──────────────│ stream tugadi   │
│    │                               │                 │
│    │  DELETE /messages/stream/{id} │ (cancel)        │
│    │──────────────────────────────▶│                 │
└──────────────────────────────────────────────────────┘
```

---

## 2. STREAMING ENDPOINT

### 2.1 Stream Boshlash

```http
POST /api/v1/chats/{chat_id}/messages/stream/
Authorization: Bearer {token}
Content-Type: application/json
Accept: text/event-stream
Cache-Control: no-cache
X-Request-ID: req_abc123

{
  "content": "Explain quantum computing in simple terms",
  "model_id": "gpt-4o",
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream_options": {
    "include_usage": true,
    "include_reasoning": false
  }
}
```

### 2.2 Streaming Response Headers

```http
HTTP/1.1 200 OK
Content-Type: text/event-stream; charset=utf-8
Cache-Control: no-cache, no-transform
X-Accel-Buffering: no          ← nginx buffering o'chirish
Connection: keep-alive
Transfer-Encoding: chunked
X-Stream-ID: stream_xyz789
X-Request-ID: req_abc123
```

---

## 3. SSE EVENT FORMATI

### 3.1 SSE Protokol Strukturasi

```
SSE format:
  event: {event_type}
  data: {json_payload}
  id: {event_id}
  retry: {ms}

  (bo'sh qator — event tugadi)
```

### 3.2 Event Turlari

#### `stream_start` — Stream boshlanishi

```
event: stream_start
data: {"stream_id":"stream_xyz789","model":"gpt-4o","created_at":"2026-07-03T11:00:07Z"}
id: 1

```

#### `token` — Har bir token

```
event: token
data: {"token":"Quantum","index":0}
id: 2

event: token
data: {"token":" computing","index":1}
id: 3

event: token
data: {"token":" is","index":2}
id: 4
```

#### `reasoning` — Model o'ylash jarayoni (agar qo'llab-quvvatlansa)

```
event: reasoning
data: {"content":"The user wants a simple explanation...","type":"thinking"}
id: 5
```

#### `tool_call` — Tool chaqiruvi (function calling)

```
event: tool_call
data: {
  "tool_call_id":"call_abc",
  "tool_name":"web_search",
  "arguments":{"query":"quantum computing basics"}
}
id: 10
```

#### `tool_result` — Tool natijasi

```
event: tool_result
data: {
  "tool_call_id":"call_abc",
  "result":"Quantum computing uses quantum bits...",
  "status":"success"
}
id: 11
```

#### `progress` — Progress yangilash (uzoq jarayonlar uchun)

```
event: progress
data: {"step":"retrieving_context","percent":30,"message":"Searching knowledge base..."}
id: 15
```

#### `partial_result` — Qisman natija

```
event: partial_result
data: {"content":"Quantum computing is a type of computation...","is_complete":false}
id: 20
```

#### `done` — Stream yakunlanishi

```
event: done
data: {
  "message_id": "msg_uuid",
  "finish_reason": "stop",
  "usage": {
    "tokens_input": 42,
    "tokens_output": 287,
    "total_tokens": 329
  },
  "model": "gpt-4o",
  "duration_ms": 2340
}
id: 99

```

#### `error` — Stream xatosi

```
event: error
data: {
  "code": "AI_PROVIDER_ERROR",
  "message": "OpenAI returned an error",
  "recovery": "Try again or switch to a different model"
}
id: 50

```

---

## 4. TOKEN STREAMING MEXANIZMI

### 4.1 Token Buffer Strategiyasi

```
Muammo: Juda kichik token'lar (1-2 belgi) juda ko'p network overhead yaratadi

Yechim: Token buffer
  - Buffer: 5-10 token to'plab yuborish
  - Flush interval: 50ms (buffer to'lmasa ham)
  - Min flush size: 1 token (oxirgi token'lar uchun)

Django implementation konsepsiyasi:
  async generator → token buffer → SSE flush

Latency maqsadi:
  TTFT (Time To First Token): < 500ms
  Token throughput: > 30 token/sec
```

### 4.2 Backpressure

```
Agar client sekin o'qisa:
  Nginx buffer:  64KB (oshsa connection sekinlashadi)
  Server buffer: 512KB (oshsa AI provider backpressure)

Timeout:
  Idle timeout: 30 sek (token kelmasa)
  Max duration: 300 sek (5 daqiqa)
```

---

## 5. STREAM CANCELLATION

### 5.1 Cancel Endpointi

```http
DELETE /api/v1/chats/{chat_id}/messages/stream/{stream_id}/
Authorization: Bearer {token}
X-Request-ID: req_cancel123
```

Response:
```json
{
  "status": 200,
  "success": true,
  "message": "Stream cancelled successfully",
  "data": {
    "stream_id": "stream_xyz789",
    "cancelled_at": "2026-07-03T11:00:15Z",
    "tokens_generated": 45
  }
}
```

### 5.2 Cancel Mexanizmi

```
Mexanizm:
  1. Client: DELETE /stream/{stream_id}/
  2. Server: Redis'da stream_{stream_id} = "cancelled"
  3. Stream generator: har token'dan keyin Redis check
  4. Cancelled bo'lsa: AI API connection uziladi (provider cancel)
  5. SSE: "event: cancelled" yuboriladi
  6. Connection yopiladi

Redis key:
  stream:cancel:{stream_id} = "1" (TTL: 60 sek)

SSE event:
  event: cancelled
  data: {"stream_id":"stream_xyz789","tokens_generated":45,"reason":"user_cancelled"}
```

### 5.3 Client-side Disconnect

```
Browser tab yopilsa:
  Connection abort → Django AsyncToSync → AI API abort
  Partial message DB'da saqlanadi (finish_reason = "cancelled")
```

---

## 6. PLATFORM API STREAMING

Tashqi platformalar uchun:

```http
POST /api/platform/chat/stream/
X-AIDA-Key: aida_sk_...
Content-Type: application/json
Accept: text/event-stream

{
  "prompt": "Mahsulotlaringiz haqida so'rang",
  "page": "product-detail",
  "customer_intent": "purchase",
  "locale": "uz"
}
```

---

## 7. RAG STREAMING

Knowledge base dan qidiruvni streaming bilan birlashtirish:

```
event: progress
data: {"step":"searching_knowledge","percent":20}

event: progress
data: {"step":"retrieved_sources","percent":40,"sources_count":3}

event: sources
data: {"sources":[{"id":"...","title":"...","relevance":0.95}]}

event: token
data: {"token":"Based"}

... (tokens davom etadi)

event: done
data: {"finish_reason":"stop","sources_used":3}
```

---

## 8. CLIENT IMPLEMENTATION MISOLLARI (KONSEPSIYA)

### JavaScript (EventSource)

```javascript
// Dizayn konsepsiyasi

const response = await fetch('/api/v1/chats/{id}/messages/stream/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
    'Accept': 'text/event-stream',
  },
  body: JSON.stringify({ content: userMessage })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

// SSE manual parsing
// Her "data: {json}\n\n" parse qilinadi
// event: token → DOM'ga token qo'shiladi
// event: done → UI tugallanadi
// event: error → error ko'rsatiladi
```

### Python (httpx streaming)

```python
# Dizayn konsepsiyasi

import httpx, json

with httpx.stream('POST', url, headers=headers, json=payload) as r:
    for line in r.iter_lines():
        if line.startswith('data: '):
            data = json.loads(line[6:])
            if data.get('token'):
                print(data['token'], end='', flush=True)
        elif line.startswith('event: done'):
            break
```

---

## 9. MONITORING VA METRICS

```
Prometheus metrics:

aida_stream_started_total          → Counter (stream boshlangan)
aida_stream_completed_total        → Counter (finish_reason label)
aida_stream_cancelled_total        → Counter
aida_stream_error_total            → Counter (error_code label)
aida_stream_ttft_seconds           → Histogram (Time To First Token)
aida_stream_duration_seconds       → Histogram
aida_stream_tokens_total           → Counter (model label)
aida_stream_active_count           → Gauge (hozir nechta stream aktiv)
```

---

*Hujjat AIDA Development Bible — Book 1, Chapter 9 asosida tayyorlangan.*
