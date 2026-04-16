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
