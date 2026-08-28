# AIDA Event Catalog

**Document:** Book 2, Chapter 4 — Event Catalog
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The Event Catalog is a comprehensive registry of all events in the AIDA system. It defines event types, schemas, topics, producers, consumers, and routing rules.

---

## 2. Event Categories

| Category | Description | Count |
|----------|-------------|-------|
| System | System lifecycle events | 8 |
| User | User interaction events | 6 |
| AI | AI processing events | 8 |
| Task | Task management events | 10 |
| Agent | Agent lifecycle events | 8 |
| Workflow | Workflow orchestration events | 8 |
| Memory | Memory management events | 6 |
| Knowledge | Knowledge base events | 6 |
| Plugin | Plugin lifecycle events | 8 |
| Security | Security events | 8 |
| Repository | Repository events | 6 |
| Git | Git operation events | 8 |
| Database | Database events | 6 |
| API | API events | 6 |
| Monitoring | Monitoring events | 6 |
| **Total** | | **106** |

---

## 3. System Events

| Event Type | Topic | Priority | Description |
|------------|-------|----------|-------------|
| `system.startup` | `system.lifecycle` | 90 | System starting |
| `system.shutdown` | `system.lifecycle` | 100 | System shutting down |
| `system.health` | `system.health` | 50 | Health check result |
| `system.config.changed` | `system.config` | 60 | Configuration changed |
| `system.error` | `system.error` | 80 | System error occurred |
| `system.warning` | `system.warning` | 60 | System warning |
| `system.metrics` | `system.metrics` | 30 | System metrics update |
| `system.backup` | `system.backup` | 40 | Backup event |

### 3.1 System Event Schema

```json
{
  "event_type": "system.startup",
  "topic": "system.lifecycle",
  "priority": 90,
  "payload": {
    "version": "1.0.0",
    "environment": "production",
    "node_id": "node-1",
    "startup_time": "2026-07-04T01:00:00Z",
    "modules_loaded": ["ai_kernel", "task_manager", "event_bus"],
    "config_version": "abc123"
  }
}
```

---

## 4. User Events

| Event Type | Topic | Priority | Description |
|------------|-------|----------|-------------|
| `user.connected` | `user.session` | 50 | User connected |
| `user.disconnected` | `user.session` | 50 | User disconnected |
| `user.message.sent` | `user.message` | 60 | User sent message |
| `user.message.received` | `user.message` | 60 | User message received |
| `user.feedback.submitted` | `user.feedback` | 50 | User submitted feedback |
| `user.settings.changed` | `user.settings` | 40 | User settings changed |

### 4.1 User Event Schema

```json
{
  "event_type": "user.message.sent",
  "topic": "user.message",
  "priority": 60,
  "user_id": "uuid",
  "session_id": "uuid",
  "payload": {
    "message_id": "uuid",
    "content": "Hello, help me with code",
    "message_type": "text",
    "language": "uz"
  }
}
```

---

## 5. AI Events

| Event Type | Topic | Priority | Description |
|------------|-------|----------|-------------|
| `ai.request.received` | `ai.request` | 70 | AI request received |
| `ai.request.processing` | `ai.request` | 60 | AI request processing |
| `ai.response.generated` | `ai.response` | 70 | AI response generated |
| `ai.token.generated` | `ai.token` | 50 | AI token generated (streaming) |
| `ai.model.selected` | `ai.model` | 50 | AI model selected |
| `ai.model.switched` | `ai.model` | 60 | AI model switched |
| `ai.error.occurred` | `ai.error` | 80 | AI error occurred |
| `ai.context.loaded` | `ai.context` | 40 | AI context loaded |

### 5.1 AI Event Schema

```json
{
  "event_type": "ai.response.generated",
  "topic": "ai.response",
  "priority": 70,
  "user_id": "uuid",
  "session_id": "uuid",
  "payload": {
    "request_id": "uuid",
    "response_id": "uuid",
    "model": "pro",
    "tokens_used": 150,
    "response_time_ms": 1200,
    "content_preview": "Here is the code..."
  }
}
```

---

## 6. Task Events

