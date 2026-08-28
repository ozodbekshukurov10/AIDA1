# AIDA Enterprise API Foundation
## SDK Guide

**Versiya:** 1.0.0
**Sana:** 2026-07-03
**Muallif:** AIDA API Team

---

## 1. SDK ARXITEKTURASI

Barcha SDK'lar uchun umumiy dizayn prinsiplari:

```
PRINSIPLAR:
  1. Idiomatik kod — har til o'ziga xos pattern
  2. Auto-retry (exponential backoff)
  3. Streaming qo'llab-quvvatlash
  4. Type safety (TypeScript, Go, Java, C#)
  5. Async/await (Python asyncio, JS Promises)
  6. Paginatsiya helper'lari
  7. Error handling standardlashtirilgan
  8. Environment-based config (env vars)
  9. Minimal dependencies
  10. OpenAPI'dan auto-generated (foundation) + manual enhancement
```

### SDK Paket Nomlari

| Til | Paket | Registry |
|-----|-------|----------|
| Python | `aida-sdk` | PyPI |
| JavaScript | `@aida/sdk` | npm |
| TypeScript | `@aida/sdk` | npm (types included) |
| Go | `github.com/aida-ai/aida-go` | Go modules |
| Java | `ai.aida:aida-java-sdk` | Maven Central |
| C# | `Aida.SDK` | NuGet |

---

## 2. PYTHON SDK

### 2.1 Dizayn

```python
# Paket: aida-sdk (PyPI)
# Python 3.9+
# Dependencies: httpx (async), pydantic (validation)

# Asosiy foydalanish:
from aida import AidaClient

client = AidaClient(
    api_key="aida_sk_...",           # yoki env: AIDA_API_KEY
    base_url="https://api.aida.ai",  # yoki env: AIDA_BASE_URL
    timeout=30.0,
    max_retries=3,
)

# Sync chat
response = client.chat.create(
    title="My Chat",
    model="gpt-4o",
)

# Message yuborish
message = client.messages.create(
    chat_id=response.id,
    content="Explain quantum computing",
)
print(message.content)

# Streaming
for token in client.messages.stream(
    chat_id=chat.id,
    content="Write a poem",
):
    print(token, end="", flush=True)

# Async versiya
import asyncio
from aida import AsyncAidaClient

async def main():
    async with AsyncAidaClient(api_key="...") as client:
        async for token in client.messages.stream(...):
            print(token, end="", flush=True)

asyncio.run(main())
```

### 2.2 Python Modullar Strukturasi

```
aida/
  __init__.py          → AidaClient, AsyncAidaClient eksport
  _client.py           → Asosiy client
  _async_client.py     → Async client
  _config.py           → Config, env vars
  _auth.py             → JWT, API key handler
  _retry.py            → Exponential backoff
  _streaming.py        → SSE parser
  _websocket.py        → WS client
  _pagination.py       → Cursor/page iterator
  resources/
    auth.py
    users.py
    chats.py
    messages.py
    agents.py
    knowledge.py
    files.py
    ...
  models/              → Pydantic models (response types)
    chat.py
    message.py
    agent.py
    ...
  exceptions.py        → AidaError, AuthError, RateLimitError, ...
```

### 2.3 Python Pagination

```python
# Barcha sahifalarni iterator bilan:
for chat in client.chats.list_all(page_size=50):
    print(chat.title)

# Bir sahifa:
page = client.chats.list(page=1, page_size=20)
print(page.count)      # total count
print(page.has_next)   # keyingi sahifa bormi
for chat in page.data:
    print(chat.title)

# Cursor-based:
cursor = None
while True:
    page = client.messages.list(chat_id=..., cursor=cursor)
    for msg in page.data:
        process(msg)
    if not page.has_next:
        break
    cursor = page.next_cursor
```

### 2.4 Python Error Handling

