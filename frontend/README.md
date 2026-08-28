# AIDA Frontend

Vite + React frontend for AIDA OS.

## Run (development)

```bash
cd frontend
npm install
npm run dev
```

Opens on `http://localhost:3000`. API requests proxy to backend at `http://127.0.0.1:8001`.

## Build

```bash
npm run build
```

Output goes to `../dist/` (root level) for Django to serve in production.

## Backend

Run the Django backend separately from project root:

```bash
python manage.py runserver 127.0.0.1:8001
```
