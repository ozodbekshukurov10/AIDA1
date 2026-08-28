# AIDA Tool Discovery

**Document:** Book 2, Chapter 9 - Tool Discovery
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

Tool Discovery automatically finds and registers tools from multiple sources: filesystem scans, plugin registries, MCP servers, API catalogs, Docker registries, and remote endpoints.

---

## 2. Discovery Sources

| Source | Method | Frequency | Reliability |
|--------|--------|-----------|-------------|
| Filesystem Scan | Directory walk | On startup + periodic | High |
| Plugin Scan | Plugin registry query | On startup | High |
| MCP Discovery | MCP server handshake | On connect | High |
| API Discovery | OpenAPI/Swagger parse | On connect | Medium |
| Docker Discovery | Docker API query | Periodic | Medium |
| Remote Discovery | Registry endpoint | Periodic | Low |

---

## 3. Discovery Pipeline

### 3.1 Flow

```
Discovery Trigger
       |
       v
+---------------------+
| Source Scanner      |
| - Scan all sources  |
| - Collect raw tools |
+----------+----------+
           |
           v
+---------------------+
| Tool Parser         |
| - Parse descriptors |
| - Extract metadata  |
+----------+----------+
           |
           v
+---------------------+
| Tool Validator      |
| - Validate schemas  |
| - Check compat      |
+----------+----------+
           |
           v
+---------------------+
| Tool Registrar      |
| - Register in       |
|   Tool Registry     |
+----------+----------+
           |
           v
Discovery Complete
```

---

## 4. Discovery Methods

### 4.1 Filesystem Scan

```
Scan Directories:
- /tools/
- /plugins/tools/
- ~/.aida/tools/

File Patterns:
- tool.json (descriptor)
- tool.yaml (descriptor)
- *.tool.py (Python tool)
- *.tool.js (Node tool)

Process:
1. Walk directories recursively
2. Find tool descriptor files
3. Parse descriptor
4. Validate format
5. Register tool
```

### 4.2 MCP Discovery

```
1. Connect to MCP server
2. Call initialize handshake
3. List available tools
4. For each tool:
   a. Get tool descriptor
   b. Convert to AIDA format
   c. Register in registry
5. Monitor MCP server health
```

### 4.3 API Discovery

```
1. Fetch OpenAPI/Swagger spec
2. Parse endpoints
3. For each endpoint:
   a. Create tool descriptor
   b. Map parameters
   c. Map response schema
   d. Register as REST tool
```

---

## 5. Configuration

```yaml
tool_discovery:
  enabled: true
  auto_discover: true
  scan_on_startup: true
  periodic_scan: true
  scan_interval: 300
  
  sources:
    filesystem:
      enabled: true
      paths: ["/tools/", "~/.aida/tools/"]
    plugin:
      enabled: true
    mcp:
      enabled: true
      servers: []
    api:
      enabled: true
    docker:
      enabled: false
    remote:
      enabled: false
      registries: []
```
