# AIDA Enterprise Monitoring Platform
## Dashboard Design Specification

**Versiya:** 1.0.0  
**Sana:** 2026-07-03  
**Muallif:** AIDA SRE Team  
**Holat:** Production-Ready Design

---

## 1. DASHBOARD IERARXIYASI

```
AIDA Monitoring Dashboards
├── 1. System Overview          ← Bosh dashboard
├── 2. AI Models Dashboard      ← AI model statistikasi
├── 3. Agent Dashboard          ← Agent monitoring
├── 4. Workflow Dashboard        ← Workflow tracking
├── 5. API Dashboard             ← Endpoint monitoring
├── 6. Database Dashboard        ← DB monitoring
├── 7. Cache Dashboard           ← Redis monitoring
├── 8. Security Dashboard        ← Xavfsizlik hodisalari
└── 9. Infrastructure Dashboard  ← CPU, RAM, GPU, Disk, Network
```

---

## 2. SYSTEM OVERVIEW DASHBOARD

### 2.1 Status Bar (Yuqori qator)

```
┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
│ BACKEND  │FRONTEND  │DATABASE  │  REDIS   │AI MODELS │  AGENTS  │
│  ● UP    │  ● UP    │  ● UP    │  ● UP    │  ● UP    │  ● UP    │
└──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
```

Har bir status:
- 🟢 `UP` — servis ishlayapti
- 🟡 `DEGRADED` — qisman ishlamoqda
- 🔴 `DOWN` — servis to'xtagan
- ⚫ `UNKNOWN` — status aniqlanmagan

### 2.2 Resource Usage (Real-time Gauges)

```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│  CPU USAGE   │  RAM USAGE   │  GPU USAGE   │  DISK USAGE  │
│              │              │              │              │
│   ████░░░░   │   ██████░░   │   ███░░░░░   │   ████████   │
│    42%       │    64%       │    38%       │    87%       │
│  Threshold   │  Threshold   │  Threshold   │  Threshold   │
│    80%       │    85%       │    90%       │    90%       │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

### 2.3 Network Usage

```
┌────────────────────────────────────────────────────────────┐
│  NETWORK I/O                                               │
│  ↑ TX: 125 MB/s    ↓ RX: 89 MB/s    Total: 214 MB/s       │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁  TX (sent)                         │  │
│  │ ▁▁▂▃▃▄▄▅▄▃▃▂▂▁▁  RX (received)                     │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

### 2.4 Quick Stats Row

```
┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
│  RUNNING │  RUNNING │   API    │  DB      │  CACHE   │  ACTIVE  │
│  AGENTS  │  TASKS   │  RPS     │  QPS     │  HIT %   │  ALERTS  │
│    12    │   47     │  238     │  1,420   │  94.2%   │    3     │
└──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
```

### 2.5 Timeline Grafiklar (Past 1h / 6h / 24h)

```
Timeline panellari (har biri alohida Grafana panel):

┌─────────────────────────────────────────────┐
│  CPU Timeline                               │
│  100%│                                      │
│   80%│    ▄▅▆▅▄▃▃▄▅▄▄▃▃▂▂▂▃▄▅              │
│   60%│▂▃▄▄                    ▄▅▆▅▄▄▃       │
│   40%│                                      │
│   20%│                                      │
│    0%└──────────────────────────────────    │
│       00:00      06:00      12:00  18:00    │
└─────────────────────────────────────────────┘

Xuddi shunday panellar:
  • RAM Timeline
  • GPU Timeline
  • Network Timeline
  • Requests Timeline
  • Errors Timeline
  • Agent Timeline
  • Workflow Timeline
```

---

## 3. AI MODELS DASHBOARD

### 3.1 Model Overview Table

