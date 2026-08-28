# AIDA Enterprise API Foundation
## WebSocket API Guide

**Versiya:** 1.0.0
**Sana:** 2026-07-03
**Muallif:** AIDA API Team

---

## 1. WEBSOCKET ARXITEKTURASI

```
Nima uchun WebSocket (SSE emas):
  Real-time ikki tomonlama aloqa kerak bo'lganda:
  ✅ Agent events (agent → server → client)
  ✅ Live chat (foydalanuvchi va agent o'rtasida)
  ✅ Workflow events (real-time progress)
  ✅ Notifications (push)
  ✅ Monitoring updates (live dashboard)
  ✅ Terminal session (input/output)
  SSE uchun: faqat AI token streaming (bir tomonlama)

Stack:
  Django Channels (ASGI)
  Channel Layer: Redis (pub/sub)
  Protocol: WSS (WebSocket Secure)
```

```
┌───────────────────────────────────────────────────────────────┐
│                   WEBSOCKET ARCHITECTURE                      │
│                                                               │
│  Client                    Django Channels       Redis        │
│    │                            │                  │          │
│    │  WSS handshake ───────────▶│                  │          │
│    │  Auth: ?token=JWT          │                  │          │
│    │◀── 101 Switching ──────────│                  │          │
│    │                            │ SUBSCRIBE ───────▶│         │
│    │                            │ channel:user:{id} │         │
│    │                            │                  │          │
│    │  {"type":"ping"} ─────────▶│                  │          │
│    │◀── {"type":"pong"} ────────│                  │          │
│    │                            │                  │          │
│    │                      [AI Agent runs]           │          │
│    │                            │◀── PUBLISH ───────│         │
│    │◀── agent_event ────────────│                  │          │
│    │◀── agent_event ────────────│                  │          │
│    │                            │                  │          │
│    │  {"type":"close"} ────────▶│                  │          │
│    │◀── connection closed ──────│                  │          │
└───────────────────────────────────────────────────────────────┘
```

---

## 2. WEBSOCKET ENDPOINTS

| Endpoint | Maqsad | Auth |
|----------|--------|------|
| `wss://api.aida.ai/ws/` | Asosiy universal channel | JWT query param |
| `wss://api.aida.ai/ws/chat/{id}/` | Chat live events | JWT |
| `wss://api.aida.ai/ws/agents/{id}/` | Agent events | JWT |
| `wss://api.aida.ai/ws/workflows/{id}/` | Workflow events | JWT |
| `wss://api.aida.ai/ws/terminal/{session_id}/` | Terminal session | JWT |
| `wss://api.aida.ai/ws/notifications/` | User notifications | JWT |
| `wss://api.aida.ai/ws/monitoring/` | System monitoring | Admin JWT |

---

## 3. AUTENTIFIKATSIYA

### 3.1 Connection Auth

```
WebSocket'da Authorization header ishlatilmaydi (browser cheklovi).
Muqobil usullar:

USUL 1: Query parameter (tavsiya)
  wss://api.aida.ai/ws/agents/123/?token={jwt_token}
  Muammo: URL loglarida token ko'rinishi mumkin
  Yechim: Short-lived WS token (30 sek, faqat WS uchun)

USUL 2: First message auth
  1. WS connect (auth yo'q)
  2. Client birinchi message: {"type": "auth", "token": "..."}
  3. Server: token verify → yoki accept yoki reject+close

USUL 3: Cookie (web browser uchun)
  HttpOnly cookie mavjud bo'lsa avtomatik yuboriladi

AIDA yondashuvi: USUL 1 + short-lived WS token
```

### 3.2 WS Token

```
Short-lived WebSocket Token:
  POST /api/v1/auth/ws-token/
  Response: {"ws_token": "...", "expires_in": 30}

  ws_token → Redis'da 30 sek saqlanadi
  wss://api.aida.ai/ws/?token={ws_token}
  Connection establish bo'lganda ws_token o'chiriladi (single-use)

Afzallik:
  JWT URL loglarida qolmaydi (ws_token log'dan keyin bekor bo'ladi)
  JWT qisqa muddatli emas (15 min), ws_token 30 sek
```

---

## 4. MESSAGE PROTOKOLI

### 4.1 Umumiy Message Format

```json
// Client → Server
{
  "type": "message_type",
  "id": "msg_uuid",
  "payload": { }
}

// Server → Client
{
  "type": "event_type",
  "id": "evt_uuid",
  "timestamp": "2026-07-03T11:00:07Z",
  "channel": "agent:123",
  "payload": { }
}
```

### 4.2 System Messages

#### Ping / Pong (keepalive)
```json
// Client → Server (har 30 sek)
{"type": "ping", "id": "ping_001"}

// Server → Client
{"type": "pong", "id": "ping_001", "timestamp": "2026-07-03T11:00:07Z"}
```

