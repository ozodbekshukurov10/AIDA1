# AIDA — AI & Agent Logging System

## 1. Design Philosophy

AI logging — AIDA'ning eng muhim log kategoriyasi. Har bir LLM chaqiruvi, agent faoliyati va tool executioni batafsil, strukturaviy tarzda qayd qilinadi. Bu ma'lumotlar:

- **Debugging** — model noto'g'ri javob qaytarganda sababni aniqlash
- **Monitoring** — token ishlatish, latency, xatoliklar statistikasi
- **Cost tracking** — har bir provider va model uchun xarajat hisobi
- **Audit** — AI qanday qaror qabul qilganini kuzatish
- **Optimization** — qaysi model tezroq/arzonroq ekanligini aniqlash

**Current State**: LLM request/response logging deyarli yo'q. `webapp/llm/gateway.py` faqat provider switching ni loglaydi. Agentlar faqat in-memory metrics yuritadi. Tool executioni hech qanday log yozmaydi.

## 2. AI Log Categories

### 2.1 LLM Provider Events

| Event | Description | Logged Fields |
|-------|-------------|---------------|
| `ai.llm.request.started` | Provider ga request yuborildi | prompt, model, provider, temperature, max_tokens |
| `ai.llm.request.completed` | Javob qaytdi | response, tokens_used, latency_ms, finish_reason |
| `ai.llm.request.failed` | Xato yuz berdi | error_type, error_message, retry_count |
| `ai.llm.request.fallback` | Boshqa provider ga o'tildi | from_provider, to_provider, reason |
| `ai.llm.stream.started` | Streaming boshlandi | session_id, model |
| `ai.llm.stream.chunk` | Har bir chunk | chunk_index, tokens, latency_ms |
| `ai.llm.stream.completed` | Streaming tugadi | total_chunks, total_tokens, total_latency |
| `ai.llm.stream.failed` | Streaming xatosi | error, chunks_received |

```json
{
  "event": "ai.llm.request.completed",
  "timestamp": "2026-07-03T12:00:00.123456+00:00",
  "logger": "aida.ai.providers.openai",
  "context": {
    "request_id": "req_abc123",
    "session_id": "sess_def456",
    "user_id": "user_789",
    "agent_id": "agent_code_review"
  },
  "metadata": {
    "provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.7,
    "max_tokens": 4096,
    "finish_reason": "stop",
    "prompt_tokens": 450,
    "completion_tokens": 120,
    "total_tokens": 570,
    "estimated_cost_usd": 0.00855,
    "response_time_ms": 1234.56,
    "ttft_ms": 320.5,
    "prompt_preview": "Review the following code for security issues...",
    "response_preview": "Found 2 potential vulnerabilities...",
    "tool_calls": ["search_web", "read_file"]
  },
  "system_state": {
    "context_size_tokens": 8500,
    "memory_used_mb": 128,
    "gpu_memory_mb": 4096
  }
}
```

### 2.2 Agent Events

| Event | Description | Logged Fields |
|-------|-------------|---------------|
| `ai.agent.started` | Agent ishga tushdi | agent_id, agent_type, task, input |
| `ai.agent.completed` | Agent tugadi | agent_id, result, duration, tools_used |
| `ai.agent.failed` | Agent xatosi | agent_id, error, retry_count, recovery |
| `ai.agent.task.assigned` | Vazifa topshirildi | task_id, from_agent, to_agent, task_type |
| `ai.agent.task.completed` | Vazifa bajarildi | task_id, result, dependencies |
| `ai.agent.task.failed` | Vazifa bajarilmadi | task_id, reason, retry_count |
| `ai.agent.plan.created` | Reja tuzildi | plan_id, steps, reasoning |
| `ai.agent.plan.updated` | Reja o'zgartirildi | plan_id, changes, reason |
| `ai.agent.decision.made` | Qaror qabul qilindi | decision, alternatives, reasoning |
| `ai.agent.memory.accessed` | Xotiraga murojaat | memory_type, key, relevance |

```json
{
  "event": "ai.agent.completed",
  "timestamp": "2026-07-03T12:00:00.123456+00:00",
  "logger": "aida.agent.code_review",
  "context": {
    "request_id": "req_abc123",
    "session_id": "sess_def456",
    "user_id": "user_789"
  },
  "metadata": {
    "agent_id": "agent_code_review",
    "agent_type": "code_review",
    "task": "Review PR #42 for security vulnerabilities",
    "result_summary": "Found 3 issues: 1 critical, 2 medium",
    "duration_seconds": 45.2,
    "reasoning_time_seconds": 32.1,
    "tools_used": [
      {"tool": "read_file", "calls": 5, "total_duration": 2.1},
      {"tool": "search_code", "calls": 3, "total_duration": 1.5}
    ],
    "llm_calls": 4,
    "total_tokens": 12500,
    "estimated_cost_usd": 0.125,
    "retry_count": 0,
    "status": "success"
  }
}
```