```
┌──────────────┬──────────────┬───────┬─────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
│ Model Name   │ Provider     │ Status│ Requests│ Success% │ Failure% │ Avg Time │ Avg Tok  │ Max Tok  │ Cost/Day │
├──────────────┼──────────────┼───────┼─────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ gpt-4o       │ OpenAI       │  🟢   │ 12,450  │  98.7%   │  1.3%    │  1.2s    │  842     │  8,192   │ $12.40   │
│ claude-3.5   │ Anthropic    │  🟢   │  8,230  │  99.1%   │  0.9%    │  0.9s    │  1,204   │ 16,384   │  $9.80   │
│ llama-3.1    │ Local        │  🟡   │  3,102  │  95.2%   │  4.8%    │  2.8s    │  612     │  4,096   │  $0.00   │
│ gemini-pro   │ Google       │  🟢   │  2,847  │  97.8%   │  2.2%    │  1.1s    │  924     │  8,192   │  $3.20   │
└──────────────┴──────────────┴───────┴─────────┴──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
```

### 3.2 Per-Model Detail Panels

Har bir model uchun quyidagi panellar:

```
┌──────────────────────────────────────────────────────────────────┐
│  MODEL: gpt-4o  │  Provider: OpenAI  │  Status: HEALTHY          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────┐   ┌──────────────────────────────────┐ │
│  │  Request Rate        │   │  Response Time Distribution      │ │
│  │  (req/min)           │   │  p50: 0.8s                       │ │
│  │  ▁▂▃▄▅▆▇▆▅▄▃▂       │   │  p95: 2.1s                       │ │
│  │                      │   │  p99: 4.3s                       │ │
│  └──────────────────────┘   └──────────────────────────────────┘ │
│                                                                  │
│  ┌──────────────────────┐   ┌──────────────────────────────────┐ │
│  │  Token Usage (24h)   │   │  Success vs Failure Rate         │ │
│  │  Input:  8.4M tokens │   │  ████████████████░░  98.7%       │ │
│  │  Output: 3.2M tokens │   │  ░░░░░░░░░░░░░░░░██   1.3%       │ │
│  └──────────────────────┘   └──────────────────────────────────┘ │
│                                                                  │
│  ┌──────────────────────┐   ┌──────────────────────────────────┐ │
│  │  Memory Usage        │   │  Cost Statistics                 │ │
│  │  Current: 4.2 GB     │   │  Today:    $12.40                │ │
│  │  Peak:    6.8 GB     │   │  This Week: $87.20               │ │
│  │  Limit:   8.0 GB     │   │  This Month: $312.80             │ │
│  └──────────────────────┘   └──────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## 4. AGENT DASHBOARD

### 4.1 Agent Pool Status

```
┌───────────────────────────────────────────────────────────────┐
│  AGENT POOL OVERVIEW                                          │
│                                                               │
│  Total Agents: 24    Active: 12    Idle: 8    Error: 4       │
│  Utilization: 50%    Queue Depth: 47 tasks                   │
└───────────────────────────────────────────────────────────────┘
```

### 4.2 Agent Status Table

```
┌───────────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────┬──────────────┐
│ Agent Name    │ Status   │ Assigned │Completed │  Failed  │ Avg Run  │ Retry│ Queue Pos    │
├───────────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────┼──────────────┤
│ agent-001     │ 🟢 RUN   │   142    │   138    │    4     │  12.3s   │   2  │    —         │
│ agent-002     │ 🟡 WAIT  │    89    │    89    │    0     │   8.7s   │   0  │    12        │
│ agent-003     │ 🔴 ERROR │    56    │    48    │    8     │  23.1s   │  14  │    —         │
│ agent-004     │ 🟢 RUN   │   201    │   197    │    4     │   6.2s   │   1  │    —         │
└───────────────┴──────────┴──────────┴──────────┴──────────┴──────────┴──────┴──────────────┘
```

---

## 5. WORKFLOW DASHBOARD

### 5.1 Active Workflows

```
┌────────────────────────────────────────────────────────────────────┐
│  ACTIVE WORKFLOWS                                                  │
├──────────────────┬──────────────┬───────┬─────────┬──────┬────────┤
│ Workflow Name    │ Current Step │ Done  │ Remain  │ Time │ Errors │
├──────────────────┼──────────────┼───────┼─────────┼──────┼────────┤
│ doc-processing   │ step 3/8     │   3   │    5    │ 45s  │   0    │
│ data-pipeline    │ step 7/12    │   7   │    5    │ 2m   │   1    │
│ model-training   │ step 2/5     │   2   │    3    │ 18m  │   0    │
│ report-gen       │ step 5/5     │   5   │    0    │ 1m   │   0    │
└──────────────────┴──────────────┴───────┴─────────┴──────┴────────┘
```

### 5.2 Workflow Progress Bar

```
doc-processing:
[████████████████████████░░░░░░░░░░░░░░░░] Step 3/8  37.5%