#### Subscribe (kanal obuna)
```json
// Client → Server
{
  "type": "subscribe",
  "id": "sub_001",
  "payload": {
    "channels": ["agent:123", "workflow:456", "notifications"]
  }
}

// Server → Client (tasdiqlash)
{
  "type": "subscribed",
  "id": "sub_001",
  "payload": {
    "channels": ["agent:123", "workflow:456", "notifications"],
    "subscribed_at": "2026-07-03T11:00:07Z"
  }
}
```

#### Unsubscribe
```json
{"type": "unsubscribe", "payload": {"channels": ["agent:123"]}}
```

#### Error
```json
{
  "type": "error",
  "payload": {
    "code": "UNAUTHORIZED",
    "message": "Token expired. Reconnect with a fresh token.",
    "close": true
  }
}
```

---

## 5. AGENT EVENTS

### 5.1 Agent Lifecycle Events

```json
// Agent ishga tushdi
{
  "type": "agent.started",
  "channel": "agent:123",
  "timestamp": "2026-07-03T11:00:07Z",
  "payload": {
    "agent_id": "agent-uuid",
    "agent_name": "Code Reviewer",
    "task_id": "task-uuid",
    "task_type": "code_review"
  }
}

// Agent fikrlayapti
{
  "type": "agent.thinking",
  "channel": "agent:123",
  "payload": {
    "agent_id": "agent-uuid",
    "thought": "Analyzing the code structure...",
    "step": 1
  }
}

// Agent tool ishlatdi
{
  "type": "agent.tool_called",
  "channel": "agent:123",
  "payload": {
    "agent_id": "agent-uuid",
    "tool_name": "code_search",
    "arguments": {"query": "authentication middleware"},
    "tool_call_id": "call_abc"
  }
}

// Tool natijasi
{
  "type": "agent.tool_result",
  "channel": "agent:123",
  "payload": {
    "tool_call_id": "call_abc",
    "tool_name": "code_search",
    "status": "success",
    "result_summary": "Found 3 relevant files"
  }
}

// Agent qadam bajarishdi
{
  "type": "agent.step_completed",
  "channel": "agent:123",
  "payload": {
    "agent_id": "agent-uuid",
    "step": 2,
    "total_steps": 5,
    "progress_percent": 40,
    "step_result": "Code structure analyzed"
  }
}

// Agent tugadi
{
  "type": "agent.completed",
  "channel": "agent:123",
  "payload": {
    "agent_id": "agent-uuid",
    "task_id": "task-uuid",
    "status": "success",
    "duration_ms": 12400,
    "result_preview": "Found 3 critical issues..."
  }
}

// Agent xatosi
{
  "type": "agent.error",
  "channel": "agent:123",
  "payload": {
    "agent_id": "agent-uuid",
    "error_code": "TOOL_TIMEOUT",
    "error_message": "Code search timed out",
    "retry_count": 1,
    "max_retries": 3
  }
}
```

---

## 6. WORKFLOW EVENTS

```json
// Workflow boshlandi
{
  "type": "workflow.started",
  "channel": "workflow:456",
  "payload": {
    "workflow_id": "wf-uuid",
    "workflow_name": "Document Processing",
    "total_steps": 5
  }
}

// Qadam boshlandi
{
  "type": "workflow.step_started",
  "channel": "workflow:456",
  "payload": {
    "workflow_id": "wf-uuid",
    "step_index": 2,
    "step_name": "Extract Text",
    "agent_id": "agent-uuid"
  }
}

// Qadam tugadi
{
  "type": "workflow.step_completed",
  "channel": "workflow:456",
  "payload": {
    "workflow_id": "wf-uuid",
    "step_index": 2,
    "step_name": "Extract Text",
    "duration_ms": 3400,
    "completed_steps": 3,
    "remaining_steps": 2,
    "progress_percent": 60
  }
}

// Workflow tugadi
{
  "type": "workflow.completed",
  "channel": "workflow:456",
  "payload": {
    "workflow_id": "wf-uuid",
    "status": "success",
    "total_duration_ms": 18500,
    "result_url": "/api/v1/workflows/wf-uuid/result/"
  }
}

// Workflow xatosi
{
  "type": "workflow.error",
  "channel": "workflow:456",
  "payload": {
    "workflow_id": "wf-uuid",
    "step_index": 3,
    "error_code": "AGENT_TIMEOUT",
    "recoverable": true
  }
}
```

---

## 7. NOTIFICATIONS

