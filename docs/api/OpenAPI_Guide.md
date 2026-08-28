# AIDA Enterprise API Foundation
## OpenAPI Guide

**Versiya:** 1.0.0
**Sana:** 2026-07-03
**Muallif:** AIDA API Team

---

## 1. OPENAPI 3.1 SPESIFIKATSIYA

### 1.1 OpenAPI Fayl Strukturasi

```yaml
# /docs/api/openapi.yaml yoki /api/v1/openapi.json da xizmat qilinadi

openapi: "3.1.0"

info:
  title: AIDA API
  version: "1.0.0"
  description: |
    AIDA Enterprise AI Platform API.
    Full documentation: https://docs.aida.ai
  contact:
    name: AIDA API Team
    email: api@aida.ai
    url: https://docs.aida.ai
  license:
    name: Proprietary
    url: https://aida.ai/terms

servers:
  - url: https://api.aida.ai/api/v1
    description: Production
  - url: https://staging.api.aida.ai/api/v1
    description: Staging
  - url: http://localhost:8000/api/v1
    description: Local development

externalDocs:
  description: Full AIDA documentation
  url: https://docs.aida.ai
```

### 1.2 Security Schemes

```yaml
components:
  securitySchemes:

    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: |
        JWT access token. Obtain via POST /auth/login/
        Include as: Authorization: Bearer {token}

    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-AIDA-Key
      description: |
        API Key for platform integrations.
        Obtain from user settings.

    OAuth2:
      type: oauth2
      flows:
        authorizationCode:
          authorizationUrl: https://api.aida.ai/api/v1/auth/oauth2/github/
          tokenUrl: https://api.aida.ai/api/v1/auth/token/
          scopes:
            chat:read: Read chats and messages
            chat:write: Create and send messages
            agent:run: Run AI agents
            knowledge:write: Add knowledge base entries

# Global security (barcha endpoint'larda default)
security:
  - BearerAuth: []
  - ApiKeyAuth: []
```

### 1.3 Common Parameters

```yaml
components:
  parameters:

    PageParam:
      name: page
      in: query
      schema:
        type: integer
        minimum: 1
        default: 1
      description: Page number for offset pagination

    PageSizeParam:
      name: page_size
      in: query
      schema:
        type: integer
        minimum: 1
        maximum: 100
        default: 20
      description: Items per page

    CursorParam:
      name: cursor
      in: query
      schema:
        type: string
      description: Cursor for cursor-based pagination

    SearchParam:
      name: search
      in: query
      schema:
        type: string
        maxLength: 200
      description: Full-text search query

    OrderingParam:
      name: ordering
      in: query
      schema:
        type: string
      description: |
        Sort field. Prefix with '-' for descending.
        Example: -created_at or created_at,title

    RequestIdHeader:
      name: X-Request-ID
      in: header
      schema:
        type: string
        format: uuid
      description: Optional client-provided request ID for tracing
```

---

## 2. SCHEMA TA'RIFLARI

### 2.1 Standard Response Wrappers

```yaml
components:
  schemas:

    SuccessResponse:
      type: object
      required: [status, success, data, request_id, execution_time_ms]
      properties:
        status:
          type: integer
          example: 200
        success:
          type: boolean
          example: true
        message:
          type: string
          example: "Resource retrieved successfully"
        data:
          description: Response payload (object or array)
        metadata:
          type: object
          description: Additional context
        pagination:
          $ref: '#/components/schemas/Pagination'
        request_id:
          type: string
          example: "req_abc123xyz"
        execution_time_ms:
          type: integer
          example: 45

    ErrorResponse:
      type: object
      required: [status, success, error, request_id]
      properties:
        status:
          type: integer
          example: 422
        success:
          type: boolean
          example: false
        message:
          type: string
          example: "Validation failed"
        error:
          $ref: '#/components/schemas/ErrorDetail'
        request_id:
          type: string
        execution_time_ms:
          type: integer

    ErrorDetail:
      type: object
      required: [code, description, reason, recovery]
      properties:
        code:
          type: string
          example: "VALIDATION_ERROR"
        description:
          type: string
        reason:
          type: string
        recovery:
          type: string
        fields:
          type: object
          additionalProperties:
            type: array
            items:
              type: string
        docs:
          type: string
          format: uri
        trace_id:
          type: string

    Pagination:
      type: object
      properties:
        count:
          type: integer
          nullable: true
        page:
          type: integer
        page_size:
          type: integer
        total_pages:
          type: integer
          nullable: true
        has_next:
          type: boolean
        has_previous:
          type: boolean
        next_cursor:
          type: string
          nullable: true
        previous_cursor:
          type: string
          nullable: true
        next:
          type: string
          format: uri
          nullable: true
        previous:
          type: string
          format: uri
          nullable: true
```

### 2.2 Core Entity Schemas

