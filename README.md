<<<<<<< HEAD
# AIDA Django + Frontend

Ushbu repo endi `AIDA` nomli Django project bilan ishlaydi. Frontend build tayyor bo'lsa, Django avtomatik ravishda `dist/index.html` va `dist/assets` ni serve qiladi.

## Backend ishga tushirish

1. `python -m venv .venv`
2. `.venv\Scripts\python -m pip install -r requirements.txt`
3. `.env.example` dan `.env` yarating
4. `.venv\Scripts\python manage.py migrate`
5. `.venv\Scripts\python manage.py runserver`

Server odatda `http://127.0.0.1:8000` da ochiladi.

## AIDA provider sozlamasi

`.env` ichida:

`AIDA_PROVIDER=local` bo'lsa, AIDA `AIDA Local Core` rejimida ishlaydi.

Serverning `runserver` manzili eslab qolinadi. Masalan:

1. `py manage.py runserver 127.0.0.1:8080`
2. Keyingi safar oddiy `py manage.py runserver`
3. Server yana `127.0.0.1:8080` da ochiladi

## Access keylar

Sayt ichida access key yaratish mumkin. Ular boshqa platformalardan quyidagi endpointga ulanish uchun ishlatiladi:

`POST /api/platform/chat/`

Header:

`X-AIDA-Key: your_secret_key`

Body:

`{"prompt":"Salom AIDA"}`

Access key yaratishda quyidagi profil maydonlarini ham berish mumkin:

`platform_name`

`business_type`

`audience`

`tone`

`assistant_goal`

`custom_instructions`

Masalan `business_type=kiyim do'koni` bo'lsa, AIDA javoblari mahsulot, o'lcham, uslub va mijozni xaridga olib borish oqimiga moslashadi.

Platforma chat endpointi qo'shimcha runtime kontekst ham qabul qiladi:

`page`

`customer_intent`

`locale`

## Real server

Deploy paytida `.env` ichida quyidagilarni to'ldirish tavsiya qilinadi:

`DJANGO_ALLOWED_HOSTS=your-domain.com,www.your-domain.com`

`DJANGO_CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com`

`DJANGO_SECURE_PROXY_SSL_HEADER=true`

## Frontend build

Frontend avvalgi `Vite + React` asosida qolgan. Build qilish uchun:

1. `npm install`
2. `npm run build`

Build tugagach, Django shu tayyor frontendni serve qiladi.

## CLI controller

Webdan tashqari alohida terminal interfeys ham bor:

`.venv\Scripts\python aida_master_controller.py`
=======
# AIDA Agent OS

Bu loyiha endi oddiy sci-fi interfeys emas, balki persistent xotira, internet research va learning qatlami bor assistantga aylantirildi.

## Nima qo'shildi

- Express backend orqali `AIDA API`
- JSON asosidagi uzoq muddatli memory store
- `learn <mavzu>` yoki `o'rgan <mavzu>` orqali yangi bilim yozish
- `research <mavzu>` yoki `izla <mavzu>` orqali internetdan qidirish
- Javob berishda oldingi xotira va bilimlardan retrieval
- Ixtiyoriy `auto-learn` sikli
- Default holatda API keysiz ishlaydigan lokal/offline kognitiv rejim
- DuckDuckGo HTML search + Wikipedia orqali ochiq internet research
- Ixtiyoriy lokal `Ollama` modeli bilan API keysiz kuchliroq synthesis
- Tashqi servis yoqilsa Pollinations ishlaydi, ishlamasa lokal fallback javobi qaytadi

## Ishga tushirish

**Talablar:** Node.js

1. `npm install`
2. `.env.example` asosida `.env.local` yoki `.env` yarating
3. Backendni ishga tushiring:
   `npm run server`
4. Yangi terminalda frontendni ishga tushiring:
   `npm run dev`

Frontend `http://localhost:3000`, backend esa odatda `http://localhost:8787` da ishlaydi.

## Muhim buyruqlar

- Chat oynasida: `o'rgan matematika`
- Chat oynasida: `izla suniy intellekt`
- Terminal oynasida: `learn suniy intellekt`
- Terminal oynasida: `research kvant fizika`
- Terminal oynasida: `memory.status`

## Konfiguratsiya

- `AIDA_API_PORT`: backend porti
- `AIDA_MEMORY_FILE`: memory JSON fayli
- `AIDA_AUTO_LEARN`: `true` bo'lsa fon rejimida bilim yig'adi
- `AIDA_OFFLINE_ONLY`: `true` bo'lsa tashqi LLMsiz ishlaydi
- `AIDA_ALLOW_WEB_RESEARCH`: `true` bo'lsa ochiq internet qidiruvi yoqiladi
- `AIDA_AUTO_LEARN_INTERVAL_MINUTES`: auto-learn oralig'i
- `AIDA_AUTO_LEARN_TOPICS`: vergul bilan ajratilgan mavzular
- `AIDA_LLM_TIMEOUT_MS`: tashqi LLM kutish vaqti
- `AIDA_OLLAMA_MODEL`: lokal model nomi
- `AIDA_OLLAMA_URL`: lokal Ollama server manzili

## Eslatma

Bu versiya xavfsizroq yo'nalishda ishlab chiqildi: persistent xotira, research va learning qo'shildi, lekin zararli yashirin ijro yoki o'zini kod darajasida nazoratsiz o'zgartirish kuchaytirilmadi.
# AIDA1
>>>>>>> b051280dea8d539a47236a4d85212f3580c11b5a