```json
// Yangi notification
{
  "type": "notification.new",
  "channel": "notifications",
  "payload": {
    "id": "notif-uuid",
    "category": "system",
    "priority": "high",
    "title": "Workflow Completed",
    "message": "Document processing workflow finished successfully",
    "action_url": "/workflows/456/result",
    "read": false,
    "created_at": "2026-07-03T11:00:07Z"
  }
}

// Notification o'qildi (Server → Client)
{
  "type": "notification.read",
  "payload": {"notification_id": "notif-uuid"}
}

// Badge count yangilash
{
  "type": "notification.badge_update",
  "payload": {"unread_count": 3}
}
```

### Notification Kategoriyalari

```
system:      Tizim xabarlari
agent:       Agent tugadi / xato
workflow:    Workflow holati
task:        Task natijasi
mention:     Kimdir eslatma qo'ydi
security:    Xavfsizlik hodisasi
billing:     To'lov eslatma
```

---

## 8. MONITORING EVENTS (Admin)

```json
// CPU spike
{
  "type": "monitoring.alert",
  "channel": "monitoring",
  "payload": {
    "alert_name": "HighCPUUsage",
    "severity": "high",
    "value": 87.3,
    "threshold": 80,
    "instance": "backend-1",
    "fired_at": "2026-07-03T11:00:07Z"
  }
}

// Metrika yangilash (live dashboard uchun)
{
  "type": "monitoring.metrics",
  "channel": "monitoring",
  "payload": {
    "timestamp": "2026-07-03T11:00:07Z",
    "cpu_percent": 42.3,
    "ram_percent": 64.1,
    "active_agents": 12,
    "api_rps": 238,
    "ai_requests_per_min": 45
  }
}
```

---

## 9. TERMINAL EVENTS

```json
// Client: buyruq yuborish
{
  "type": "terminal.input",
  "id": "input_001",
  "payload": {"data": "ls -la\n"}
}

// Server: chiqish
{
  "type": "terminal.output",
  "payload": {
    "data": "total 48\ndrwxr-xr-x 2 user user 4096 Jul  3 11:00 .\n",
    "stream": "stdout"
  }
}

// Terminal resize
{
  "type": "terminal.resize",
  "payload": {"cols": 120, "rows": 40}
}

// Terminal exit
{
  "type": "terminal.exit",
  "payload": {"exit_code": 0}
}
```

---

## 10. CONNECTION MANAGEMENT

### 10.1 Reconnect Strategiyasi

```
Avtomatik reconnect (client tomonida):
  attempt 1: 1 sek kutish
  attempt 2: 2 sek
  attempt 3: 4 sek
  attempt 4: 8 sek
  attempt 5: 16 sek
  Max attempts: 10
  Max delay: 30 sek
  Jitter: ±500ms

Close codes:
  1000 → Normal close (reconnect kerak emas)
  1001 → Server restart (reconnect qiling)
  1006 → Abnormal (reconnect qiling)
  4000 → Auth failure (token yangilab reconnect)
  4001 → Rate limited (Retry-After headerga qarang)
  4002 → Forbidden (reconnect kerak emas)
```

### 10.2 Channel Layer (Redis)

```
Django Channels + Redis channel layer:

Channel groups:
  user_{user_id}          → Foydalanuvchiga shaxsiy
  agent_{agent_id}        → Agent events
  workflow_{workflow_id}  → Workflow events
  org_{org_id}            → Org-wide notifications
  monitoring              → System monitoring (admin)

Publish (agent service → Redis → WebSocket client):
  channel_layer.group_send("agent_{id}", event_dict)

Scaling:
  Har backend instance Redis channel layer'ga ulangan
  Message istalgan instance'ga kelishi mumkin
  Redis pub/sub to'g'ri instance'ga yo'naltiradi
```

### 10.3 Heartbeat

```
Server → Client: Har 30 sek ping
  {"type": "ping", "timestamp": "..."}

Client javob bermasa: 60 sek → connection yopiladi
Client keepalive: Har 25 sek pong yuboradi

Idle timeout: 5 daqiqa (hech qanday message yo'q)
Max connection duration: 24 soat (keyin reconnect talab qilinadi)
```

---

## 11. SECURITY

```
WSS (TLS) majburiy:
  ws:// → 400 Bad Request (upgrade talab qilinadi)

Origin check:
  Allowed origins whitelist'da bo'lishi shart
  CORS_ALLOWED_ORIGINS qoidalari WS ga ham qo'llanadi

Message size limit:
  Max message: 64KB (terminal uchun 256KB)
  Spam protection: Max 100 msg/sek per connection

Rate limiting:
  Max concurrent connections per user: 5
  Max total connections: 10,000

Input validation:
  Har message JSON schema bilan validate qilinadi
  Unknown message type → error (close emas)
```

---

*Hujjat AIDA Development Bible — Book 1, Chapter 9 asosida tayyorlangan.*