```python
from aida.exceptions import (
    AidaError,           # Barcha xatolarning asosi
    AuthenticationError, # 401
    PermissionError,     # 403
    NotFoundError,       # 404
    ValidationError,     # 422
    RateLimitError,      # 429
    AIProviderError,     # 502
    ServerError,         # 500
)

try:
    message = client.messages.create(...)
except RateLimitError as e:
    print(f"Rate limited. Retry after: {e.retry_after}s")
except AIProviderError as e:
    print(f"AI error: {e.code} — {e.recovery}")
    # Fallback model
    message = client.messages.create(..., model="claude-3-5-sonnet")
except ValidationError as e:
    print(f"Validation: {e.fields}")
except AidaError as e:
    print(f"Error: {e.code} — {e.message}")
```

---

## 3. JAVASCRIPT / TYPESCRIPT SDK

### 3.1 Dizayn

```typescript
// Paket: @aida/sdk (npm)
// Node.js 18+, Browser (fetch API)
// Zero dependencies (fetch built-in)

import { AidaClient } from '@aida/sdk';

const client = new AidaClient({
  apiKey: process.env.AIDA_API_KEY,    // yoki string
  baseUrl: 'https://api.aida.ai',
  timeout: 30_000,
  maxRetries: 3,
});

// Chat yaratish
const chat = await client.chats.create({ title: 'My Chat' });

// Message (streaming)
const stream = await client.messages.stream({
  chatId: chat.id,
  content: 'Explain REST APIs',
});

for await (const token of stream) {
  process.stdout.write(token);
}
const finalMessage = await stream.finalMessage();
console.log('Tokens used:', finalMessage.usage.totalTokens);

// Agents
const agent = await client.agents.get('agent-id');
const run = await client.agents.run('agent-id', {
  taskType: 'code_review',
  input: { code: '...' },
});

// WebSocket
const ws = client.websocket.connect();
ws.on('agent.completed', (event) => {
  console.log('Agent done:', event.payload);
});
ws.subscribe(['agent:123', 'notifications']);
```

### 3.2 TypeScript Tizimlari

```typescript
// Response types (auto-generated + manual)

interface Chat {
  id: string;
  title: string;
  userId: string;
  projectId: string | null;
  modelConfig: ModelConfig;
  messageCount: number;
  totalTokens: number;
  lastMessageAt: Date | null;
  isArchived: boolean;
  createdAt: Date;
  updatedAt: Date;
}

interface Message {
  id: number;
  chatId: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  tokensInput: number;
  tokensOutput: number;
  modelName: string | null;
  finishReason: 'stop' | 'length' | 'tool_calls' | 'error' | null;
  metadata: Record<string, unknown>;
  createdAt: Date;
}

interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    count: number | null;
    hasNext: boolean;
    hasPrevious: boolean;
    nextCursor: string | null;
    previousCursor: string | null;
  };
}

// Streaming types
interface StreamToken {
  token: string;
  index: number;
}

interface StreamFinalMessage extends Message {
  usage: {
    tokensInput: number;
    tokensOutput: number;
    totalTokens: number;
  };
  durationMs: number;
}
```

### 3.3 JavaScript Modullar

```
@aida/sdk/
  src/
    index.ts          → AidaClient, types eksport
    client.ts         → Asosiy client
    auth.ts           → Token handler
    retry.ts          → Backoff
    streaming.ts      → SSE parser
    websocket.ts      → WS client
    resources/
      chats.ts
      messages.ts
      agents.ts
      knowledge.ts
      ...
    types/
      index.ts        → Barcha public types
      resources.ts    → Resource response types
      errors.ts       → Error types
  dist/               → Compiled JS (CJS + ESM)
  types/              → .d.ts files
```

---

## 4. GO SDK

### 4.1 Dizayn