### 2.3 Tool Events

| Event | Description | Logged Fields |
|-------|-------------|---------------|
| `ai.tool.execution.started` | Tool chaqirildi | tool_name, input_params |
| `ai.tool.execution.completed` | Tool tugadi | tool_name, output_summary, duration |
| `ai.tool.execution.failed` | Tool xatosi | tool_name, error, input |
| `ai.tool.execution.timeout` | Tool timeout | tool_name, timeout_seconds |
| `ai.tool.registered` | Tool ro'yxatdan o'tdi | tool_name, version, permissions |
| `ai.tool.removed` | Tool o'chirildi | tool_name, reason |

```json
{
  "event": "ai.tool.execution.completed",
  "timestamp": "2026-07-03T12:00:00.123456+00:00",
  "logger": "aida.tool.search_web",
  "context": {
    "request_id": "req_abc123",
    "agent_id": "agent_research",
    "task_id": "task_def456"
  },
  "metadata": {
    "tool_name": "search_web",
    "tool_version": "1.2.0",
    "input": {
      "query": "latest Python security vulnerabilities 2026",
      "max_results": 5,
      "source": "web"
    },
    "output_summary": "Returned 5 results. Top result: CVE-2026-1234",
    "output_size_bytes": 12450,
    "execution_time_ms": 2340.5,
    "status": "success",
    "error": null,
    "retry_count": 0
  }
}
```

### 2.4 Workflow Events

| Event | Description | Logged Fields |
|-------|-------------|---------------|
| `ai.workflow.started` | Workflow boshlandi | workflow_id, workflow_type, input |
| `ai.workflow.step.started` | Step boshlandi | step_id, step_type, agent_assigned |
| `ai.workflow.step.completed` | Step tugadi | step_id, result, duration |
| `ai.workflow.step.failed` | Step xatosi | step_id, error, retry_count |
| `ai.workflow.completed` | Workflow tugadi | workflow_id, result, total_duration |
| `ai.workflow.failed` | Workflow xatosi | workflow_id, error, failed_step |
| `ai.workflow.transition` | Holat o'zgarishi | from_state, to_state, trigger |

## 3. Prompt Logging

### 3.1 Logged Prompt Structure

```json
{
  "event": "ai.llm.request.started",
  "prompt": {
    "system": "You are a code review assistant...",
    "messages": [
      {"role": "user", "content": "Review this code:\n```python\ndef foo():\n    ...```"}
    ],
    "tools": [
      {"name": "search_web", "description": "Search the internet..."}
    ],
    "tool_choice": "auto"
  },
  "metadata": {
    "prompt_tokens": 450,
    "context_window_used_percent": 35.0,
    "messages_count": 3,
    "tool_definitions_count": 5
  }
}
```

### 3.2 Response Structure

```json
{
  "event": "ai.llm.request.completed",
  "response": {
    "content": "Found 2 issues:\n1. SQL injection in line 42...",
    "finish_reason": "tool_calls",
    "tool_calls": [
      {
        "id": "call_abc123",
        "function": "search_web",
        "arguments": {"query": "CVE-2024-1234 fix"}
      }
    ],
    "usage": {
      "prompt_tokens": 450,
      "completion_tokens": 120,
      "total_tokens": 570
    }
  }
}
```

### 3.3 Privacy Rules for Prompts

| Content | Logged? | Notes |
|---------|---------|-------|
| System prompt | ✅ Yes | Truncated to 500 chars |
| User message | ✅ Yes | Truncated, PII redacted |
| Assistant response | ✅ Yes | Truncated, PII redacted |
| Tool definitions | ✅ Yes | Names only, descriptions truncated |
| Tool call arguments | ✅ Yes | Redacted if contain secrets |
| API keys in prompt | ❌ Never | Auto-redacted by SecretRedactor |
| Passwords in content | ❌ Never | Auto-redacted by SecretRedactor |
| File contents | ✅ Partial | First 200 chars only |
| Code snippets | ✅ Yes | Full code logged (for debugging) |

## 4. Token Usage Tracking

### 4.1 Per-Request Token Log

```json
{
  "event": "ai.usage.tokens",
  "timestamp": "2026-07-03T12:00:00.123456+00:00",
  "provider": "openai",
  "model": "gpt-4o",
  "prompt_tokens": 450,
  "completion_tokens": 120,
  "total_tokens": 570,
  "cached_tokens": 0,
  "reasoning_tokens": 0,
  "estimated_cost_usd": 0.00855,
  "user_id": "user_789",
  "agent_id": "agent_code_review",
  "session_id": "sess_def456"
}
```

