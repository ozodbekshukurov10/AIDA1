# AIDA Tool Chaining

**Document:** Book 2, Chapter 9 - Tool Chaining
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

Tool Chaining enables **sequential and parallel execution** of multiple tools, where the output of one tool becomes the input of the next. It supports complex workflows like Clone -> Analyze -> Build -> Test -> Deploy.

---

## 2. Chain Types

| Type | Description | Example |
|------|-------------|---------|
| Sequential | One after another | git clone -> analyze -> build |
| Parallel | Simultaneous execution | test frontend + test backend |
| Conditional | Based on results | if tests pass then deploy |
| Loop | Repeat until condition | retry until success |
| Pipeline | Data stream | extract -> transform -> load |

---

## 3. Chain Definition

### 3.1 Chain Structure

```
ToolChain:
  chain_id: string
  name: string
  description: string
  steps: list[ChainStep]
  on_failure: FailureStrategy
  timeout: int (total seconds)

ChainStep:
  step_id: string
  tool_id: string
  parameters: dict
  input_mapping: dict (step_output -> tool_input)
  output_key: string (result key for next step)
  condition: string (optional, for conditional)
  timeout: int (step timeout)
  retry: RetryPolicy
```

### 3.2 Example Chain

```
Chain: deploy_feature
Steps:
  1. git_clone -> repository_url
  2. code_analyze -> repository_path (from step 1)
  3. [parallel]
     3a. run_tests -> repository_path
     3b. security_scan -> repository_path
  4. docker_build -> repository_path (after 3a+3b)
  5. deploy -> image_name (from step 4)
  6. monitor -> deploy_url (from step 5)
```

---

## 4. Execution Engine

### 4.1 Sequential Execution

```
for step in chain.steps:
    input = resolve_input(step, previous_results)
    result = execute_tool(step.tool_id, input)
    if result.failed and chain.on_failure == "stop":
        return ChainResult(status="failed")
    previous_results[step.output_key] = result
return ChainResult(status="completed")
```

### 4.2 Parallel Execution

```
parallel_steps = get_parallel_steps(chain)
results = execute_all(parallel_steps, max_concurrent=5)
merge_results(results)
```

---

## 5. Data Flow

```
Step 1 Output: { "path": "/tmp/repo" }
         |
         v
Step 2 Input Mapping: { "repository_path": "$.step1.path" }
         |
         v
Step 2 Input: { "repository_path": "/tmp/repo" }
         |
         v
Step 2 Output: { "analysis": {...} }
```

---

## 6. Configuration

```yaml
tool_chaining:
  enabled: true
  max_steps: 20
  max_parallel: 5
  total_timeout: 600
  on_failure: stop
  data_format: json
```
