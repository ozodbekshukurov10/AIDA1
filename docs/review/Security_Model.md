# AIDA Event Bus Security Model

**Document:** Book 2, Chapter 4 — Security Model
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The Security Model ensures every event is authenticated, authorized, validated, encrypted, and audited. It prevents unauthorized event publishing, ensures data confidentiality, and maintains a complete audit trail.

---

## 2. Security Layers

### 2.1 Layer Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    EVENT BUS SECURITY LAYERS                         │
│                                                                      │
│  Layer 1: Authentication                                            │
│  ├── Verify publisher identity                                      │
│  ├── Verify subscriber identity                                     │
│  └── Validate tokens/credentials                                    │
│                                                                      │
│  Layer 2: Authorization                                             │
│  ├── Check publish permissions                                      │
│  ├── Check subscribe permissions                                    │
│  └── Check topic-level permissions                                  │
│                                                                      │
│  Layer 3: Validation                                                │
│  ├── Schema validation                                              │
│  ├── Payload validation                                             │
│  └── Business rule validation                                       │
│                                                                      │
│  Layer 4: Encryption                                                │
│  ├── TLS in transit                                                 │
│  ├── Payload encryption at rest                                     │
│  └── Field-level encryption                                         │
│                                                                      │
│  Layer 5: Audit                                                     │
│  ├── Log all events                                                 │
│  ├── Log all access                                                 │
│  └── Tamper-proof audit log                                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Authentication

### 3.1 Authentication Methods

| Method | Description | Use Case |
|--------|-------------|----------|
| `api_key` | API key in header | Service-to-service |
| `jwt` | JWT token | User-facing |
| `mtls` | Mutual TLS | High-security |
| `hmac` | HMAC signature | Webhook-style |

### 3.2 Authentication Configuration

```yaml
authentication:
  methods:
    api_key:
      enabled: true
      header: "X-API-Key"
      validate: true
      
    jwt:
      enabled: true
      header: "Authorization"
      issuer: "https://auth.aida.dev"
      audience: "event-bus"
      
    mtls:
      enabled: false
      ca_cert: /etc/certs/ca.pem
      client_cert_required: true
      
    hmac:
      enabled: false
      secret_env: HMAC_SECRET
      algorithm: sha256
```

### 3.3 Authentication Flow

```
Event Published
    │
    ├── Extract credentials from event
    │
    ├── Method: api_key
    │   ├── Validate API key against database
    │   ├── Check key is active
    │   └── Return subscriber_id
    │
    ├── Method: jwt
    │   ├── Validate JWT signature
    │   ├── Check expiration
    │   ├── Validate claims
    │   └── Return user_id
    │
    ├── Method: mtls
    │   ├── Validate client certificate
    │   ├── Check CA chain
    │   └── Return certificate CN
    │
    └── Method: hmac
        ├── Calculate HMAC of payload
        ├── Compare with signature
        └── Return publisher_id
```

---

## 4. Authorization

### 4.1 Permission Model

```python
class EventPermission:
    # Topic-level permissions
    publish_topics: list[str]    # ["user.*", "task.created"]
    subscribe_topics: list[str]  # ["task.**", "ai.*"]
    
    # Event type permissions
    publish_types: list[str]     # ["user.message", "task.*"]
    subscribe_types: list[str]   # ["task.completed", "ai.*"]
    
    # Priority permissions
    max_publish_priority: int    # Can publish up to this priority
    min_subscribe_priority: int  # Can subscribe from this priority
```

### 4.2 Role-Based Access Control

```yaml
rbac:
  roles:
    admin:
      publish: ["**"]
      subscribe: ["**"]
      max_priority: 100
      
    service:
      publish: ["task.*", "agent.*", "ai.*"]
      subscribe: ["task.**", "agent.**", "ai.**"]
      max_priority: 80
      
    user:
      publish: ["user.*"]
      subscribe: ["ai.*", "task.*"]
      max_priority: 60
      
    readonly:
      publish: []
      subscribe: ["monitoring.*"]
      max_priority: 0
```

### 4.3 Authorization Check

```python
def authorize_publish(publisher: str, event: Event) -> bool:
    """Check if publisher can publish this event."""
    
    permissions = get_permissions(publisher)
    
    # Check topic permission
    if not any(topic_matches(event.topic, p) for p in permissions.publish_topics):
        return False
    
    # Check type permission
    if not any(type_matches(event.event_type, p) for p in permissions.publish_types):
        return False
    
    # Check priority permission
    if event.priority > permissions.max_publish_priority:
        return False
    
    return True

def authorize_subscribe(subscriber: str, topic: str) -> bool:
    """Check if subscriber can subscribe to this topic."""
    
    permissions = get_permissions(subscriber)
    
    # Check topic permission
    return any(topic_matches(topic, p) for p in permissions.subscribe_topics)
```

---

## 5. Validation

### 5.1 Schema Validation

```yaml
schema_validation:
  enabled: true
  strict_mode: false
  
  # JSON Schema for each event type
  schemas:
    user.message.sent:
      type: object
      required: [message_id, content]
      properties:
        message_id:
          type: string
          format: uuid
        content:
          type: string
          minLength: 1
          maxLength: 10000
          
    task.completed:
      type: object
      required: [task_type, duration_ms]
      properties:
        task_type:
          type: string
          enum: [coding, testing, research]
        duration_ms:
          type: integer
          minimum: 0
```

