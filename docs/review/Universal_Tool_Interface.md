# AIDA Universal Tool Interface

**Document:** Book 2, Chapter 9 - Universal Tool Interface
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The Universal Tool Interface defines a **single standardized contract** that every tool must implement. This ensures all tools can be discovered, invoked, monitored, and managed uniformly regardless of their underlying technology.

---

## 2. Interface Definition

### 2.1 Tool Descriptor

```
ToolDescriptor:
  # Identity
  tool_id: string (unique)
  name: string
  description: string
  version: string (semver)
  category: ToolCategory
  
  # Capabilities
  capabilities: list[string]
  input_schema: JSONSchema
  output_schema: JSONSchema
  
  # Configuration
  permissions: list[Permission]
  timeout: int (seconds)
  retry_policy: RetryPolicy
  sandbox_required: boolean
  
  # Health
  health_status: HealthStatus
  last_health_check: datetime
  
  # Metadata
  author: string
  license: string
  tags: list[string]
  created_at: datetime
  updated_at: datetime
```

### 2.2 Tool Execution Request

```
ToolExecutionRequest:
  request_id: string
  tool_id: string
  agent_id: string
  parameters: dict
  context: ExecutionContext
  timeout: int (optional override)
  metadata: dict
```

### 2.3 Tool Execution Response

```
ToolExecutionResponse:
  request_id: string
  tool_id: string
  status: ExecutionStatus
  result: any
  error: ToolError (nullable)
  metrics: ExecutionMetrics
  artifacts: list[Artifact]
  timestamp: datetime
```

---

## 3. Execution Status

| Status | Description |
|--------|-------------|
| pending | Queued for execution |
| running | Currently executing |
| completed | Finished successfully |
| failed | Finished with error |
| timeout | Exceeded time limit |
| cancelled | Cancelled by user/system |
| retrying | Retrying after failure |

---

## 4. Execution Metrics

```
ExecutionMetrics:
  start_time: datetime
  end_time: datetime
  duration_ms: int
  tokens_used: int
  memory_used_mb: float
  cpu_used_percent: float
  network_bytes_in: int
  network_bytes_out: int
  retries: int
  cache_hit: boolean
```

---

## 5. Input/Output Schemas

### 5.1 JSON Schema Example

```
input_schema:
  type: object
  properties:
    command:
      type: string
      description: Git command to execute
      enum: [clone, pull, push, status, diff, log]
    repository:
      type: string
      description: Repository URL or path
    branch:
      type: string
      description: Branch name
      default: main
  required: [command, repository]

output_schema:
  type: object
  properties:
    success:
      type: boolean
    output:
      type: string
    exit_code:
      type: integer
    files_changed:
      type: array
      items:
        type: string
```

---

## 6. Retry Policy

```
RetryPolicy:
  max_retries: int (default: 2)
  retry_delay_ms: int (default: 1000)
  backoff_strategy: string (linear|exponential)
  backoff_multiplier: float (default: 2.0)
  max_delay_ms: int (default: 30000)
  retry_on: list[string] (timeout|error|rate_limit)
```

---

## 7. Configuration

```yaml
universal_tool_interface:
  version: "1.0"
  schema_validation: strict
  default_timeout: 60
  default_retries: 2
  max_parameters_size: 1MB
  max_result_size: 10MB
```