```yaml
    Chat:
      type: object
      properties:
        id:
          type: string
          format: uuid
        title:
          type: string
          maxLength: 500
        user_id:
          type: string
          format: uuid
        project_id:
          type: string
          format: uuid
          nullable: true
        model_id:
          type: string
          format: uuid
          nullable: true
        model_config:
          type: object
          properties:
            temperature:
              type: number
              minimum: 0
              maximum: 2
            max_tokens:
              type: integer
        message_count:
          type: integer
          readOnly: true
        total_tokens:
          type: integer
          readOnly: true
        is_archived:
          type: boolean
          default: false
        created_at:
          type: string
          format: date-time
          readOnly: true
        updated_at:
          type: string
          format: date-time
          readOnly: true

    Message:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        chat_id:
          type: string
          format: uuid
        role:
          type: string
          enum: [user, assistant, system, tool]
        content:
          type: string
        tokens_input:
          type: integer
          readOnly: true
        tokens_output:
          type: integer
          readOnly: true
        model_name:
          type: string
          nullable: true
          readOnly: true
        finish_reason:
          type: string
          enum: [stop, length, tool_calls, error]
          nullable: true
          readOnly: true
        created_at:
          type: string
          format: date-time
          readOnly: true

    Agent:
      type: object
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
          maxLength: 255
        slug:
          type: string
          pattern: '^[a-z0-9-]+$'
        type:
          type: string
          enum: [general, code, research, data, custom]
        status:
          type: string
          enum: [active, inactive, maintenance]
        capabilities:
          type: array
          items:
            type: string
        created_at:
          type: string
          format: date-time
          readOnly: true
```

---

## 3. ENDPOINT TA'RIFLARI (MISOLLAR)

### 3.1 Chat yaratish

```yaml
paths:
  /chats/:
    post:
      summary: Create a new chat
      operationId: chats_create
      tags: [Chats]
      security:
        - BearerAuth: []
      parameters:
        - $ref: '#/components/parameters/RequestIdHeader'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [title]
              properties:
                title:
                  type: string
                  minLength: 1
                  maxLength: 500
                  example: "My first chat"
                project_id:
                  type: string
                  format: uuid
                  nullable: true
                model_id:
                  type: string
                  format: uuid
                  nullable: true
                model_config:
                  type: object
                  properties:
                    temperature:
                      type: number
                      default: 0.7
                    max_tokens:
                      type: integer
                      default: 2000
            examples:
              basic:
                summary: Basic chat
                value:
                  title: "My Chat"
              with_model:
                summary: Chat with specific model
                value:
                  title: "GPT-4 Chat"
                  model_id: "uuid-of-gpt4o"
                  model_config:
                    temperature: 0.5
      responses:
        "201":
          description: Chat created successfully
          content:
            application/json:
              schema:
                allOf:
                  - $ref: '#/components/schemas/SuccessResponse'
                  - type: object
                    properties:
                      data:
                        $ref: '#/components/schemas/Chat'
        "401":
          $ref: '#/components/responses/Unauthorized'
        "422":
          $ref: '#/components/responses/ValidationError'
        "429":
          $ref: '#/components/responses/RateLimited'

    get:
      summary: List chats
      operationId: chats_list
      tags: [Chats]
      parameters:
        - $ref: '#/components/parameters/CursorParam'
        - $ref: '#/components/parameters/PageSizeParam'
        - $ref: '#/components/parameters/SearchParam'
        - name: is_archived
          in: query
          schema:
            type: boolean
        - $ref: '#/components/parameters/OrderingParam'
      responses:
        "200":
          description: List of chats
          content:
            application/json:
              schema:
                allOf:
                  - $ref: '#/components/schemas/SuccessResponse'
                  - type: object
                    properties:
                      data:
                        type: array
                        items:
                          $ref: '#/components/schemas/Chat'
```

### 3.2 Standard Responses

```yaml
components:
  responses:

    Unauthorized:
      description: Authentication required or token invalid
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
          examples:
            token_expired:
              value:
                status: 401
                success: false
                error:
                  code: TOKEN_EXPIRED
                  description: The access token has expired
                  reason: Token expired at 2026-07-03T10:52:00Z
                  recovery: Use refresh token to get a new access token

    Forbidden:
      description: Permission denied
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'

    NotFound:
      description: Resource not found
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'

    ValidationError:
      description: Validation failed
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'

    RateLimited:
      description: Rate limit exceeded
      headers:
        Retry-After:
          schema:
            type: integer
          description: Seconds to wait before retry
        X-RateLimit-Limit:
          schema:
            type: integer
        X-RateLimit-Remaining:
          schema:
            type: integer
        X-RateLimit-Reset:
          schema:
            type: integer
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'

    ServerError:
      description: Internal server error
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
```

---

## 4. SWAGGER UI SOZLAMALARI

### 4.1 Django drf-spectacular integratsiyasi