| Event Type | Topic | Priority | Description |
|------------|-------|----------|-------------|
| `task.created` | `task.lifecycle` | 60 | Task created |
| `task.started` | `task.lifecycle` | 60 | Task started |
| `task.progress` | `task.lifecycle` | 40 | Task progress update |
| `task.completed` | `task.lifecycle` | 70 | Task completed |
| `task.failed` | `task.lifecycle` | 80 | Task failed |
| `task.cancelled` | `task.lifecycle` | 60 | Task cancelled |
| `task.retrying` | `task.lifecycle` | 50 | Task retrying |
| `task.checkpoint` | `task.checkpoint` | 40 | Task checkpoint saved |
| `task.assigned` | `task.assignment` | 50 | Task assigned to agent |
| `task.unassigned` | `task.assignment` | 50 | Task unassigned |

### 6.1 Task Event Schema

```json
{
  "event_type": "task.completed",
  "topic": "task.lifecycle",
  "priority": 70,
  "task_id": "uuid",
  "user_id": "uuid",
  "payload": {
    "task_type": "coding",
    "agent_id": "code_agent",
    "model": "pro",
    "duration_ms": 45000,
    "result_summary": "Created user authentication module",
    "files_created": ["auth.py", "auth_test.py"],
    "files_modified": ["settings.py"]
  }
}
```

---

## 7. Agent Events

| Event Type | Topic | Priority | Description |
|------------|-------|----------|-------------|
| `agent.started` | `agent.lifecycle` | 50 | Agent started |
| `agent.stopped` | `agent.lifecycle` | 50 | Agent stopped |
| `agent.assigned` | `agent.task` | 60 | Agent assigned to task |
| `agent.completed` | `agent.task` | 70 | Agent completed task |
| `agent.failed` | `agent.task` | 80 | Agent failed task |
| `agent.health` | `agent.health` | 50 | Agent health check |
| `agent.metrics` | `agent.metrics` | 30 | Agent metrics update |
| `agent.error` | `agent.error` | 80 | Agent error occurred |

---

## 8. Workflow Events

| Event Type | Topic | Priority | Description |
|------------|-------|----------|-------------|
| `workflow.created` | `workflow.lifecycle` | 60 | Workflow created |
| `workflow.started` | `workflow.lifecycle` | 70 | Workflow started |
| `workflow.step.started` | `workflow.step` | 50 | Workflow step started |
| `workflow.step.completed` | `workflow.step` | 60 | Workflow step completed |
| `workflow.step.failed` | `workflow.step` | 80 | Workflow step failed |
| `workflow.completed` | `workflow.lifecycle` | 70 | Workflow completed |
| `workflow.failed` | `workflow.lifecycle` | 80 | Workflow failed |
| `workflow.paused` | `workflow.lifecycle` | 50 | Workflow paused |

---

## 9. Memory Events

| Event Type | Topic | Priority | Description |
|------------|-------|----------|-------------|
| `memory.stored` | `memory.write` | 40 | Memory stored |
| `memory.retrieved` | `memory.read` | 30 | Memory retrieved |
| `memory.updated` | `memory.write` | 40 | Memory updated |
| `memory.deleted` | `memory.write` | 40 | Memory deleted |
| `memory.expired` | `memory.maintenance` | 30 | Memory expired |
| `memory.compacted` | `memory.maintenance` | 30 | Memory compacted |

---

## 10. Knowledge Events

| Event Type | Topic | Priority | Description |
|------------|-------|----------|-------------|
| `knowledge.document.added` | `knowledge.write` | 50 | Document added |
| `knowledge.document.updated` | `knowledge.write` | 50 | Document updated |
| `knowledge.document.deleted` | `knowledge.write` | 50 | Document deleted |
| `knowledge.index.updated` | `knowledge.index` | 40 | Index updated |
| `knowledge.search.executed` | `knowledge.search` | 30 | Search executed |
| `knowledge.search.completed` | `knowledge.search` | 30 | Search completed |

---

## 11. Plugin Events

| Event Type | Topic | Priority | Description |
|------------|-------|----------|-------------|
| `plugin.installed` | `plugin.lifecycle` | 60 | Plugin installed |
| `plugin.uninstalled` | `plugin.lifecycle` | 60 | Plugin uninstalled |
| `plugin.activated` | `plugin.lifecycle` | 50 | Plugin activated |
| `plugin.deactivated` | `plugin.lifecycle` | 50 | Plugin deactivated |
| `plugin.error` | `plugin.error` | 70 | Plugin error |
| `plugin.event.published` | `plugin.events` | 40 | Plugin published event |
| `plugin.config.changed` | `plugin.config` | 50 | Plugin config changed |
| `plugin.health` | `plugin.health` | 40 | Plugin health check |

