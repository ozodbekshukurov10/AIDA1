# AIDA Prompt Templates

**Document:** Book 2, Chapter 7 — Prompt Templates
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The Template System provides **reusable, versioned, dynamic prompt structures** that support conditional logic, nested composition, variable substitution, and model-specific variants.

---

## 2. Template Architecture

### 2.1 Template Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                    TEMPLATE REGISTRY                             │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Base       │  │   Task       │  │   Model      │          │
│  │  Templates   │  │  Templates   │  │  Variants    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                    TEMPLATE ENGINE                               │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Variable   │  │  Conditional │  │   Nested     │          │
│  │  Resolver    │→ │   Evaluator  │→ │   Assembler  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                    ASSEMBLED PROMPT                              │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Template Categories

| Category | Description | Count |
|----------|-------------|-------|
| `base` | Core templates for all tasks | 6 |
| `task` | Task-specific templates | 12 |
| `model` | Model-specific variants | 9 |
| `workflow` | Workflow templates | 5 |
| `composite` | Combined templates | 4 |

---

## 3. Template Types

### 3.1 Base Templates

#### 3.1.1 Chat Base Template

```yaml
name: chat_base
version: 1.0.0
type: base
components:
  system: |
    Siz AIDA AI yordamchisiz.
    {language_rule}
    {behavior_rules}
    {output_rules}
  context: |
    # Loyiha konteksti
    {project_context}
    
    # Xotira konteksti
    {memory_context}
  examples: |
    # Namunalar
    {examples}
  user: |
    # Foydalanuvchi so'rovi
    {user_request}
```

#### 3.1.2 Code Base Template

```yaml
name: code_base
version: 1.0.0
type: base
components:
  system: |
    Siz professional dasturchisiz.
    {language_rule}
    {coding_standards}
    {security_rules}
  context: |
    # Repozitoriya konteksti
    {repository_context}
    
    # Loyiha konteksti
    {project_context}
  code_context: |
    # Mavjud kod
    {existing_code}
  user: |
    # Vazifa
    {task_description}
```

#### 3.1.3 Debug Base Template

```yaml
name: debug_base
version: 1.0.0
type: base
components:
  system: |
    Siz tajribali debuggerisiz.
    {debugging_approach}
  error_context: |
    # Xatolik
    {error_message}
    
    # Xatolik tarixi
    {error_history}
  code_context: |
    # Muammoli kod
    {problematic_code}
  user: |
    # Muammo tavsifi
    {problem_description}
```

#### 3.1.4 Planning Base Template

```yaml
name: planning_base
version: 1.0.0
type: base
components:
  system: |
    Siz tajribali loyiha rahbarisiz.
    {planning_approach}
  context: |
    # Maqsad
    {goal}
    
    # Cheklovlar
    {constraints}
    
    # Resurslar
    {resources}
  user: |
    # Loyiha tavsifi
    {project_description}
```

#### 3.1.5 Research Base Template

```yaml
name: research_base
version: 1.0.0
type: base
components:
  system: |
    Siz tajribali tadqiqotchisiz.
    {research_approach}
  context: |
    # Tadqiqot mavzusi
    {topic}
    
    # Mavjud manbalar
    {sources}
  user: |
    # Tadqiqot savoli
    {research_question}
```

#### 3.1.6 Security Base Template

```yaml
name: security_base
version: 1.0.0
type: base
components:
  system: |
    Siz tajribali xavfsizlik mutaxassisisiz.
    {security_approach}
  context: |
    # Kod
    {code_context}
    
    # Tizim arxitekturasi
    {architecture}
  user: |
    # Xavfsizlik tahlili
    {security_request}
```

---

### 3.2 Task Templates