data-pipeline:
[████████████████████████████████████████████████████░░░░░░░░] Step 7/12  58.3%
  ⚠ 1 error in step 4
```

---

## 6. API DASHBOARD

### 6.1 Endpoint Performance Table

```
┌─────────────────────────────────────┬─────────┬────────┬────────┬────────┬────────┬────────┐
│ Endpoint                            │  Count  │  p50   │  p95   │  p99   │ Error% │  RPS   │
├─────────────────────────────────────┼─────────┼────────┼────────┼────────┼────────┼────────┤
│ POST /api/platform/chat/            │ 45,230  │  320ms │  890ms │ 2.1s   │  0.8%  │  52.4  │
│ GET  /api/health/                   │ 12,100  │   12ms │   28ms │  45ms  │  0.0%  │  14.0  │
│ POST /api/auth/login/               │  3,420  │   45ms │  120ms │  280ms │  2.1%  │   3.9  │
│ GET  /api/agents/status/            │  8,900  │   89ms │  210ms │  540ms │  0.3%  │  10.3  │
│ POST /api/workflows/start/          │  1,240  │  450ms │ 1.2s   │  3.4s  │  1.2%  │   1.4  │
└─────────────────────────────────────┴─────────┴────────┴────────┴────────┴────────┴────────┘
```

### 6.2 Request Rate Timeline

```
Grafana panels:
  • Request rate per endpoint (stacked area chart)
  • Error rate timeline (red line)
  • Latency heatmap
  • HTTP status code distribution (pie chart)