---

## 12. Security Events

| Event Type | Topic | Priority | Description |
|------------|-------|----------|-------------|
| `security.login.success` | `security.auth` | 60 | Login successful |
| `security.login.failed` | `security.auth` | 80 | Login failed |
| `security.logout` | `security.auth` | 50 | User logged out |
| `security.token.expired` | `security.token` | 60 | Token expired |
| `security.token.refreshed` | `security.token` | 40 | Token refreshed |
| `security.permission.denied` | `security.auth` | 90 | Permission denied |
| `security.violation.detected` | `security.violation` | 100 | Security violation |
| `security.audit` | `security.audit` | 50 | Security audit event |

---

## 13. Repository Events

| Event Type | Topic | Priority | Description |
|------------|-------|----------|-------------|
| `repo.cloned` | `repo.lifecycle` | 50 | Repository cloned |
| `repo.updated` | `repo.lifecycle` | 50 | Repository updated |
| `repo.analyzed` | `repo.analysis` | 50 | Repository analyzed |
| `repo.file.changed` | `repo.file` | 50 | File changed |
| `repo.branch.created` | `repo.branch` | 50 | Branch created |
| `repo.branch.deleted` | `repo.branch` | 50 | Branch deleted |

---

## 14. Git Events

| Event Type | Topic | Priority | Description |
|------------|-------|----------|-------------|
| `git.commit.created` | `git.commit` | 50 | Commit created |
| `git.push.completed` | `git.push` | 60 | Push completed |
| `git.pull.completed` | `git.pull` | 50 | Pull completed |
| `git.merge.conflict` | `git.merge` | 70 | Merge conflict |
| `git.merge.completed` | `git.merge` | 50 | Merge completed |
| `git.branch.checkout` | `git.branch` | 40 | Branch checked out |
| `git.stash.created` | `git.stash` | 30 | Stash created |
| `git.tag.created` | `git.tag` | 40 | Tag created |

---

## 15. Database Events

| Event Type | Topic | Priority | Description |
|------------|-------|----------|-------------|
| `db.query.executed` | `db.query` | 30 | Query executed |
| `db.query.slow` | `db.query` | 60 | Slow query detected |
| `db.migration.started` | `db.migration` | 70 | Migration started |
| `db.migration.completed` | `db.migration` | 70 | Migration completed |
| `db.backup.completed` | `db.backup` | 50 | Backup completed |
| `db.error.occurred` | `db.error` | 80 | Database error |

---

## 16. API Events

| Event Type | Topic | Priority | Description |
|------------|-------|----------|-------------|
| `api.request.received` | `api.request` | 40 | API request received |
| `api.request.completed` | `api.request` | 40 | API request completed |
| `api.request.failed` | `api.request` | 60 | API request failed |
| `api.rate_limited` | `api.limit` | 60 | Rate limited |
| `api.quota.exceeded` | `api.limit` | 70 | Quota exceeded |
| `api.endpoint.added` | `api.config` | 40 | Endpoint added |

---

## 17. Monitoring Events

| Event Type | Topic | Priority | Description |
|------------|-------|----------|-------------|
| `monitor.metric.collected` | `monitor.metrics` | 20 | Metric collected |
| `monitor.alert.raised` | `monitor.alert` | 80 | Alert raised |
| `monitor.alert.resolved` | `monitor.alert` | 60 | Alert resolved |
| `monitor.health.check` | `monitor.health` | 30 | Health check |
| `monitor.log.created` | `monitor.log` | 20 | Log created |
| `monitor.trace.completed` | `monitor.trace` | 20 | Trace completed |

---

## 18. Configuration

```yaml
event_catalog:
  # Auto-discovery
  auto_discover: true
  discovery_interval: 300s
  
  # Schema validation
  schema_validation: true
  strict_mode: false
  
  # Event versioning
  versioning:
    enabled: true
    strategy: backward Compatible
    
  # Documentation
  auto_document: true
  export_format: openapi
```