```python
# Django settings.py (dizayn)

INSTALLED_APPS = [
    'drf_spectacular',
    ...
]

SPECTACULAR_SETTINGS = {
    'TITLE': 'AIDA API',
    'VERSION': '1.0.0',
    'DESCRIPTION': 'AIDA Enterprise AI Platform API',
    'CONTACT': {'email': 'api@aida.ai'},
    'SCHEMA_PATH_PREFIX': '/api/v[0-9]',

    # UI sozlamalari
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
        'defaultModelsExpandDepth': 2,
        'defaultModelExpandDepth': 2,
        'filter': True,
    },

    # Postman collection uchun
    'POSTMAN_SETTINGS': {
        'name': 'AIDA API Collection',
        'version': '1.0.0',
    },

    # Security
    'SECURITY': [{'BearerAuth': []}, {'ApiKeyAuth': []}],

    # Component prefix
    'COMPONENT_SPLIT_REQUEST': True,
    'COMPONENT_NO_READ_ONLY_REQUIRED': True,
}
```

### 4.2 Swagger UI Endpointlari

```
GET /api/docs/              → Swagger UI (HTML)
GET /api/docs/redoc/        → ReDoc UI (HTML)
GET /api/schema/            → OpenAPI JSON/YAML
GET /api/schema/download/   → OpenAPI fayl yuklab olish
```

---

## 5. POSTMAN COLLECTION

### 5.1 Collection Strukturasi

```
AIDA API Collection
├── 🔐 Authentication
│   ├── Register
│   ├── Login → saves {{access_token}}, {{refresh_token}}
│   ├── Refresh Token
│   └── Logout
├── 💬 Chats
│   ├── Create Chat
│   ├── List Chats
│   ├── Get Chat
│   ├── Update Chat
│   └── Delete Chat
├── 📨 Messages
│   ├── Send Message
│   ├── Stream Message (SSE)
│   ├── List Messages
│   └── Regenerate
├── 🤖 Agents
│   ├── Create Agent
│   ├── Run Agent
│   ├── Get Status
│   └── Stop Agent
├── 🧠 Knowledge
│   ├── Add Knowledge
│   ├── Search Knowledge
│   └── Index Knowledge
└── 🔧 Platform API
    ├── Chat (API Key)
    └── Stream Chat (API Key)
```

### 5.2 Postman Environment Variables

```json
{
  "name": "AIDA Production",
  "values": [
    {"key": "base_url",      "value": "https://api.aida.ai"},
    {"key": "api_version",   "value": "v1"},
    {"key": "access_token",  "value": "", "type": "secret"},
    {"key": "refresh_token", "value": "", "type": "secret"},
    {"key": "api_key",       "value": "", "type": "secret"},
    {"key": "chat_id",       "value": ""},
    {"key": "agent_id",      "value": ""}
  ]
}
```

### 5.3 Postman Pre-request Script (Login)

```javascript
// Login request'da: Tests tab
const response = pm.response.json();
if (response.success) {
    pm.environment.set("access_token", response.data.access_token);
    // refresh_token HttpOnly cookie'da keladi
    pm.test("Login successful", () => pm.expect(response.success).to.be.true);
}

// Authorization header avto-to'ldirish:
// Collection > Authorization > Bearer Token: {{access_token}}
```

---

## 6. SDK DOCUMENTATION

### 6.1 Python SDK Docs

```
docs.aida.ai/sdk/python/
  /getting-started       → Installation, quick start
  /authentication        → API key, JWT setup
  /chats                 → Chat management
  /messages              → Streaming messages
  /agents                → Agent management
  /knowledge             → Knowledge base
  /pagination            → Iterating pages
  /error-handling        → Exception types
  /async                 → AsyncAidaClient guide
  /changelog             → Version history
```

### 6.2 Interactive Code Examples

Har endpoint uchun hujjatda:

```
1. cURL misoli
2. Python misoli
3. JavaScript misoli
4. "Run in Postman" tugmasi
5. Response misoli (real JSON)
6. Error misollari (401, 422, 429)
```

---

## 7. API CHANGELOG STANDARTI

```markdown
# API Changelog

## v1.1.0 (2026-08-01)
### Added
- `POST /api/v1/rag/rerank/` — RAG natijalarini qayta tartiblash
- `GET /api/v1/models/{slug}/pricing/` — Model narxi

### Changed
- `GET /api/v1/chats/` — `last_message_at` sort qo'shildi

### Deprecated
- `GET /api/v1/models/list/` → `GET /api/v1/models/` ishlatilsin
  Sunset: 2026-11-01

## v1.0.0 (2026-07-03)
### Initial release
```

---

## 8. API VERSIONING HUJJATLARI

```
docs.aida.ai/api/
  /v1/          → v1 hujjatlari (joriy)
  /v2/          → v2 hujjatlari (beta)
  /migration/v1-to-v2/  → Migration guide
  /changelog/   → Barcha versiyalar tarixi
  /deprecations/ → Eskirgan endpointlar va sunset sanalari
```

---

*Hujjat AIDA Development Bible — Book 1, Chapter 9 asosida tayyorlangan.*