### 5.2 Payload Validation

```python
class PayloadValidator:
    def validate(self, event: Event) -> ValidationResult:
        errors = []
        
        # Size limit
        if len(json.dumps(event.payload)) > 1_000_000:  # 1MB
            errors.append("Payload too large")
        
        # Field validation
        for field, rules in self.field_rules.items():
            if field in event.payload:
                if not self.validate_field(event.payload[field], rules):
                    errors.append(f"Invalid field: {field}")
        
        # Custom validation
        for rule in self.custom_rules:
            if not rule.validate(event):
                errors.append(f"Custom rule failed: {rule.name}")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors
        )
```

---

## 6. Encryption

### 6.1 In-Transit Encryption

```yaml
tls:
  enabled: true
  
  # Server TLS
  server:
    cert: /etc/certs/server.pem
    key: /etc/certs/server-key.pem
    ca: /etc/certs/ca.pem
    
  # Client TLS (for mTLS)
  client:
    verify: true
    cert_required: true
    
  # TLS settings
  min_version: TLSv1.2
  ciphers:
    - TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
    - TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
```

### 6.2 Payload Encryption

```yaml
payload_encryption:
  enabled: false
  
  # Encryption algorithm
  algorithm: aes-256-gcm
  
  # Key management
  key_management:
    provider: env  # env | vault | aws_kms
    key_env: EVENT_ENCRYPTION_KEY
    
  # Fields to encrypt
  encrypt_fields:
    - "payload.sensitive_data"
    - "payload.user_email"
    - "payload.credit_card"
```

### 6.3 Event Signing

```yaml
event_signing:
  enabled: true
  
  # Signing algorithm
  algorithm: hmac-sha256
  
  # Key management
  key_management:
    provider: env
    key_env: EVENT_SIGNING_KEY
    
  # Signature header
  header: "X-Event-Signature"
```

---

## 7. Audit Trail

### 7.1 Audit Events

| Event | Description | Priority |
|-------|-------------|----------|
| `security.event.published` | Event published | 50 |
| `security.event.consumed` | Event consumed | 40 |
| `security.event.failed` | Event delivery failed | 70 |
| `security.auth.success` | Authentication success | 50 |
| `security.auth.failure` | Authentication failure | 80 |
| `security.authz.denied` | Authorization denied | 80 |
| `security.violation` | Security violation | 100 |

### 7.2 Audit Log Schema

```python
class AuditLog:
    timestamp: datetime
    event_id: UUID
    event_type: str
    
    # Actor
    actor_id: str
    actor_type: str  # user, service, system
    actor_ip: str
    
    # Action
    action: str  # publish, subscribe, consume
    topic: str
    success: bool
    error: Optional[str]
    
    # Context
    correlation_id: Optional[UUID]
    request_id: Optional[UUID]
    
    # Metadata
    metadata: dict
```

### 7.3 Audit Configuration

```yaml
audit:
  enabled: true
  
  # What to audit
  events:
    - publish
    - subscribe
    - consume
    - auth_success
    - auth_failure
    - authz_denied
    - violation
    
  # Storage
  storage:
    backend: postgresql
    table: event_audit_log
    retention: 90d
    
  # Tamper protection
  tamper_protection:
    enabled: true
    hash_chain: true
    hash_algorithm: sha256
```

---

## 8. Security Rules

### 8.1 Rate Limiting

```yaml
rate_limiting:
  enabled: true
  
  # Per publisher
  per_publisher:
    events_per_second: 100
    burst: 200
    
  # Per subscriber
  per_subscriber:
    events_per_second: 1000
    burst: 2000
    
  # Per topic
  per_topic:
    events_per_second: 10000
    burst: 20000
```

### 8.2 Content Filtering

```yaml
content_filtering:
  enabled: true
  
  # Block sensitive data
  sensitive_patterns:
    - pattern: "\\b\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}\\b"
      action: redact
      replacement: "[REDACTED_CARD]"
      
    - pattern: "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b"
      action: redact
      replacement: "[REDACTED_EMAIL]"
      
  # Block malicious content
  malicious_patterns:
    - pattern: "<script.*?>.*?</script>"
      action: block
      
    - pattern: "javascript:"
      action: block
```

---

## 9. Configuration

```yaml
security:
  # Authentication
  authentication:
    enabled: true
    methods: [api_key, jwt]
    required: true
    
  # Authorization
  authorization:
    enabled: true
    rbac_enabled: true
    default_role: readonly
    
  # Validation
  validation:
    schema: true
    payload: true
    max_payload_size: 1MB
    
  # Encryption
  encryption:
    tls: true
    payload: false
    signing: true
    
  # Audit
  audit:
    enabled: true
    retention: 90d
    tamper_protection: true
    
  # Rate limiting
  rate_limiting:
    enabled: true
    events_per_second: 100
    
  # Content filtering
  content_filtering:
    enabled: true
    redact_pii: true
    block_malicious: true
```
