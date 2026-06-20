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
