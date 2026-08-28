# AIDA — Enterprise Dashboard Design

## 1. Design Principles

Dashboardlar AIDA holatini bir qarashda tushunish imkonini berishi kerak. Har bir dashboard aniq bir maqsad va auditoriyaga xizmat qiladi.

```
┌──────────────────────────────────────────────────────────────┐
│                    DASHBOARD ECOSYSTEM                        │
│                                                              │
│  Operator View     ← Grafana (infrastructure + metrics)       │
│  Developer View    ← Grafana (AI + agent + API details)      │
│  Business View     ← Grafana (cost, usage, SLA)              │
│  In-App View       ← React (embedded, user-facing)           │
│  Admin Panel       ← Django Admin (config + logs)            │
└──────────────────────────────────────────────────────────────┘
```

**Current State**: Hech qanday dashboard mavjud emas. Grafana va Prometheus konteynerlari hujjatlarda ko'rsatilgan, lekin implementatsiya qilinmagan.

## 2. Dashboard Architecture

### 2.1 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Metrics storage | Prometheus | Time-series metrics database |
| Long-term storage | Thanos / Cortex | Metrics aggregation & archival |
| Visualization | Grafana | Dashboards, charts, alerts |
| Log visualization | Grafana Loki | Log aggregation & search |
| Tracing visualization | Grafana Tempo / Jaeger | Distributed tracing UI |
| In-app dashboard | React + Chart.js | Embedded real-time metrics |
| Alert management | Grafana Alerting | Threshold rules + notifications |

### 2.2 Data Flow

```
AIDA Application
  │
  ├── /metrics (Prometheus endpoint)
  │     └── Prometheus (scrape every 15s)
  │           ├── Grafana (query + visualize)
  │           ├── Alertmanager (evaluate rules)
  │           └── Thanos (long-term storage)
  │
  ├── /health, /ready
  │     └── Probes (Kubernetes / Docker)
  │
  ├── Logs (JSON lines)
  │     └── Promtail → Loki → Grafana
  │
  ├── Traces (OpenTelemetry)
  │     └── OTel Collector → Tempo → Grafana
  │
  └── Events (Domain events)
        └── Event Bus → Metrics bridge
```

## 3. Dashboard Definitions

### 3.1 Grafana Dashboard: AIDA Overview

**Audience**: SRE / DevOps / Platform Engineers
**Refresh**: 30s auto-refresh

```
Row 1: System Status
┌─────────────────────────────────────────────────────────────────┐
│  [Status Panel]     │  [Status Panel]   │  [Status Panel]       │
│  API: ✅ Online     │  DB: ✅ Connected │  Redis: ✅ Connected  │
│  Uptime: 14d 3h     │  Queries: 1.2K/min│  Hit ratio: 94.5%    │
├──────────────────────┼───────────────────┼───────────────────────┤
│  [Status Panel]     │  [Status Panel]   │  [Status Panel]       │
│  Vector DB: ✅ OK   │  Queue: 0 pending │  Plugins: 5 active    │
│  Collections: 12    │  Processed: 500/h │  Errors: 0            │
└──────────────────────┴───────────────────┴───────────────────────┘

Row 2: Resource Usage
┌──────────────────────┬──────────────────────┬──────────────────────┐
│  CPU Usage           │  Memory Usage        │  GPU Usage           │
│  [Time Series Graph] │  [Time Series Graph] │  [Time Series Graph] │
│  Current: 45%        │  Current: 62% (4.2GB)│  Current: 78%        │
│  Max: 82%            │  Max: 85% (5.8GB)   │  Max: 95%            │
│  Avg: 38%            │  Avg: 54% (3.7GB)   │  Avg: 65%            │
└──────────────────────┴──────────────────────┴──────────────────────┘

Row 3: API Performance
┌──────────────────────┬──────────────────────┬──────────────────────┐
│  Requests/min        │  Latency (P50/P95/P99)│  Error Rate          │
│  [Time Series Graph] │  [Time Series Graph] │  [Time Series Graph] │
│  Current: 245/min    │  P50: 120ms          │  Current: 0.5%       │
│  Peak: 890/min       │  P95: 450ms          │  24h avg: 1.2%       │
│                       │  P99: 1200ms         │                      │
└──────────────────────┴──────────────────────┴──────────────────────┘

Row 4: AI Model Performance
┌──────────────────────┬──────────────────────┬──────────────────────┐
│  LLM Requests/min    │  Token Usage/min     │  Cost/min            │
│  [Time Series Graph] │  [Time Series Graph] │  [Time Series Graph] │
│  By provider stacked │  Prompt vs Completion│  By provider stacked │
└──────────────────────┴──────────────────────┴──────────────────────┘

Row 5: Agent Status
┌──────────────────────────────────────────────────────────────────┐
│  Agent Cards (one per agent)                                     │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │
│  │ Code   │ │ Secur. │ │ Debug  │ │ Resear.│ │ Memory │        │
│  │ ✅ 98% │ │ ✅ 95% │ │ ⚠️ 82%│ │ ✅ 99% │ │ ✅ 97% │        │
│  │ 1.2s   │ │ 2.1s   │ │ 0.8s   │ │ 3.4s   │ │ 0.3s   │        │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘        │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 Grafana Dashboard: AI & Agent Deep Dive

**Audience**: ML Team / AI Engineers
**Refresh**: 15s

```
Row 1: LLM Provider Comparison
┌──────────────────────────────────────────────────────────────────┐
│  Provider Health           │  Provider Latency (P50/P95)         │
│  [Table: Provider, Status,  │  [Time Series, multi-line]         │
│   Requests, Errors, Cost]  │  One line per provider             │
└────────────────────────────┴──────────────────────────────────────┘