```

---

## 7. INFRASTRUCTURE DASHBOARD

### 7.1 Resource Overview

```
┌───────────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE RESOURCES                       │
│                                                                   │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────────────┐  │
│  │     CPU       │  │     RAM       │  │         GPU           │  │
│  │               │  │               │  │                       │  │
│  │  ┌─────────┐  │  │  ┌─────────┐  │  │  Device: NVIDIA A100  │  │
│  │  │ 42%     │  │  │  │ 64%     │  │  │  CUDA Cores: 6912     │  │
│  │  │ 8 cores │  │  │  │ 64/100GB│  │  │  VRAM: 38/80 GB       │  │
│  │  │ Load:2.3│  │  │  │ Swap:2% │  │  │  Temp: 72°C           │  │
│  │  └─────────┘  │  │  └─────────┘  │  │  Fan: 65%             │  │
│  └───────────────┘  └───────────────┘  └───────────────────────┘  │
│                                                                   │
│  ┌───────────────────────┐  ┌──────────────────────────────────┐  │
│  │        DISK           │  │           NETWORK                │  │
│  │  /       87% 870GB    │  │  eth0                            │  │
│  │  /data   45% 450GB    │  │  ↑ TX: 125 MB/s                  │  │
│  │  /logs   72% 720GB    │  │  ↓ RX: 89 MB/s                   │  │
│  │  I/O: 240 MB/s read   │  │  Packets: 18,420/s               │  │
│  │  I/O: 180 MB/s write  │  │  Errors: 0                       │  │
│  └───────────────────────┘  └──────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
```

### 7.2 Docker Containers Table

```
┌────────────────────┬──────────┬───────┬───────┬────────────────┬────────┐
│ Container          │ Status   │ CPU%  │ RAM   │ Uptime         │ Restart│
├────────────────────┼──────────┼───────┼───────┼────────────────┼────────┤
│ aida-backend       │ 🟢 UP    │ 12.3% │ 1.2GB │ 7d 4h 23m      │   0    │
│ aida-celery        │ 🟢 UP    │  8.7% │ 842MB │ 7d 4h 23m      │   0    │
│ aida-postgres      │ 🟢 UP    │  3.2% │ 2.4GB │ 12d 8h 12m     │   0    │
│ aida-redis         │ 🟢 UP    │  1.1% │ 284MB │ 12d 8h 12m     │   0    │
│ aida-prometheus    │ 🟢 UP    │  4.8% │ 1.8GB │ 7d 4h 22m      │   0    │
│ aida-grafana       │ 🟢 UP    │  2.1% │ 512MB │ 7d 4h 21m      │   0    │
└────────────────────┴──────────┴───────┴───────┴────────────────┴────────┘
```

---

## 8. SECURITY DASHBOARD

```
┌──────────────────────────────────────────────────────────────┐
│  SECURITY MONITORING (Last 24h)                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Failed Logins: 47      ████░░░░░░  Normal range            │
│  Suspicious IPs: 3      ██░░░░░░░░  ⚠ Review needed        │
│  Permission Violations: 2           ✓ Low                   │
│  Rate Limit Events: 128 ██████░░░░  Normal                  │
│  API Abuse Events: 12   ███░░░░░░░  ⚠ Monitor              │
│  Invalid Key Attempts: 8            ✓ Low                   │
│                                                              │
│  Recent Events:                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 08:42 | FAILED_LOGIN   | IP: 192.168.x.x  | admin   │   │
│  │ 08:39 | RATE_LIMITED   | IP: 10.0.x.x     | api     │   │
│  │ 08:31 | PERM_VIOLATION | User: [masked]   | /admin  │   │
│  │ 08:15 | INVALID_KEY    | IP: 203.x.x.x    | api     │   │
│  └──────────────────────────────────────────────────────┘   │
│  NOTE: IP va User ma'lumotlari maskalanadi (PII xavfsizligi) │
└──────────────────────────────────────────────────────────────┘
```

---

## 9. GRAFANA KONFIGURATSIYA STANDARTLARI

### 9.1 Panel Turlari

| Panel turi | Ishlatilishi |
|------------|-------------|
| Gauge | CPU, RAM, Disk foiz ko'rsatish |
| Stat | Raqamli qiymatlar (count, rate) |
| Time series | Timeline grafiklar |
| Bar gauge | Comparisons (model performance) |
| Table | Agent/API/Container jadvallar |
| Heatmap | Latency distribution |
| Pie chart | Status distribution |
| Status history | Health check tarixi |
| Logs panel | Real-time log stream |

### 9.2 Color Scheme

```
Sog'lom:    #73BF69  (yashil)
Ogohlantirish: #FADE2A  (sariq)
Kritik:     #F2495C  (qizil)
Noma'lum:   #808080  (kulrang)
Ma'lumot:   #5794F2  (ko'k)
```

### 9.3 Refresh Intervals

| Dashboard | Refresh |
|-----------|---------|
| System Overview | 10s |
| AI Models | 30s |
| Agents | 15s |
| Workflows | 10s |
| API | 15s |
| Database | 30s |
| Security | 60s |
| Infrastructure | 15s |

### 9.4 Time Range Defaults

| Dashboard | Default Range | Max Range |
|-----------|--------------|-----------|
| Real-time | Last 15 min | Last 24h |
| Historical | Last 24h | Last 90 days |
| Reports | Last 7 days | Last 1 year |

---

## 10. XAVFSIZLIK CHEKLOVLARI

> ❌ **TAQIQLANGAN** — Dashboardda ko'rsatilmaydigan ma'lumotlar:

- API kalitlari va tokenlar
- Foydalanuvchi parollari yoki hash'lari
- Shaxsiy ma'lumotlar (ism, email, telefon)
- IP manzillar to'liq ko'rinishida (faqat subnet)
- Session tokenlar yoki JWT tarkibi
- Database connection string'lar

> ✅ **RUXSAT** — Ko'rsatilishi mumkin:
- Aggregated count va rate'lar
- Masked identifikatorlar
- Umumiy status va sog'liqlik holati
- Performance metrikalar

---

*Hujjat AIDA Development Bible — Book 1, Chapter 7 asosida tayyorlangan.*