| Template | Base | Specialization |
|----------|------|----------------|
| `code_generation` | code_base | + file generation rules |
| `code_review` | code_base | + review criteria |
| `bug_fix` | debug_base | + fix strategies |
| `feature_design` | planning_base | + design patterns |
| `architecture` | planning_base | + architecture patterns |
| `performance` | research_base | + optimization |
| `testing` | code_base | + test strategies |
| `documentation` | code_base | + doc standards |
| `refactoring` | code_base | + refactoring patterns |
| `migration` | planning_base | + migration steps |
| `deployment` | planning_base | + deployment steps |
| `monitoring` | research_base | + monitoring setup |

---

## 4. Template Features

### 4.1 Dynamic Variables

```yaml
variables:
  - name: user_request
    type: string
    required: true
  - name: project_context
    type: string
    required: false
    default: ""
  - name: language_rule
    type: string
    required: true
    default: "Javobni O'zbek tilida bering."
  - name: examples
    type: list
    required: false
    default: []
```

### 4.2 Conditional Blocks

```yaml
conditions:
  - name: has_code_context
    condition: "{code_context} != ''"
    template: |
      # Mavjud kod
      ```
      {code_context}
      ```
  - name: is_multilingual
    condition: "{language} == 'multi'"
    template: |
      Siz ko'p tilli yordamchisiz.
      Foydalanuvchi tilida javob bering.
  - name: requires_security
    condition: "{security_level} == 'high'"
    template: |
      Xavfsizlik qoidalari:
      - Hech qanday maxfiy ma'lumotni chiqarmang
      - Xavfsiz kod yozing
```

### 4.3 Nested Templates

```yaml
composite_templates:
  - name: full_code_generation
    components:
      - template: code_base
        variables:
          language_rule: "{language_rule}"
          coding_standards: "{coding_standards}"
      - template: task_specific
        variables:
          task: "{task}"
      - template: output_format
        variables:
          format: "{output_format}"
```

### 4.4 Versioning

```yaml
versioning:
  enabled: true
  strategy: semantic
  history:
    - version: 1.0.0
      date: 2026-01-01
      author: system
      score: 0.75
    - version: 1.1.0
      date: 2026-02-01
      author: system
      score: 0.82
    - version: 1.2.0
      date: 2026-03-01
      author: system
      score: 0.88
```

### 4.5 Localization

```yaml
localization:
  enabled: true
  languages:
    - code: uz
      name: O'zbek
      template: chat_base_uz
    - code: en
      name: English
      template: chat_base_en
    - code: ru
      name: Русский
      template: chat_base_ru
```

---

## 5. Template Selection Logic

### 5.1 Selection Algorithm

```
Task Type Detection
    │
    ↓
┌─────────────────────────────────────────────────────┐
│  1. Map task_type → base_template                    │
│     code_generation → code_base                      │
│     debugging → debug_base                           │
│     planning → planning_base                         │
│     research → research_base                         │
│     security → security_base                         │
└──────────────────────────┬──────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────┐
│  2. Map task_type → task_template                    │
│     code_generation → code_generation                │
│     code_review → code_review                        │
│     bug_fix → bug_fix                                │
└──────────────────────────┬──────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────┐
│  3. Map model → model_variant                        │
│     claude → code_base_claude                        │
│     gpt → code_base_gpt                              │
│     qwen → code_base_qwen                            │
└──────────────────────────┬──────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────┐
│  4. Select language variant                          │
│     uz → _uz suffix                                  │
│     en → _en suffix                                  │
│     (default) → _en suffix                           │
└──────────────────────────┬──────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────┐
│  5. Assemble composite template                      │
│     base + task + model + language                   │
└─────────────────────────────────────────────────────┘
```

---

## 6. Configuration

```yaml
prompt_templates:
  # Registry
  registry:
    enabled: true
    auto_register: true
    
  # Selection
  selection:
    auto_select: true
    fallback: chat_base
    
  # Features
  features:
    variables: true
    conditions: true
    nesting: true
    versioning: true
    localization: true
    
  # Limits
  limits:
    max_templates: 100
    max_variables: 50
    max_conditions: 20
    max_nesting_depth: 5
```
