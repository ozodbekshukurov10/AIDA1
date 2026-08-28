# AIDA Enterprise API Foundation
## Endpoint Catalog

**Versiya:** 1.0.0
**Sana:** 2026-07-03
**Muallif:** AIDA API Team

---

## 1. AUTHENTICATION MODULE `/api/v1/auth/`

| Method | Endpoint | Tavsif | Auth |
|--------|----------|--------|------|
| POST | `/api/v1/auth/register/` | Ro'yxatdan o'tish | Public |
| POST | `/api/v1/auth/login/` | Login (email+password) | Public |
| POST | `/api/v1/auth/logout/` | Logout, token revoke | JWT |
| POST | `/api/v1/auth/token/refresh/` | Access token yangilash | Refresh token |
| POST | `/api/v1/auth/token/verify/` | Token validligini tekshirish | — |
| POST | `/api/v1/auth/password/reset/` | Parol tiklash so'rovi | Public |
| POST | `/api/v1/auth/password/reset/confirm/` | Yangi parol o'rnatish | Reset token |
| POST | `/api/v1/auth/password/change/` | Parol o'zgartirish | JWT |
| POST | `/api/v1/auth/email/verify/` | Email tasdiqlash | JWT |
| POST | `/api/v1/auth/email/resend/` | Tasdiqlash emailini qayta yuborish | JWT |
| GET | `/api/v1/auth/oauth2/{provider}/` | OAuth2 redirect (github, google) | Public |
| GET | `/api/v1/auth/oauth2/{provider}/callback/` | OAuth2 callback | Public |
| GET | `/api/v1/auth/me/` | Joriy foydalanuvchi ma'lumoti | JWT |
| POST | `/api/v1/auth/mfa/enable/` | 2FA yoqish | JWT |
| POST | `/api/v1/auth/mfa/disable/` | 2FA o'chirish | JWT |
| POST | `/api/v1/auth/mfa/verify/` | 2FA kod tekshirish | JWT |

---

## 2. USERS MODULE `/api/v1/users/`

