# -*- coding: utf-8 -*-
"""
AIDA Web Search RAG Assistant Test
===================================
1. Murakkab qidiruv talab qiladigan topshiriq yuboradi.
2. engine.py avtomatik ravishda search_helper.py orqali internetdan ma'lumot qidiradi.
3. Ma'lumotlarni modelga (Gemini yoki local Ollama) beradi.
4. Natijani tekshiradi.
"""
import urllib.request, json, time

URL = "http://127.0.0.1:8001/api/si"
TOKEN = "aida-super-secure-token-2026"

def post(path, data):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        f"{URL}{path}", data=body,
        headers={"Content-Type": "application/json", "X-AIDA-Security-Token": TOKEN},
        method="POST"
    )
    resp = urllib.request.urlopen(req, timeout=30)
    return json.loads(resp.read().decode())

def get(path):
    req = urllib.request.Request(
        f"{URL}{path}",
        headers={"X-AIDA-Security-Token": TOKEN},
        method="GET"
    )
    resp = urllib.request.urlopen(req, timeout=30)
    return json.loads(resp.read().decode())

print("=" * 60)
print("AIDA WEB SEARCH RAG ASSISTANT TEST")
print("=" * 60)

# Topshiriq yuboramiz
print("\n[1] Murakkab topshiriq yuborilmoqda (Internet qidiruv faollashadi)...")
task_data = {
    "user_request": "O'zbekistonning eng oxirgi texnologik yangiliklari va sun'iy intellekt sohasidagi loyihalar haqida qisqacha ma'lumot ber.",
    "goal": "Eng so'nggi ma'lumotlarni internetdan qidirib topib tahlil qilish.",
    "domain": "knowledge",
    "difficulty": 7
}
task_resp = post("/tasks/", task_data)
task_id = task_resp["task_id"]
print(f"  Topshiriq ID: {task_id}")
print("  Internetdan qidirish va AI javobi kutilmoqda (25 soniya)...")
time.sleep(25)

# Natija olish
print("\n[2] Natijani tekshirish...")
result = get(f"/tasks/{task_id}/")
print(f"  Topshiriq Statusi: {result['status']}")

if result.get("executions"):
    ex = result["executions"][0]
    ev = ex.get("evaluation") or {}
    print(f"  Bajaruvchi Model:  {ex['model']}")
    print(f"  Baho:             {ev.get('score', 0):.3f}")
    print("\n  [KOD / MATN JAVOBI]:")
    print("-" * 60)
    print(ex['output'][:800])
    print("-" * 60)
else:
    print("  XATO: Bajarilish tafsilotlari topilmadi!")

print("\n" + "=" * 60)
