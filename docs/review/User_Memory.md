# AIDA User Memory

**Document:** Book 2, Chapter 6 — User Memory
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

User Memory stores user-specific knowledge including preferences, coding style, frameworks, languages, and frequently used tools. It enables personalized AI responses.

---

## 2. User Memory Structure

### 2.1 Memory Categories

| Category | Description | Examples |
|----------|-------------|----------|
| `preferences` | User preferences | Language, theme, output format |
| `coding_style` | Coding patterns | Indentation, naming, comments |
| `frameworks` | Preferred frameworks | Django, React, FastAPI |
| `languages` | Programming languages | Python, JavaScript, Go |
| `tools` | Frequently used tools | VS Code, Git, Docker |
| `pinned` | Pinned knowledge | Important notes, rules |
| `custom_rules` | Custom instructions | User-defined rules |

---

## 3. User Memory Data

### 3.1 User Preferences

```python
class UserPreferences:
    user_id: UUID
    
    # Language
    preferred_language: str  # uz, en, ru
    response_language: str
    
    # Output format
    output_format: str  # text, code, markdown
    
    # Detail level
    detail_level: str  # minimal, standard, detailed
    
    # Code style
    code_style: dict
    
    # Framework preferences
    preferred_frameworks: list[str]
    
    # Tool preferences
    preferred_tools: list[str]
```

### 3.2 Coding Style

```python
class CodingStyle:
    user_id: UUID
    
    # Indentation
    indent_style: str  # spaces, tabs
    indent_size: int
    
    # Naming
    naming_convention: str  # snake_case, camelCase
    
    # Comments
    comment_style: str  # inline, docstring
    
    # Imports
    import_style: str  # grouped, sorted
    
    # Custom rules
    custom_rules: list[str]
```

---

## 4. User Memory Management

### 4.1 Learning Process

```
User Interaction
    │
    ├── Detect Preferences
    │   ├── Analyze user messages
    │   ├── Detect coding patterns
    │   └── Identify tool usage
    │
    ├── Update Memory
    │   ├── Update preferences
    │   ├── Update coding style
    │   └── Update frequently used
    │
    └── Apply Preferences
        ├── Customize responses
        ├── Apply coding style
        └── Suggest relevant tools
```

---

## 5. Configuration

```yaml
user_memory:
  enabled: true
  
  # Learning
  learning:
    auto_learn: true
    learning_rate: 0.1
    
  # Categories
  categories:
    preferences: true
    coding_style: true
    frameworks: true
    languages: true
    tools: true
    pinned: true
    custom_rules: true
    
  # Retention
  retention:
    max_age: permanent
    max_size: unlimited
    
  # Privacy
  privacy:
    encrypt: true
    user_control: true
    export_enabled: true
    delete_enabled: true
```