Row 2: Model Performance
┌────────────────────────────┬──────────────────────────────────────┐
│  Token Usage by Model      │  Cost by Model                      │
│  [Bar chart]               │  [Bar chart, $]                     │
│  Stacked: prompt/completion│  Stacked by provider                │
└────────────────────────────┴──────────────────────────────────────┘

Row 3: Agent Flow
┌──────────────────────────────────────────────────────────────────┐
│  Agent Execution Flow (Sankey diagram)                           │
│  [User → Orchestrator → Code Agent → Tool → Response]           │
│  Width = request count per path                                  │
└──────────────────────────────────────────────────────────────────┘

Row 4: Agent Metrics Detail
┌─────────────┬─────────────┬─────────────┬─────────────┬─────────┐
│ Agent       │ Calls (24h) │ Avg Latency │ Success Rate│ Tokens  │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────┤
│ Code Review │ 1,234       │ 2.1s        │ 97.2%       │ 12.5M   │
│ Security    │ 567         │ 3.4s        │ 94.8%       │ 8.2M    │
│ Research    │ 2,890       │ 4.2s        │ 99.1%       │ 45.6M   │
│ Debug       │ 345         │ 1.8s        │ 88.3%       │ 3.4M    │
│ ...         │ ...         │ ...         │ ...         │ ...     │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────┘
```

### 3.3 Grafana Dashboard: Business / Cost

**Audience**: Product Managers / Business Owners
**Refresh**: 1h

```
Row 1: Usage Overview
┌────────────────────────────┬──────────────────────────────────────┐
│  Active Users (24h)        │  Total Requests (30d)               │
│  [Stat panel: 142]         │  [Stat panel: 45,678]               │
├────────────────────────────┼──────────────────────────────────────┤
│  Total Cost (30d)          │  Avg Cost per Request                │
│  [Stat panel: $234.50]     │  [Stat panel: $0.0051]              │
└────────────────────────────┴──────────────────────────────────────┘

Row 2: Cost Breakdown
┌────────────────────────────┬──────────────────────────────────────┐
│  Cost by Provider (30d)    │  Cost by Agent (30d)                │
│  [Pie chart]               │  [Bar chart]                        │
│  OpenAI: 45%               │  Research: 38%                      │
│  Anthropic: 30%            │  Code: 22%                          │
│  Ollama: 15%               │  Security: 18%                      │
│  Gemini: 10%               │  ...                                │
└────────────────────────────┴──────────────────────────────────────┘

