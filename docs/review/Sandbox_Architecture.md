# AIDA Sandbox Architecture

**Document:** Book 2, Chapter 9 - Sandbox Architecture
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The Sandbox provides **isolation and resource limits** for tool execution. Dangerous tools run in sandboxed environments with filesystem isolation, memory limits, CPU limits, network policies, and execution timeouts.

---

## 2. Isolation Layers

| Layer | Description | Implementation |
|-------|-------------|----------------|
| Filesystem | Restricted file access | Chroot / Container |
| Memory | RAM limits | cgroups / Container |
| CPU | Processing limits | cgroups / Container |
| Network | Network policy | iptables / Container |
| Process | Process limits | PID namespace |
| Time | Execution timeout | Watchdog timer |

---

## 3. Sandbox Types

| Type | Isolation | Performance | Use Case |
|------|-----------|-------------|----------|
| None | No isolation | Fastest | Trusted local tools |
| Process | Process-level | Fast | CLI tools |
| Container | Full isolation | Medium | Untrusted tools |
| VM | Maximum isolation | Slow | Maximum security |

---

## 4. Resource Limits

```
SandboxLimits:
  max_memory_mb: int (default: 512)
  max_cpu_percent: int (default: 50)
  max_execution_time_s: int (default: 60)
  max_output_size_mb: int (default: 10)
  max_file_size_mb: int (default: 100)
  allowed_paths: list[string]
  blocked_paths: list[string]
  network_policy: NetworkPolicy
  environment_vars: dict
```

### 4.1 Network Policy

| Policy | Description |
|--------|-------------|
| deny_all | No network access |
| allow_list | Only specified hosts |
| deny_list | All except specified hosts |
| allow_all | Full network access |

---

## 5. Sandbox Lifecycle

```
1. Create    - Setup isolated environment
2. Configure - Apply resource limits
3. Execute   - Run tool in sandbox
4. Monitor   - Track resource usage
5. Enforce   - Kill if limits exceeded
6. Collect   - Gather results and logs
7. Cleanup   - Destroy sandbox
```

---

## 6. Configuration

```yaml
sandbox:
  enabled: true
  default_type: container
  
  limits:
    memory_mb: 512
    cpu_percent: 50
    execution_time_s: 60
    output_size_mb: 10
  
  network:
    default_policy: deny_all
    allow_list: []
  
  filesystem:
    read_only: ["/etc", "/usr"]
    read_write: ["/tmp", "/workspace"]
    blocked: ["/root", "/home"]
```