| Method | Endpoint | Tavsif | Auth |
|--------|----------|--------|------|
| GET | `/api/v1/users/` | Foydalanuvchilar ro'yxati | Admin |
| GET | `/api/v1/users/{id}/` | Foydalanuvchi profili | JWT |
| PUT | `/api/v1/users/{id}/` | Profilni to'liq yangilash | JWT (o'zi) |
| PATCH | `/api/v1/users/{id}/` | Profilni qisman yangilash | JWT (o'zi) |
| DELETE | `/api/v1/users/{id}/` | Hisobni o'chirish | JWT (o'zi) |
| GET | `/api/v1/users/{id}/profile/` | Kengaytirilgan profil | JWT |
| PATCH | `/api/v1/users/{id}/profile/` | Profilni yangilash | JWT (o'zi) |
| GET | `/api/v1/users/{id}/sessions/` | Aktiv sessionlar | JWT (o'zi) |
| DELETE | `/api/v1/users/{id}/sessions/{sid}/` | Sessionni tugatish | JWT (o'zi) |
| GET | `/api/v1/users/{id}/api-keys/` | API kalitlar ro'yxati | JWT (o'zi) |
| POST | `/api/v1/users/{id}/api-keys/` | Yangi API kalit | JWT (o'zi) |
| DELETE | `/api/v1/users/{id}/api-keys/{kid}/` | API kalitni bekor qilish | JWT (o'zi) |
| GET | `/api/v1/users/{id}/activity/` | Faollik tarixi | JWT (o'zi) |
| POST | `/api/v1/users/{id}/avatar/` | Avatar yuklash | JWT (o'zi) |
| DELETE | `/api/v1/users/{id}/avatar/` | Avatarni o'chirish | JWT (o'zi) |

---

## 3. ORGANIZATIONS MODULE `/api/v1/orgs/`

| Method | Endpoint | Tavsif | Auth |
|--------|----------|--------|------|
| GET | `/api/v1/orgs/` | Foydalanuvchi orglari | JWT |
| POST | `/api/v1/orgs/` | Yangi org yaratish | JWT |
| GET | `/api/v1/orgs/{slug}/` | Org ma'lumoti | JWT + member |
| PUT | `/api/v1/orgs/{slug}/` | Orgni yangilash | JWT + admin |
| PATCH | `/api/v1/orgs/{slug}/` | Qisman yangilash | JWT + admin |
| DELETE | `/api/v1/orgs/{slug}/` | Orgni o'chirish | JWT + owner |
| GET | `/api/v1/orgs/{slug}/members/` | A'zolar ro'yxati | JWT + member |
| POST | `/api/v1/orgs/{slug}/members/` | A'zo taklif qilish | JWT + admin |
| PATCH | `/api/v1/orgs/{slug}/members/{uid}/` | A'zo rolini o'zgartirish | JWT + admin |
| DELETE | `/api/v1/orgs/{slug}/members/{uid}/` | A'zoni chiqarish | JWT + admin |
| GET | `/api/v1/orgs/{slug}/settings/` | Org sozlamalari | JWT + admin |
| PATCH | `/api/v1/orgs/{slug}/settings/` | Sozlamalarni yangilash | JWT + admin |
| GET | `/api/v1/orgs/{slug}/usage/` | Resurs ishlatilishi | JWT + admin |
| GET | `/api/v1/orgs/{slug}/billing/` | To'lov ma'lumotlari | JWT + owner |

---

## 4. PROJECTS MODULE `/api/v1/projects/`

| Method | Endpoint | Tavsif | Auth |
|--------|----------|--------|------|
| GET | `/api/v1/projects/` | Loyihalar ro'yxati | JWT |
| POST | `/api/v1/projects/` | Yangi loyiha | JWT |
| GET | `/api/v1/projects/{id}/` | Loyiha ma'lumoti | JWT + member |
| PUT | `/api/v1/projects/{id}/` | Loyihani yangilash | JWT + admin |
| PATCH | `/api/v1/projects/{id}/` | Qisman yangilash | JWT + admin |
| DELETE | `/api/v1/projects/{id}/` | Loyihani o'chirish | JWT + admin |
| GET | `/api/v1/projects/{id}/members/` | A'zolar | JWT + member |
| POST | `/api/v1/projects/{id}/members/` | A'zo qo'shish | JWT + admin |
| DELETE | `/api/v1/projects/{id}/members/{uid}/` | A'zo chiqarish | JWT + admin |
| GET | `/api/v1/projects/{id}/settings/` | Sozlamalar | JWT + admin |
| PATCH | `/api/v1/projects/{id}/settings/` | Sozlama yangilash | JWT + admin |
| GET | `/api/v1/projects/{id}/stats/` | Statistika | JWT + member |
| POST | `/api/v1/projects/{id}/archive/` | Arxivlash | JWT + admin |
| POST | `/api/v1/projects/{id}/restore/` | Arxivdan qaytarish | JWT + admin |

---

## 5. REPOSITORIES MODULE `/api/v1/repositories/`

| Method | Endpoint | Tavsif | Auth |
|--------|----------|--------|------|
| GET | `/api/v1/repositories/` | Repolar ro'yxati | JWT |
| POST | `/api/v1/repositories/` | Repo qo'shish | JWT |
| GET | `/api/v1/repositories/{id}/` | Repo ma'lumoti | JWT + member |
| PUT | `/api/v1/repositories/{id}/` | Yangilash | JWT + admin |
| DELETE | `/api/v1/repositories/{id}/` | O'chirish | JWT + admin |
| POST | `/api/v1/repositories/{id}/sync/` | GitHub'dan sinxronizatsiya | JWT |
| GET | `/api/v1/repositories/{id}/status/` | Sinxronizatsiya holati | JWT |
| GET | `/api/v1/repositories/{id}/tree/` | Fayl daraxti | JWT |
| GET | `/api/v1/repositories/{id}/file/` | Fayl tarkibi | JWT |
| POST | `/api/v1/repositories/{id}/analyze/` | Kod tahlili | JWT |
| GET | `/api/v1/repositories/{id}/analysis/` | Tahlil natijalari | JWT |

---

## 6. CHATS MODULE `/api/v1/chats/`

| Method | Endpoint | Tavsif | Auth |
|--------|----------|--------|------|
| GET | `/api/v1/chats/` | Chatlar ro'yxati | JWT |
| POST | `/api/v1/chats/` | Yangi chat | JWT |
| GET | `/api/v1/chats/{id}/` | Chat ma'lumoti | JWT + owner |
| PUT | `/api/v1/chats/{id}/` | Yangilash | JWT + owner |
| PATCH | `/api/v1/chats/{id}/` | Qisman yangilash | JWT + owner |
| DELETE | `/api/v1/chats/{id}/` | O'chirish | JWT + owner |
| POST | `/api/v1/chats/{id}/archive/` | Arxivlash | JWT + owner |
| POST | `/api/v1/chats/{id}/pin/` | Muhimlash | JWT + owner |
| GET | `/api/v1/chats/{id}/export/` | Export (JSON/Markdown) | JWT + owner |
| POST | `/api/v1/chats/{id}/branch/` | Chat'dan branch yaratish | JWT + owner |

---

## 7. MESSAGES MODULE `/api/v1/chats/{id}/messages/`

| Method | Endpoint | Tavsif | Auth |
|--------|----------|--------|------|
| GET | `/api/v1/chats/{id}/messages/` | Xabarlar (paginated) | JWT + owner |
| POST | `/api/v1/chats/{id}/messages/` | Yangi xabar + AI javob | JWT + owner |
| GET | `/api/v1/chats/{id}/messages/{mid}/` | Xabar ma'lumoti | JWT + owner |
| DELETE | `/api/v1/chats/{id}/messages/{mid}/` | Xabarni o'chirish | JWT + owner |
| POST | `/api/v1/chats/{id}/messages/{mid}/regenerate/` | Qayta generatsiya | JWT + owner |
| POST | `/api/v1/chats/{id}/messages/stream/` | **Streaming** AI javob (SSE) | JWT + owner |
| DELETE | `/api/v1/chats/{id}/messages/stream/{stream_id}/` | Streamni bekor qilish | JWT + owner |

> **Note:** `POST /messages/stream/` → `text/event-stream` response qaytaradi. Batafsil Streaming_API.md da.

---

## 8. AI MODELS MODULE `/api/v1/models/`

| Method | Endpoint | Tavsif | Auth |
|--------|----------|--------|------|
| GET | `/api/v1/models/` | Barcha modellar | JWT |
| GET | `/api/v1/models/{slug}/` | Model ma'lumoti | JWT |
| POST | `/api/v1/models/{slug}/test/` | Model test qilish | JWT |
| GET | `/api/v1/models/{slug}/pricing/` | Narx ma'lumoti | JWT |
| GET | `/api/v1/models/compare/` | Modellarni solishtirish | JWT |

---

## 9. PROVIDERS MODULE `/api/v1/providers/`

| Method | Endpoint | Tavsif | Auth |
|--------|----------|--------|------|
| GET | `/api/v1/providers/` | Provayderlar ro'yxati | JWT |
| POST | `/api/v1/providers/` | Yangi provayder | Admin |
| GET | `/api/v1/providers/{slug}/` | Provayder ma'lumoti | JWT |
| PATCH | `/api/v1/providers/{slug}/` | Yangilash | Admin |
| GET | `/api/v1/providers/{slug}/health/` | Provayder holati | JWT |
| GET | `/api/v1/providers/{slug}/models/` | Provayder modellari | JWT |

---

## 10. AGENTS MODULE `/api/v1/agents/`

| Method | Endpoint | Tavsif | Auth |
|--------|----------|--------|------|
| GET | `/api/v1/agents/` | Agentlar ro'yxati | JWT |
| POST | `/api/v1/agents/` | Yangi agent | JWT |
| GET | `/api/v1/agents/{id}/` | Agent ma'lumoti | JWT |
| PUT | `/api/v1/agents/{id}/` | Yangilash | JWT + owner |
| PATCH | `/api/v1/agents/{id}/` | Qisman yangilash | JWT + owner |
| DELETE | `/api/v1/agents/{id}/` | O'chirish | JWT + owner |
| POST | `/api/v1/agents/{id}/run/` | Agentni ishga tushirish | JWT |
| POST | `/api/v1/agents/{id}/stop/` | Agentni to'xtatish | JWT |
| GET | `/api/v1/agents/{id}/status/` | Joriy holat | JWT |
| GET | `/api/v1/agents/{id}/tasks/` | Agent tasklari | JWT |
| GET | `/api/v1/agents/{id}/tools/` | Agent toolllari | JWT |
| POST | `/api/v1/agents/{id}/tools/` | Tool qo'shish | JWT + owner |
| DELETE | `/api/v1/agents/{id}/tools/{tid}/` | Toolni olib tashlash | JWT + owner |
| GET | `/api/v1/agents/{id}/logs/` | Agent loglari | JWT |

---

## 11. TASKS MODULE `/api/v1/tasks/`

| Method | Endpoint | Tavsif | Auth |
|--------|----------|--------|------|
| GET | `/api/v1/tasks/` | Tasklar ro'yxati | JWT |
| POST | `/api/v1/tasks/` | Yangi task yaratish | JWT |
| GET | `/api/v1/tasks/{id}/` | Task ma'lumoti | JWT |
| DELETE | `/api/v1/tasks/{id}/` | Taskni bekor qilish | JWT |
| POST | `/api/v1/tasks/{id}/retry/` | Qayta urinish | JWT |
| GET | `/api/v1/tasks/{id}/result/` | Task natijasi | JWT |
| GET | `/api/v1/tasks/{id}/logs/` | Task loglari | JWT |

---

## 12. WORKFLOWS MODULE `/api/v1/workflows/`

| Method | Endpoint | Tavsif | Auth |
|--------|----------|--------|------|
| GET | `/api/v1/workflows/` | Workflowlar ro'yxati | JWT |
| POST | `/api/v1/workflows/` | Yangi workflow | JWT |
| GET | `/api/v1/workflows/{id}/` | Workflow ma'lumoti | JWT |
| PUT | `/api/v1/workflows/{id}/` | Yangilash | JWT + owner |
| DELETE | `/api/v1/workflows/{id}/` | O'chirish | JWT + owner |
| POST | `/api/v1/workflows/{id}/run/` | Ishga tushirish | JWT |
| POST | `/api/v1/workflows/{id}/stop/` | To'xtatish | JWT |
| GET | `/api/v1/workflows/{id}/runs/` | Run tarixi | JWT |
| GET | `/api/v1/workflows/{id}/runs/{rid}/` | Run ma'lumoti | JWT |

---

## 13. KNOWLEDGE MODULE `/api/v1/knowledge/`

| Method | Endpoint | Tavsif | Auth |
|--------|----------|--------|------|
| GET | `/api/v1/knowledge/` | Knowledge ro'yxati | JWT |
| POST | `/api/v1/knowledge/` | Yangi knowledge qo'shish | JWT |
| GET | `/api/v1/knowledge/{id}/` | Knowledge ma'lumoti | JWT |
| PUT | `/api/v1/knowledge/{id}/` | Yangilash | JWT + owner |
| DELETE | `/api/v1/knowledge/{id}/` | O'chirish | JWT + owner |
| POST | `/api/v1/knowledge/{id}/index/` | Vektorlashtirish | JWT |
| GET | `/api/v1/knowledge/{id}/status/` | Indekslash holati | JWT |
| GET | `/api/v1/knowledge/{id}/chunks/` | Chunk ko'rish | JWT |
| POST | `/api/v1/knowledge/search/` | Semantik qidiruv | JWT |

---

## 14. RAG MODULE `/api/v1/rag/`

| Method | Endpoint | Tavsif | Auth |
|--------|----------|--------|------|
| POST | `/api/v1/rag/query/` | RAG so'rovi | JWT |
| POST | `/api/v1/rag/query/stream/` | Streaming RAG (SSE) | JWT |
| GET | `/api/v1/rag/sources/` | Manba hujjatlari | JWT |
| POST | `/api/v1/rag/rerank/` | Natijalarni qayta tartiblash | JWT |

---

## 15. EMBEDDINGS MODULE `/api/v1/embeddings/`

| Method | Endpoint | Tavsif | Auth |
|--------|----------|--------|------|
| POST | `/api/v1/embeddings/create/` | Matn uchun vektor yaratish | JWT |
| POST | `/api/v1/embeddings/search/` | Vektor qidiruv | JWT |
| POST | `/api/v1/embeddings/similarity/` | O'xshashlik hisoblash | JWT |

---

## 16. MEMORY MODULE `/api/v1/memory/`

| Method | Endpoint | Tavsif | Auth |
|--------|----------|--------|------|
| GET | `/api/v1/memory/` | Memory ro'yxati | JWT |
| POST | `/api/v1/memory/` | Memory yozish | JWT |
| GET | `/api/v1/memory/{id}/` | Memory o'qish | JWT |
| DELETE | `/api/v1/memory/{id}/` | Memory o'chirish | JWT |
| POST | `/api/v1/memory/search/` | Memory qidiruv | JWT |
| DELETE | `/api/v1/memory/clear/` | Barcha memory tozalash | JWT |

---

## 17. PLUGINS MODULE `/api/v1/plugins/`

| Method | Endpoint | Tavsif | Auth |
|--------|----------|--------|------|
| GET | `/api/v1/plugins/` | O'rnatilgan pluginlar | JWT |
| GET | `/api/v1/plugins/marketplace/` | Mavjud pluginlar | JWT |
| POST | `/api/v1/plugins/install/` | Plugin o'rnatish | Admin |
| DELETE | `/api/v1/plugins/{id}/` | Plugin o'chirish | Admin |
| POST | `/api/v1/plugins/{id}/enable/` | Yoqish | Admin |
| POST | `/api/v1/plugins/{id}/disable/` | O'chirish | Admin |
| GET | `/api/v1/plugins/{id}/` | Plugin ma'lumoti | JWT |
| GET | `/api/v1/plugins/{id}/tools/` | Plugin toollari | JWT |
| PATCH | `/api/v1/plugins/{id}/config/` | Plugin konfiguratsiyasi | Admin |
| GET | `/api/v1/plugins/{id}/permissions/` | Ruxsatlar | JWT |
| GET | `/api/v1/plugins/{id}/logs/` | Plugin loglari | Admin |

---

## 18. FILES MODULE `/api/v1/files/`

| Method | Endpoint | Tavsif | Auth |
|--------|----------|--------|------|
| POST | `/api/v1/files/upload/` | Fayl yuklash (multipart) | JWT |
| POST | `/api/v1/files/upload/chunked/initiate/` | Chunked upload boshlash | JWT |
| POST | `/api/v1/files/upload/chunked/{upload_id}/` | Chunk yuborish | JWT |
| POST | `/api/v1/files/upload/chunked/{upload_id}/complete/` | Uploadni yakunlash | JWT |
| GET | `/api/v1/files/{id}/` | Fayl metadata | JWT |
| GET | `/api/v1/files/{id}/download/` | Fayl yuklash | JWT |
| DELETE | `/api/v1/files/{id}/` | Faylni o'chirish | JWT + owner |

---

## 19. TOOL MODULES

### Terminal `/api/v1/terminal/`
| Method | Endpoint | Tavsif | Auth |
|--------|----------|--------|------|
| POST | `/api/v1/terminal/sessions/` | Terminal sessiya ochish | JWT |
| DELETE | `/api/v1/terminal/sessions/{id}/` | Sessiya yopish | JWT |
| POST | `/api/v1/terminal/execute/` | Buyruq bajarish | JWT |

### Python Sandbox `/api/v1/sandbox/python/`
| Method | Endpoint | Tavsif | Auth |
|--------|----------|--------|------|
| POST | `/api/v1/sandbox/python/execute/` | Python kodni bajarish | JWT |
| GET | `/api/v1/sandbox/python/sessions/{id}/` | Sessiya holati | JWT |
| DELETE | `/api/v1/sandbox/python/sessions/{id}/` | Sessiayani o'chirish | JWT |

### Browser `/api/v1/browser/`
| Method | Endpoint | Tavsif | Auth |
|--------|----------|--------|------|
| POST | `/api/v1/browser/navigate/` | URL'ga o'tish | JWT |
| POST | `/api/v1/browser/screenshot/` | Screenshot olish | JWT |
| POST | `/api/v1/browser/extract/` | Sahifadan matn olish | JWT |

---

## 20. GIT & GITHUB MODULES

### Git `/api/v1/git/`
| Method | Endpoint | Tavsif | Auth |
|--------|----------|--------|------|
| POST | `/api/v1/git/clone/` | Repo klonlash | JWT |
| GET | `/api/v1/git/{repo_id}/log/` | Commit tarixi | JWT |
| GET | `/api/v1/git/{repo_id}/diff/` | Diff ko'rish | JWT |
| GET | `/api/v1/git/{repo_id}/branches/` | Branch ro'yxati | JWT |

### GitHub `/api/v1/github/`
| Method | Endpoint | Tavsif | Auth |
|--------|----------|--------|------|
| GET | `/api/v1/github/repos/` | GitHub repolar | JWT + GH OAuth |
| POST | `/api/v1/github/repos/import/` | Repo import | JWT + GH OAuth |
| POST | `/api/v1/github/webhooks/` | Webhook endpoint | GitHub signature |

---

## 21. CONFIGURATION MODULE `/api/v1/config/`

| Method | Endpoint | Tavsif | Auth |
|--------|----------|--------|------|
| GET | `/api/v1/config/` | Sozlamalar ro'yxati | JWT |
| GET | `/api/v1/config/{key}/` | Bitta sozlama | JWT |
| PUT | `/api/v1/config/{key}/` | Sozlamani o'rnatish | JWT + scope |
| DELETE | `/api/v1/config/{key}/` | Sozlamani o'chirish | JWT + scope |

---

## 22. MONITORING MODULE `/api/v1/monitoring/`

| Method | Endpoint | Tavsif | Auth |
|--------|----------|--------|------|
| GET | `/api/v1/monitoring/status/` | Tizim holati | JWT |
| GET | `/api/v1/monitoring/metrics/` | Asosiy metrikalar | Admin |
| GET | `/api/v1/monitoring/agents/` | Agent statistikasi | Admin |
| GET | `/api/v1/monitoring/models/` | Model statistikasi | JWT |

---

## 23. PUBLIC ENDPOINTS `/api/public/`

| Method | Endpoint | Tavsif | Auth |
|--------|----------|--------|------|
| GET | `/api/public/models/` | Ochiq modellar ro'yxati | Public |
| GET | `/api/public/status/` | Tizim statusi | Public |
| GET | `/api/public/version/` | API versiyasi | Public |

---

## 24. PLATFORM API `/api/platform/`

| Method | Endpoint | Tavsif | Auth |
|--------|----------|--------|------|
| POST | `/api/platform/chat/` | Tashqi platforma chat | API Key |
| POST | `/api/platform/chat/stream/` | Streaming chat | API Key |

---

## 25. HEALTH ENDPOINTS

| Method | Endpoint | Tavsif | Auth |
|--------|----------|--------|------|
| GET | `/api/health/` | Liveness probe | Public |
| GET | `/api/health/ready/` | Readiness probe | Public |
| GET | `/api/health/detailed/` | Batafsil holat | Admin |

---

## ENDPOINT STATISTIKASI

```
Jami endpoint'lar:  ~130+ ta
Authentication:      16
Users:               15
Organizations:       14
Projects:            14
Repositories:        11
Chats:               10
Messages:             7
AI Models:            5
Providers:            6
Agents:              13
Tasks:                7
Workflows:            9
Knowledge:            9
RAG:                  4
Embeddings:           3
Memory:               6
Plugins:             11
Files:                7
Tool Modules:        10
Git/GitHub:           8
Configuration:        4
Monitoring:           4
Public:               3
Platform:             2
Health:               3
```

---

*Hujjat AIDA Development Bible — Book 1, Chapter 9 asosida tayyorlangan.*