```go
// Module: github.com/aida-ai/aida-go
// Go 1.21+

package main

import (
    "context"
    "fmt"
    "github.com/aida-ai/aida-go"
)

func main() {
    client := aida.NewClient(
        aida.WithAPIKey("aida_sk_..."),   // yoki AIDA_API_KEY env
        aida.WithBaseURL("https://api.aida.ai"),
        aida.WithTimeout(30),
        aida.WithMaxRetries(3),
    )

    ctx := context.Background()

    // Chat yaratish
    chat, err := client.Chats.Create(ctx, &aida.CreateChatParams{
        Title:   "My Chat",
        ModelID: aida.String("gpt-4o"),
    })
    if err != nil {
        var rateLimitErr *aida.RateLimitError
        if errors.As(err, &rateLimitErr) {
            fmt.Printf("Rate limited, retry after %ds\n", rateLimitErr.RetryAfter)
        }
        return
    }

    // Streaming
    stream, err := client.Messages.Stream(ctx, chat.ID, &aida.StreamParams{
        Content: "Explain Go concurrency",
    })
    if err != nil { /* handle */ }
    defer stream.Close()

    for stream.Next() {
        token := stream.Token()
        fmt.Print(token)
    }
    if err := stream.Err(); err != nil { /* handle */ }
}
```

### 4.2 Go Xususiyatlari

```go
// Pagination iterator
iter := client.Chats.List(ctx, &aida.ListParams{PageSize: 50})
for iter.Next() {
    chat := iter.Current()
    fmt.Println(chat.Title)
}
if err := iter.Err(); err != nil { /* handle */ }

// Context cancellation (streaming bekor qilish)
ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
defer cancel()

stream, _ := client.Messages.Stream(ctx, chatID, params)
// ctx.Done() → stream avtomatik to'xtatiladi

// Strukturali error handling
var apiErr *aida.APIError
if errors.As(err, &apiErr) {
    fmt.Printf("Code: %s\nRecovery: %s\n", apiErr.Code, apiErr.Recovery)
}
```

---

## 5. JAVA SDK

### 5.1 Dizayn

```java
// Artifact: ai.aida:aida-java-sdk
// Java 17+, Spring Boot bilan ham ishlaydi
// Dependencies: Jackson, OkHttp3

import ai.aida.AidaClient;
import ai.aida.models.*;
import ai.aida.exceptions.*;

public class Example {
    public static void main(String[] args) {
        AidaClient client = AidaClient.builder()
            .apiKey("aida_sk_...")          // yoki env: AIDA_API_KEY
            .baseUrl("https://api.aida.ai")
            .timeout(Duration.ofSeconds(30))
            .maxRetries(3)
            .build();

        // Chat yaratish
        Chat chat = client.chats().create(
            CreateChatRequest.builder()
                .title("My Chat")
                .modelId("gpt-4o")
                .build()
        );

        // Streaming (reactive)
        client.messages().stream(
            chat.getId(),
            StreamMessageRequest.builder()
                .content("Explain Java streams")
                .build()
        )
        .subscribe(
            token -> System.out.print(token),
            error -> System.err.println("Error: " + error.getMessage()),
            () -> System.out.println("\nDone!")
        );

        // Error handling
        try {
            Message msg = client.messages().create(...);
        } catch (RateLimitException e) {
            System.out.printf("Retry after: %ds%n", e.getRetryAfter());
        } catch (AIProviderException e) {
            System.out.printf("AI error: %s%n", e.getRecovery());
        } catch (AidaException e) {
            System.out.printf("Error: %s%n", e.getCode());
        }
    }
}
```

### 5.2 Java Builder Pattern

```java
// Barcha request va response'lar Builder pattern:

CreateAgentRequest request = CreateAgentRequest.builder()
    .name("Code Assistant")
    .type(AgentType.CODE)
    .modelId("gpt-4o")
    .capabilities(List.of("code_review", "refactoring"))
    .config(AgentConfig.builder()
        .maxIterations(10)
        .timeoutSeconds(300)
        .build())
    .build();

// Pagination
Page<Chat> page = client.chats().list(
    ListChatsRequest.builder()
        .pageSize(20)
        .ordering("-created_at")
        .build()
);

for (Chat chat : page.getData()) {
    System.out.println(chat.getTitle());
}

if (page.hasNext()) {
    Page<Chat> nextPage = page.nextPage();
}
```

---

## 6. C# SDK

### 6.1 Dizayn

