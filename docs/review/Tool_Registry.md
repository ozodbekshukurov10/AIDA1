# AIDA Tool Registry

**Document:** Book 2, Chapter 9 - Tool Registry
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The Tool Registry is the **central catalog** of all available, installed, disabled, and remote tools. It supports dynamic registration, versioning, capability indexing, and health tracking.

---

## 2. Registry Structure

### 2.1 Storage Model

```
ToolRegistry:
  tools: Map<ToolId, ToolDescriptor>
  categories: Map<Category, List<ToolId>>
  capabilities: Map<Capability, List<ToolId>>
  versions: Map<ToolId, List<Version>>
  health: Map<ToolId, HealthStatus>
```

### 2.2 Registry Categories

| Category | Count | Description |
|----------|-------|-------------|
| installed | Dynamic | Locally installed tools |
| available | Dynamic | Discoverable but not installed |
| disabled | Manual | Disabled by admin |
| remote | Dynamic | Remote API tools |
| plugin | Dynamic | Plugin-provided tools |
| mcp | Dynamic | MCP server tools |

---

## 3. Registry Operations

### 3.1 Register

```
1. Receive tool descriptor
2. Validate descriptor format
3. Check for conflicts (ID uniqueness)
4. Validate input/output schemas
5. Check permissions
6. Store in registry
7. Index by category and capabilities
8. Run initial health check
9. Emit registration event
```

### 3.2 Unregister

```
1. Check tool not in active execution
2. Remove from all indexes
3. Remove health status
4. Archive version history
5. Emit unregistration event
```

### 3.3 Update

```
1. Load current version
2. Compare new vs current
3. Validate backward compatibility
4. Update descriptor
5. Update indexes
6. Store previous version in history
7. Emit update event
```

---

## 4. Lookup Methods

| Method | Input | Output | Use Case |
|--------|-------|--------|----------|
| GetById | tool_id | ToolDescriptor | Direct access |
| GetByName | name | ToolDescriptor | Human lookup |
| GetByCategory | category | List[ToolId] | Category browse |
| GetByCapability | capability | List[ToolId] | Task matching |
| Search | query | List[ToolId] | Free text search |
| GetHealthy | (none) | List[ToolId] | Available tools |

---

## 5. Version Management

```
VersionHistory:
  tool_id: string
  versions: list[Version]
  current: string
  latest: string
  deprecated: list[string]

Version:
  version: string (semver)
  descriptor: ToolDescriptor
  changelog: string
  released_at: datetime
  compatibility: list[string]
```

---

## 6. Configuration

```yaml
tool_registry:
  enabled: true
  backend: database
  max_tools: 500
  version_history: true
  auto_health_check: true
  health_check_interval: 60
  index_by:
    - category
    - capabilities
    - tags
```
