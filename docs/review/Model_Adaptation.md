# AIDA Model Adaptation

**Document:** Book 2, Chapter 7 - Model Adaptation
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

Model Adaptation automatically adjusts prompts based on each model's strengths, weaknesses, token limits, formatting preferences, and behavioral patterns. Every model receives a prompt optimized for its specific characteristics.

---

## 2. Model Profiles

| Model | Provider | Context | Output | Strengths | Weaknesses |
|-------|----------|---------|--------|-----------|------------|
| Claude | Anthropic | 200K | 4K | Reasoning, Safety, Code | Slower, Costly |
| GPT-4 | OpenAI | 128K | 4K | Speed, Functions, Vision | Verbose |
| Gemini | Google | 1M | 8K | Large context, Speed | Less precise |
| Qwen | Alibaba | 32K | 2K | Code, Cost-efficient | English |
| DeepSeek | DeepSeek | 64K | 4K | Math, Code, Reasoning | Slow |
| Llama | Meta | 8K | 2K | Open-source, Fast | Limited features |
| Mistral | Mistral | 32K | 4K | Speed, European languages | Smaller models |
| Phi | Microsoft | 4K | 2K | Small, Fast, Efficient | Limited knowledge |
| Local | Ollama | Varies | Varies | Private, Free | Limited power |

---

## 3. Prompt Strategies

### 3.1 Claude Strategy

- Structure Format: XML tags
- Instruction Style: Explicit and detailed
- System Prefix: Wrapped in system tags
- Example Format: example-input-output-example
- Output Format: response-thinking-answer-response
- Strengths to leverage: Long context, multi-step reasoning, safety awareness
- Avoid: Very long prompts (expensive), rapid-fire requests

### 3.2 GPT Strategy

- Structure Format: JSON
- Instruction Style: Concise
- Function Calling: Enabled for structured output
- System Prefix: System Instructions markdown header
- Example Format: Input: ... Output: ...
- Output Format: JSON with thinking and answer fields
- Strengths to leverage: Function calling, multimodal, speed
- Avoid: Very long system prompts (token waste)

### 3.3 Gemini Strategy

- Structure Format: Markdown
- Instruction Style: Visual and descriptive
- System Prefix: System Instructions H1 header
- Example Format: Example Input: ... Output: ...
- Output Format: Markdown sections for thinking and answer
- Strengths to leverage: 1M context window, multimodal, fast
- Avoid: Precise numerical reasoning

### 3.4 Qwen Strategy

- Structure Format: ChatML format
- Instruction Style: Detailed with context
- System Prefix: ChatML system role
- Example Format: ChatML user/assistant pairs
- Output Format: ChatML assistant response
- Strengths to leverage: Code generation, cost efficiency
- Avoid: Complex English instructions

### 3.5 DeepSeek Strategy

- Structure Format: Markdown
- Instruction Style: Step-by-step reasoning
- System Prefix: Markdown system block
- Example Format: Numbered examples with reasoning chains
- Output Format: Chain-of-thought followed by answer
- Strengths to leverage: Math, code, deep reasoning
- Avoid: Speed-critical applications

### 3.6 Llama Strategy

- Structure Format: Simple text
- Instruction Style: Direct and clear
- System Prefix: SYS tags (Llama format)
- Example Format: Simple input/output pairs
- Output Format: Plain text
- Strengths to leverage: Local deployment, privacy, customization
- Avoid: Complex multi-turn conversations

### 3.7 Mistral Strategy

- Structure Format: Simple text with headers
- Instruction Style: Professional and concise
- System Prefix: System instruction block
- Example Format: Numbered examples
- Output Format: Structured text
- Strengths to leverage: European languages, speed, instruction following
- Avoid: Very long context windows

### 3.8 Phi Strategy

- Structure Format: Simple text
- Instruction Style: Minimal and focused
- System Prefix: Short system message
- Example Format: 1-2 examples maximum
- Output Format: Concise text
- Strengths to leverage: Fast inference, edge deployment, efficiency
- Avoid: Complex reasoning tasks

### 3.9 Local Model Strategy (Ollama)

- Structure Format: Depends on model family
- Instruction Style: Adjusted to model capability
- System Prefix: Varies by model
- Example Format: Minimal examples
- Output Format: Matches model training format
- Strengths to leverage: Privacy, no API cost, customization
- Avoid: Tasks exceeding model capability

---

## 4. Adaptation Logic

### 4.1 Selection Algorithm

`
1. Detect target model
2. Load model profile
3. Check model capabilities
4. Select appropriate strategy
5. Apply model-specific formatting
6. Adjust token limits
7. Set output format
8. Validate against model constraints
`

### 4.2 Capability Matching

| Capability | Required | Models Supporting |
|------------|----------|-------------------|
| Function Calling | code, workflow | Claude, GPT, Gemini |
| Vision | vision tasks | Claude, GPT, Gemini |
| Large Context | >32K tokens | Claude, GPT, Gemini |
| Streaming | real-time | All |
| JSON Mode | structured output | GPT, Claude |
| Code Execution | sandbox | GPT, Gemini |

---

## 5. Token Budget Per Model

| Model | Input Budget | Output Budget | Cost per 1K |
|-------|-------------|---------------|-------------|
| Claude-3.5 | 180K | 3.5K | .003 |
| GPT-4o | 110K | 3.5K | .0025 |
| Gemini-1.5 | 900K | 7K | .001 |
| Qwen-2.5 | 28K | 1.8K | .0005 |
| DeepSeek-V2 | 56K | 3.5K | .0003 |
| Llama-3-70B | 6K | 1.8K | .0002 |
| Mistral-7B | 28K | 3.5K | .0002 |
| Phi-3 | 3K | 1.8K | .0001 |
| Local (Ollama) | Varies | Varies | .00 |

---

## 6. Configuration

`yaml
model_adaptation:
  enabled: true
  auto_detect: true
  fallback_model: qwen2.5:3b
  profiles:
    auto_load: true
    cache_profiles: true
  strategies:
    auto_select: true
    prefer_model_strengths: true
  token_budget:
    enforce_limits: true
    warning_threshold: 0.8
  cost_tracking:
    enabled: true
    alert_threshold: 1.0
`
