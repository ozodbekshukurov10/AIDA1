# AIDA Repository Analyzer

**Document:** Book 2, Chapter 10 - Repository Analyzer
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Vision

The Repository Analyzer is the **foundation layer** of Code Intelligence. It automatically discovers project type, framework, languages, folder structure, architecture style, dependencies, build system, configuration files, and entrypoints.

---

## 2. Analysis Pipeline

```
Repository Path
       |
       v
+---------------------+
| File System Scanner |
| - Walk directory    |
| - Collect file info |
+----------+----------+
           |
           v
+---------------------+
| Language Detector   |
| - File extensions   |
| - Content analysis  |
+----------+----------+
           |
           v
+---------------------+
| Framework Detector  |
| - Config files      |
| - Dependencies      |
+----------+----------+
           |
           v
+---------------------+
| Structure Analyzer  |
| - Folder hierarchy  |
| - Module mapping    |
+----------+----------+
           |
           v
+---------------------+
| Architecture Detect |
| - Pattern matching  |
| - Style classification|
+----------+----------+
           |
           v
Repository Profile
```

---

## 3. Detection Dimensions

### 3.1 Project Type

| Type | Detection Signals |
|------|-------------------|
| Web Application | index.html, package.json, requirements.txt |
| API Service | openapi.yaml, api/ directory, route definitions |
| Library | setup.py, pyproject.toml, lib/ directory |
| CLI Tool | argparse/click, bin/ directory, entry_points |
| Mobile App | AndroidManifest.xml, Info.plist, pubspec.yaml |
| Desktop App | electron-builder, main window, tray icon |
| Data Pipeline | airflow, dag, pipeline, etl |
| ML Project | notebook, model, training, dataset |

### 3.2 Framework Detection

| Language | Frameworks | Detection Signals |
|----------|------------|-------------------|
| Python | Django, Flask, FastAPI | settings.py, app.py, main.py |
| JavaScript | React, Vue, Angular, Express | package.json dependencies |
| TypeScript | Next.js, NestJS, Angular | tsconfig.json + framework |
| Go | Gin, Echo, Fiber | go.mod dependencies |
| Rust | Actix, Rocket, Axum | Cargo.toml dependencies |
| Java | Spring, Jakarta | pom.xml, build.gradle |

### 3.3 Folder Structure Analysis

```
Structure Patterns:
- src/           -> Source code
- tests/         -> Test files
- docs/          -> Documentation
- config/        -> Configuration
- scripts/       -> Build/deploy scripts
- lib/           -> Libraries
- bin/           -> Executables
- data/          -> Data files
- assets/        -> Static assets
- migrations/    -> Database migrations
```

---

## 4. Repository Profile

```
RepositoryProfile:
  path: string
  name: string
  description: string
  project_type: string
  framework: string
  languages: list[Language]
  folder_structure: FolderTree
  architecture_style: string
  dependencies: list[Dependency]
  build_system: string
  config_files: list[string]
  entrypoints: list[string]
  total_files: int
  total_lines: int
  last_modified: datetime
```

---

## 5. Configuration

```yaml
repository_analyzer:
  enabled: true
  auto_analyze: true
  scan_depth: 5
  ignore_patterns:
    - node_modules
    - .git
    - __pycache__
    - dist
    - build
    - .venv
  index_on_open: true
```