### 4.2 Cost Calculation

```python
# Standard pricing (configurable via config)
TOKEN_COSTS = {
    "gpt-4o": {
        "input": 0.00001,    # $0.01 per 1K input tokens
        "output": 0.00003,   # $0.03 per 1K output tokens
    },
    "claude-3-opus": {
        "input": 0.000015,
        "output": 0.000075,
    },
    # ...
}
```

### 4.3 Token Usage Summary (Dashboard)

```bash
aida ai usage --period 24h --group-by model
aida ai usage --period 7d --group-by user
aida ai usage --period 30d --group-by agent
```

## 5. Performance Metrics

### 5.1 Per-Operation Timing

```json
{
  "event": "ai.performance",
  "timestamp": "2026-07-03T12:00:00.123456+00:00",
  "metrics": {
    "ttft_ms": 320.5,
    "response_time_ms": 1234.56,
    "reasoning_time_ms": 890.2,
    "tool_execution_time_ms": 2340.5,
    "total_operation_time_ms": 4567.8,
    "context_loading_ms": 150.2,
    "memory_retrieval_ms": 45.3,
    "embedding_time_ms": 12.4
  },
  "system": {
    "cpu_percent": 45.2,
    "ram_mb": 256.0,
    "gpu_percent": 78.0,
    "gpu_memory_mb": 2048.0
  }
}
```

### 5.2 Performance by Component

```
LLM Call Breakdown:
├── Network latency:    120ms
├── Queue wait:          50ms
├── Tokenization:        15ms
├── Inference:          890ms
├── Response parsing:    20ms
└── Total:            1,095ms

Agent Breakdown:
├── Task analysis:      200ms
├── Tool selection:     150ms
├── Tool execution:   2,340ms
├── Response synthesis: 500ms
└── Total:            3,190ms
```

## 6. Log Storage

### 6.1 File Structure

```
logs/ai/
├── llm.2026-07-03.jsonl           # LLM requests/responses
├── agent.2026-07-03.jsonl         # Agent lifecycle
├── tool.2026-07-03.jsonl          # Tool executions
├── workflow.2026-07-03.jsonl      # Workflow events
├── tokens.2026-07-03.jsonl        # Token usage (for billing)
├── prompts/                       # Full prompt storage
│   └── 2026/07/03/
│       ├── prompt_req_abc123.json
│       └── prompt_req_def456.json
└── archive/                       # Compressed archives
    └── ai.2026-06.jsonl.gz
```

### 6.2 Retention

| Log Type | Hot | Warm | Archive |
|----------|-----|------|---------|
| LLM requests | 7 days | 30 days | 90 days |
| Agent events | 30 days | 90 days | 1 year |
| Tool executions | 7 days | 30 days | 90 days |
| Token usage | 90 days | 1 year | 3 years |
| Full prompts | 1 day | 7 days | 30 days |

## 7. Monitoring & Alerting

### 7.1 Key Metrics

| Metric | Warning | Critical | Description |
|--------|---------|----------|-------------|
| `llm.error_rate` | > 5% | > 15% | LLM call failure rate |
| `llm.latency_p99` | > 5s | > 15s | P99 response time |
| `llm.token_usage` | > 80% daily quota | > 95% | Token consumption |
| `llm.cost_daily` | > $100 | > $500 | Daily cost |
| `agent.error_rate` | > 10% | > 25% | Agent failure rate |
| `agent.duration_p99` | > 60s | > 180s | Agent execution time |
| `tool.error_rate` | > 5% | > 15% | Tool failure rate |
| `tool.latency_p99` | > 10s | > 30s | Tool execution time |

### 7.2 Alert Channels

| Severity | Channel | Examples |
|----------|---------|----------|
| WARNING | Slack #ai-monitoring | Elevated error rate, high latency |
| CRITICAL | PagerDuty + Slack | Provider down, cost spike, auth failures |

## 8. Implementation Priority

| Phase | Component | Priority | Effort |
|-------|-----------|----------|--------|
| P0 | LLM request/response logging in providers | CRITICAL | Small |
| P0 | Token usage tracking | CRITICAL | Small |
| P0 | Agent lifecycle logging (start/completed/failed) | CRITICAL | Small |
| P1 | Tool execution logging | HIGH | Small |
| P1 | Prompt truncation + PII redaction | HIGH | Medium |
| P1 | Execution time tracking (ttft, response, tool) | HIGH | Small |
| P2 | Cost tracking & estimation | MEDIUM | Medium |
| P2 | Workflow logging | MEDIUM | Medium |
| P2 | Token usage per-user/per-agent aggregation | MEDIUM | Medium |
| P3 | Full prompt archiving | LOW | Medium |
| P3 | Performance dashboards | LOW | Large |
