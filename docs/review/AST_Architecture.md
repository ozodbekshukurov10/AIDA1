# AIDA AST Architecture

**Document:** Book 2, Chapter 10 - AST Architecture
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The AST (Abstract Syntax Tree) Architecture parses every source file into a structured tree representation, enabling deep code understanding including scope, variables, methods, call graphs, inheritance, and composition relationships.

---

## 2. AST Pipeline

```
Source File
    |
    v
+-------------------+
| Lexer             |
| - Tokenize source |
+---------+---------+
          |
          v
+-------------------+
| Parser            |
| - Build AST tree  |
+---------+---------+
          |
          v
+-------------------+
| Scope Resolver    |
| - Resolve scopes  |
| - Link variables  |
+---------+---------+
          |
          v
+-------------------+
| Type Resolver     |
| - Resolve types   |
| - Check inference |
+---------+---------+
          |
          v
+-------------------+
| Call Graph Builder|
| - Build call graph|
| - Track calls     |
+---------+---------+
          |
          v
Enriched AST
```

---

## 3. AST Node Types

| Node Type | Description | Children |
|-----------|-------------|----------|
| Module | Top-level file | statements |
| ClassDef | Class definition | methods, attributes |
| FunctionDef | Function definition | params, body |
| Assignment | Variable assignment | target, value |
| Call | Function call | func, args |
| Import | Import statement | module, names |
| If | Conditional | test, body, orelse |
| For | Loop | target, iter, body |
| Return | Return statement | value |
| Expr | Expression | value |

---

## 4. Scope Analysis

```
Scope:
  scope_id: string
  parent_scope: string
  scope_type: string (module|class|function|block)
  variables: list[Variable]
  definitions: list[Definition]
  references: list[Reference]

Variable:
  name: string
  type: TypeInfo
  defined_at: Location
  assigned_at: list[Location]
  used_at: list[Location]
  is_parameter: boolean
  is_global: boolean
```

---

## 5. Call Graph

```
CallGraph:
  nodes: list[CallNode]
  edges: list[CallEdge]

CallNode:
  function_id: string
  location: Location
  callees: list[string]
  callers: list[string]

CallEdge:
  caller: string
  callee: string
  call_site: Location
  call_type: string (direct|indirect|dynamic)
```

---

## 6. Multi-Language AST Support

| Language | Parser | AST Format |
|----------|--------|------------|
| Python | ast module | Python AST |
| JavaScript | esprima/acorn | ESTree |
| TypeScript | typescript compiler | TS AST |
| Go | go/parser | Go AST |
| Rust | syn | Rust AST |
| Java | javaparser | Java AST |

---

## 7. Configuration

```yaml
ast_architecture:
  enabled: true
  parsers:
    python: ast
    javascript: acorn
    typescript: typescript
    go: go/parser
    rust: syn
    java: javaparser
  
  analysis:
    scope_resolution: true
    type_inference: true
    call_graph: true
    inheritance: true
    composition: true
```