Row 3: SLA Compliance
┌──────────────────────┬──────────────────────┬──────────────────────┐
│  API Latency SLA     │  Agent Success SLA   │  Uptime SLA          │
│  Target: <500ms P95  │  Target: >95%        │  Target: 99.9%       │
│  Current: 450ms ✅   │  Current: 96.2% ✅   │  Current: 99.95% ✅ │
│  30d: 98.5%          │  30d: 97.1%          │  30d: 99.97%         │
└──────────────────────┴──────────────────────┴──────────────────────┘
```

## 4. In-App Dashboard (React)

### 4.1 Component Tree

```
<Dashboard>
├── <StatusBar>
│   ├── <ServiceIndicator name="API" status="ok" />
│   ├── <ServiceIndicator name="Database" status="ok" />
│   ├── <ServiceIndicator name="AI Provider" status="degraded" />
│   └── <ServiceIndicator name="Agents" status="ok" />
├── <MetricsRow>
│   ├── <MetricCard title="Requests" value="1,234" change="+12%" />
│   ├── <MetricCard title="Latency" value="120ms" change="-5%" />
│   ├── <MetricCard title="Errors" value="0.5%" change="+0.1%" />
│   └── <MetricCard title="Cost Today" value="$12.34" />
├── <TimeSeriesChart title="API Requests" data={...} />
├── <TimeSeriesChart title="Token Usage" data={...} />
├── <AgentGrid>
│   └── {agents.map(a => <AgentCard agent={a} />)}
└── <ErrorFeed errors={errors} limit={10} />
```

### 4.2 API Endpoints

```
GET  /api/v2/monitoring/summary          — Dashboard summary (all metrics)
GET  /api/v2/monitoring/status           — Service status indicators
GET  /api/v2/monitoring/metrics          — Raw metrics data
GET  /api/v2/monitoring/agents           — Agent status + metrics
GET  /api/v2/monitoring/models           — Model/provider metrics
GET  /api/v2/monitoring/errors           — Recent errors
GET  /api/v2/monitoring/history?period=24h  — Historical metrics
```

## 5. Widget Library

### 5.1 Available Widgets

| Widget | Type | Data Source | Update |
|--------|------|-------------|--------|
| `StatusIndicator` | Single value | `/monitoring/status` | 10s |
| `MetricCard` | Single value + change | `/monitoring/summary` | 30s |
| `TimeSeriesChart` | Line chart | `/monitoring/history` | 30s |
| `BarChart` | Bar chart | `/monitoring/metrics` | 60s |
| `PieChart` | Pie/Doughnut | `/monitoring/metrics` | 60s |
| `StatTable` | Table | `/monitoring/agents` | 30s |
| `Heatmap` | Calendar heatmap | `/monitoring/history` | 5m |
| `ErrorFeed` | Scrollable list | `/monitoring/errors` | 10s |
| `SankeyFlow` | Flow diagram | `/monitoring/agents` | 60s |
| `AgentCard` | Card with status | `/monitoring/agents` | 15s |

### 5.2 Custom Widget Registration

```python
# Plugins can register custom widgets
from aida.monitoring.widgets import register_widget

@register_widget(
    name="custom_metric",
    description="My custom metric",
    data_source="/api/v2/monitoring/custom",
    refresh_interval=30,
)
class CustomWidget:
    def render(self, data):
        return {"value": data["value"], "unit": data["unit"]}
```

## 6. Panel Organization

```
Grafana Folder: AIDA
├── AIDA - Overview              (SRE/DevOps)
├── AIDA - AI & Agents           (ML team)
├── AIDA - Business & Cost       (Product)
├── AIDA - Infrastructure        (Kubernetes/Docker)
├── AIDA - Database              (DBA)
├── AIDA - Security              (Security team)
└── AIDA - Alerts                (All)

Grafana Folder: AIDA / Drill-Down
├── AIDA - Agent: Code Review    (Agent detail)
├── AIDA - Agent: Security       (Agent detail)
├── AIDA - Model: GPT-4o         (Model detail)
├── AIDA - Model: Claude-3       (Model detail)
├── AIDA - Endpoint: /chat       (Endpoint detail)
└── AIDA - Provider: OpenAI      (Provider detail)
```

## 7. Time Range Presets

| Preset | Use Case | Granularity |
|--------|----------|-------------|
| Last 15m | Real-time debugging | 15s |
| Last 1h | Recent incident analysis | 1m |
| Last 6h | Shift handover | 5m |
| Last 24h | Daily standup | 15m |
| Last 7d | Weekly review | 1h |
| Last 30d | Monthly business review | 1h |
| Last 90d | Quarterly trends | 1d |
| Custom | Ad-hoc analysis | Auto |

## 8. Dashboard Security

| Dashboard | Access | Actions |
|-----------|--------|---------|
| Overview | All authenticated users | View only |
| AI & Agents | Developers + ML team | View + template variables |
| Business & Cost | Admin + Finance | View + cost data |
| Infrastructure | SRE + DevOps | View + edit alerts |
| Security | Security team only | View + export |
| Drill-down | Team-specific | View only |

## 9. Implementation Priority

| Phase | Component | Priority | Effort |
|-------|-----------|----------|--------|
| P0 | `/monitoring/summary` API endpoint | CRITICAL | Small |
| P0 | `/monitoring/status` API endpoint | CRITICAL | Small |
| P0 | `/monitoring/agents` API endpoint | CRITICAL | Small |
| P1 | Grafana + Prometheus Docker Compose | HIGH | Medium |
| P1 | Overview dashboard (Grafana) | HIGH | Medium |
| P1 | AI & Agents dashboard (Grafana) | HIGH | Medium |
| P1 | Prometheus metrics endpoint | HIGH | Small |
| P2 | In-app React dashboard (basic) | MEDIUM | Large |
| P2 | Business & Cost dashboard | MEDIUM | Medium |
| P2 | Drill-down dashboards | MEDIUM | Medium |
| P3 | Infrastructure dashboard | LOW | Medium |
| P3 | Custom widget system | LOW | Large |
| P3 | Dashboard export/sharing | LOW | Small |