```csharp
// Package: Aida.SDK (NuGet)
// .NET 8+, async/await

using Aida;
using Aida.Models;
using Aida.Exceptions;

var client = new AidaClient(new AidaClientOptions
{
    ApiKey = Environment.GetEnvironmentVariable("AIDA_API_KEY"),
    BaseUrl = "https://api.aida.ai",
    Timeout = TimeSpan.FromSeconds(30),
    MaxRetries = 3
});

// Chat yaratish
var chat = await client.Chats.CreateAsync(new CreateChatRequest
{
    Title = "My Chat",
    ModelId = "gpt-4o"
});

// Streaming
await foreach (var token in client.Messages.StreamAsync(
    chat.Id,
    new StreamMessageRequest { Content = "Explain C# LINQ" },
    cancellationToken))
{
    Console.Write(token);
}

// LINQ-style pagination
var allChats = await client.Chats
    .ListAsync()
    .Where(c => !c.IsArchived)
    .OrderByDescending(c => c.LastMessageAt)
    .ToListAsync();

// Error handling
try
{
    var msg = await client.Messages.CreateAsync(...);
}
catch (RateLimitException ex)
{
    Console.WriteLine($"Rate limited. Retry after: {ex.RetryAfter}s");
}
catch (AidaException ex)
{
    Console.WriteLine($"Error: {ex.ErrorCode} — {ex.Recovery}");
}
```

---

## 7. BARCHA SDK UCHUN UMUMIY STANDARTLAR

### 7.1 Environment Variables

```
AIDA_API_KEY        → API kalit (barcha SDK)
AIDA_BASE_URL       → Base URL (default: https://api.aida.ai)
AIDA_TIMEOUT        → Timeout soniyada (default: 30)
AIDA_MAX_RETRIES    → Max retry soni (default: 3)
AIDA_LOG_LEVEL      → debug/info/warning/error (default: warning)
AIDA_PROXY          → HTTP proxy URL
```

### 7.2 Retry Logikasi (Barcha SDK)

```
Retry qilinadi:
  429 → Retry-After headerga qarab
  500, 503 → Exponential backoff
  504 → 1 retry
  Network error → Exponential backoff

Retry qilinmaydi:
  400, 422 → Client xatosi
  401, 403 → Auth xatosi
  404, 409 → Business xatosi

Backoff:
  attempt 1: darhol
  attempt 2: 1s + jitter
  attempt 3: 2s + jitter
  attempt 4: 4s + jitter
  Max: 3 (default), sozlanadi
```

### 7.3 Logging

```
SDK internal logging (strukturali):
  request:  method, url, request_id, duration_ms
  response: status_code, request_id
  retry:    attempt, delay, reason
  error:    error_code, message

Log levels:
  DEBUG: barcha request/response
  INFO:  muhim operatsiyalar
  WARNING: retry, rate limit
  ERROR: barcha xatolar
```

### 7.4 SDK Versioning

```
SDK semver: MAJOR.MINOR.PATCH
  MAJOR: breaking change (yangi major API version)
  MINOR: yangi feature (backward compatible)
  PATCH: bug fix

API version bilan moslik:
  SDK v1.x → API v1
  SDK v2.x → API v2
  Eski API versiyasini SDK qo'llab-quvvatlashi mumkin (deprecation period)
```

---

## 8. QUICK START (BARCHA TILLAR)

```bash
# Python
pip install aida-sdk
export AIDA_API_KEY=aida_sk_...
python -c "from aida import AidaClient; c=AidaClient(); print(c.models.list())"

# JavaScript/TypeScript
npm install @aida/sdk
export AIDA_API_KEY=aida_sk_...
node -e "const {AidaClient}=require('@aida/sdk'); ..."

# Go
go get github.com/aida-ai/aida-go
export AIDA_API_KEY=aida_sk_...

# Java (Maven)
# pom.xml: ai.aida:aida-java-sdk:1.0.0

# C# (NuGet)
dotnet add package Aida.SDK
```

---

*Hujjat AIDA Development Bible — Book 1, Chapter 9 asosida tayyorlangan.*
