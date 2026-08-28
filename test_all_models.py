"""
AIDA - Barcha modellar va AIDA Beta test skripti
Sana: 2026-07-03
"""
import json
import time
import urllib.request
import urllib.error
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

PROVIDERS = [
    "ollama",
    "openai",
    "anthropic",
    "gemini",
    "deepseek",
    "lm_studio",
    "vllm",
    "tensorrt-llm",
    "aida_model",
    "local",
]

TEST_PROMPTS = [
    {
        "id": "salom",
        "name": "Salom va tanishuv",
        "prompt": "Salom! Sen kimsan?",
    },
    {
        "id": "kod",
        "name": "Kod yozish",
        "prompt": "Python da ikki sonni qo'shuvchi funksiya yoz.",
    },
    {
        "id": "mantiq",
        "name": "Mantiqiy savol",
        "prompt": "1 dan 5 gacha sonlarning yig'indisi necha?",
    },
]

results = []


def post_json(url, data, headers=None):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            **(headers or {}),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8"))
        except Exception:
            return e.code, {"error": str(e)}
    except Exception as e:
        return 0, {"error": str(e)}


def get_json(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8"))
        except Exception:
            return e.code, {"error": str(e)}
    except Exception as e:
        return 0, {"error": str(e)}


def print_separator(char="-", width=60):
    print(char * width)


def status_icon(ok):
    return "[OK]" if ok else "[FAIL]"



# ──────────────────────────────────────────────
# 1. Server va gateway holati
# ──────────────────────────────────────────────

def test_server_status():
    print("\n" + "═" * 60)
    print("  1. SERVER VA GATEWAY HOLATI")
    print("═" * 60)

    code, data = get_json(f"{BASE_URL}/api/status/")
    ok = code == 200 and data.get("status") == "ok"
    print(f"  /api/status/          {status_icon(ok)}  HTTP {code}")
    if ok:
        print(f"    Platform   : {data.get('platform')}")
        print(f"    Version    : {data.get('version')}")
        print(f"    Active     : {data.get('active_provider')}")
        providers_info = data.get("providers", {})
        print(f"    Providers  : {list(providers_info.keys())}")
    results.append({
        "section": "server_status",
        "ok": ok,
        "http": code,
        "data": data,
    })

    code2, data2 = get_json(f"{BASE_URL}/api/v2/gateway/")
    ok2 = code2 == 200
    print(f"  /api/v2/gateway/      {status_icon(ok2)}  HTTP {code2}")
    if ok2:
        print(f"    Active     : {data2.get('active_provider')}")
        print(f"    Total      : {data2.get('total_providers')}")
        print(f"    Fallback   : {data2.get('fallback_order')}")
    results.append({
        "section": "gateway_status",
        "ok": ok2,
        "http": code2,
        "data": data2,
    })

    return ok


# ──────────────────────────────────────────────
# 2. Provider health check
# ──────────────────────────────────────────────

def test_provider_health():
    print("\n" + "═" * 60)
    print("  2. PROVIDER HEALTH CHECK")
    print("═" * 60)

    code, data = get_json(f"{BASE_URL}/api/v2/gateway/health/")
    ok = code == 200
    print(f"  /api/v2/gateway/health/  {status_icon(ok)}  HTTP {code}")

    health_results = {}
    if ok and isinstance(data, dict):
        for provider, healthy in data.items():
            icon = "🟢" if healthy else "🔴"
            print(f"    {icon}  {provider:<20} {'ONLINE' if healthy else 'OFFLINE'}")
            health_results[provider] = healthy
    elif not ok:
        print(f"    Xato: {data.get('error', data)}")

    results.append({
        "section": "provider_health",
        "ok": ok,
        "http": code,
        "health": health_results,
    })
    return health_results



# ──────────────────────────────────────────────
# 3. Har bir provider bilan chat testi
# ──────────────────────────────────────────────

def test_chat_with_provider(provider_name):
    print(f"\n  Provider: [{provider_name}]")
    print_separator("-", 50)

    provider_results = []
    for pt in TEST_PROMPTS:
        payload = {
            "message": pt["prompt"],
            "provider": provider_name,
        }
        t0 = time.time()
        code, data = post_json(f"{BASE_URL}/api/chat/", payload)
        elapsed_ms = int((time.time() - t0) * 1000)

        ok = code == 200 and bool(data.get("response") or data.get("message"))
        resp_text = data.get("response") or data.get("message") or data.get("error", "")
        short = resp_text[:80].replace("\n", " ") if resp_text else ""

        icon = "✅" if ok else "❌"
        print(f"    {icon} [{pt['name']}]  {elapsed_ms}ms")
        if ok:
            print(f"       Javob: {short}...")
            print(f"       Model: {data.get('model','')} | Provider: {data.get('provider','')}")
        else:
            print(f"       Xato : {short}")

        provider_results.append({
            "provider": provider_name,
            "test_id": pt["id"],
            "test_name": pt["name"],
            "ok": ok,
            "http": code,
            "latency_ms": elapsed_ms,
            "response_preview": short,
            "model": data.get("model", ""),
            "actual_provider": data.get("provider", ""),
        })

    results.extend(provider_results)
    passed = sum(1 for r in provider_results if r["ok"])
    print(f"    Natija: {passed}/{len(provider_results)} muvaffaqiyatli")
    return provider_results


def test_all_providers():
    print("\n" + "═" * 60)
    print("  3. BARCHA PROVIDERLAR BILAN CHAT")
    print("═" * 60)

    for p in PROVIDERS:
        test_chat_with_provider(p)



# ──────────────────────────────────────────────
# 4. AIDA Beta maxsus testlari
# ──────────────────────────────────────────────

def test_aida_beta():
    print("\n" + "═" * 60)
    print("  4. AIDA BETA TESTLARI")
    print("═" * 60)

    # 4a. Status
    code, data = get_json(f"{BASE_URL}/api/aida-beta/status/")
    ok = code == 200
    print(f"\n  4a. Status       {status_icon(ok)}  HTTP {code}")
    if ok:
        print(f"     available : {data.get('available')}")
        print(f"     provider  : {data.get('provider')}")
        print(f"     providers : {data.get('providers')}")
    results.append({"section": "aida_beta_status", "ok": ok, "http": code, "data": data})

    # 4b. Oddiy chat
    t0 = time.time()
    code2, data2 = post_json(
        f"{BASE_URL}/api/aida-beta/chat/",
        {"prompt": "Salom! Sen AIDA betamissan?", "session_id": "beta_test_1"},
    )
    ms2 = int((time.time() - t0) * 1000)
    ok2 = code2 == 200 and bool(data2.get("message"))
    print(f"\n  4b. Oddiy chat   {status_icon(ok2)}  HTTP {code2}  {ms2}ms")
    if ok2:
        print(f"     Javob : {data2.get('message','')[:100]}")
        print(f"     Model : {data2.get('model','')}")
    else:
        print(f"     Xato  : {data2}")
    results.append({"section": "aida_beta_chat", "ok": ok2, "http": code2,
                    "latency_ms": ms2, "data": data2})

    # 4c. Xotira testi — eslab qol
    t0 = time.time()
    code3, data3 = post_json(
        f"{BASE_URL}/api/aida-beta/chat/",
        {"prompt": "Mening ismim Jasur, Python o'rganmoqdaman. Eslab qol.", "session_id": "beta_mem_1"},
    )
    ms3 = int((time.time() - t0) * 1000)
    ok3 = code3 == 200
    print(f"\n  4c. Xotira (saqlash)  {status_icon(ok3)}  HTTP {code3}  {ms3}ms")
    if ok3:
        print(f"     Javob : {data3.get('message','')[:100]}")

    # 4d. Xotira testi — so'rash
    t0 = time.time()
    code4, data4 = post_json(
        f"{BASE_URL}/api/aida-beta/chat/",
        {"prompt": "Mening ismim nima edi?", "session_id": "beta_mem_1"},
    )
    ms4 = int((time.time() - t0) * 1000)
    ok4 = code4 == 200
    resp4 = data4.get("message", "")
    mem_ok = "jasur" in resp4.lower()
    print(f"\n  4d. Xotira (eslash)   {status_icon(mem_ok)}  HTTP {code4}  {ms4}ms")
    print(f"     Javob : {resp4[:100]}")
    print(f"     Xotira ishladi: {'HA ✅' if mem_ok else 'YOQ ❌'}")
    results.append({"section": "aida_beta_memory", "ok": mem_ok, "http": code4,
                    "latency_ms": ms4, "response": resp4})

    # 4e. Remember endpoint
    t0 = time.time()
    code5, data5 = post_json(
        f"{BASE_URL}/api/aida-beta/remember/",
        {"fact": "AIDA Django platformasida ishlaydi", "session_id": "beta_test_1"},
    )
    ms5 = int((time.time() - t0) * 1000)
    ok5 = code5 == 200 and data5.get("saved") is True
    print(f"\n  4e. Remember       {status_icon(ok5)}  HTTP {code5}  {ms5}ms")
    if ok5:
        print(f"     Saqlangan: {data5.get('fact','')}")
    results.append({"section": "aida_beta_remember", "ok": ok5, "http": code5,
                    "latency_ms": ms5, "data": data5})

    # 4f. Kod generatsiya
    t0 = time.time()
    code6, data6 = post_json(
        f"{BASE_URL}/api/aida-beta/chat/",
        {"prompt": "Python da faktorial funksiya yoz.", "session_id": "beta_code_1"},
    )
    ms6 = int((time.time() - t0) * 1000)
    ok6 = code6 == 200 and "def " in data6.get("message", "")
    print(f"\n  4f. Kod generatsiya  {status_icon(ok6)}  HTTP {code6}  {ms6}ms")
    resp6 = data6.get("message", "")
    print(f"     Kod bor: {'HA ✅' if ok6 else 'YOQ ❌'}")
    if resp6:
        print(f"     Javob : {resp6[:120]}")
    results.append({"section": "aida_beta_code", "ok": ok6, "http": code6,
                    "latency_ms": ms6, "has_code": ok6})



# ──────────────────────────────────────────────
# 5. Models ro'yxati testi
# ──────────────────────────────────────────────

def test_models_list():
    print("\n" + "═" * 60)
    print("  5. MODELS RO'YXATI")
    print("═" * 60)

    endpoints = [
        "/api/models/list/",
        "/api/v2/models/",
        "/api/v2/gateway/plugins/",
    ]
    for ep in endpoints:
        code, data = get_json(f"{BASE_URL}{ep}")
        ok = code == 200
        print(f"  {status_icon(ok)} {ep}  HTTP {code}")
        if ok:
            if isinstance(data, list):
                print(f"     {len(data)} ta element")
            elif isinstance(data, dict):
                keys = list(data.keys())[:5]
                print(f"     Kalitlar: {keys}")
        results.append({"section": "models_list", "endpoint": ep, "ok": ok, "http": code})


# ──────────────────────────────────────────────
# 6. Fallback testi
# ──────────────────────────────────────────────

def test_fallback():
    print("\n" + "═" * 60)
    print("  6. FALLBACK TESTI")
    print("═" * 60)

    # Mavjud bo'lmagan provider so'rash
    t0 = time.time()
    code, data = post_json(
        f"{BASE_URL}/api/chat/",
        {"message": "Salom!", "provider": "nonexistent_provider_xyz"},
    )
    ms = int((time.time() - t0) * 1000)
    # Fallback ishlasa ham javob qaytarishi kerak
    ok = code == 200 and bool(data.get("response") or data.get("message"))
    print(f"  Noto'g'ri provider → fallback  {status_icon(ok)}  HTTP {code}  {ms}ms")
    if ok:
        actual = data.get("provider", "")
        print(f"     Fallback provider: {actual}")
    else:
        print(f"     Javob: {data}")
    results.append({"section": "fallback_test", "ok": ok, "http": code,
                    "latency_ms": ms, "fallback_provider": data.get("provider", "")})


# ──────────────────────────────────────────────
# 7. Yakuniy hisobot
# ──────────────────────────────────────────────

def print_summary():
    print("\n" + "═" * 60)
    print("  YAKUNIY HISOBOT")
    print("═" * 60)

    total = len(results)
    passed = sum(1 for r in results if r.get("ok"))
    failed = total - passed

    print(f"\n  Jami testlar   : {total}")
    print(f"  Muvaffaqiyatli : {passed} ✅")
    print(f"  Muvaffaqiyatsiz: {failed} ❌")
    print(f"  Foiz           : {int(passed/total*100) if total else 0}%")

    # Provider bo'yicha statistika
    print("\n  Provider bo'yicha natijalar:")
    print_separator("-", 50)
    prov_stats = {}
    for r in results:
        pname = r.get("provider") or r.get("section", "other")
        if pname not in prov_stats:
            prov_stats[pname] = {"ok": 0, "fail": 0}
        if r.get("ok"):
            prov_stats[pname]["ok"] += 1
        else:
            prov_stats[pname]["fail"] += 1

    for pname, stat in prov_stats.items():
        total_p = stat["ok"] + stat["fail"]
        icon = "✅" if stat["fail"] == 0 else ("⚠️" if stat["ok"] > 0 else "❌")
        print(f"  {icon}  {pname:<25} {stat['ok']}/{total_p}")

    # Latency statistika
    latencies = [r["latency_ms"] for r in results if "latency_ms" in r and r["latency_ms"] > 0]
    if latencies:
        print(f"\n  Latency:")
        print(f"    Min  : {min(latencies)}ms")
        print(f"    Max  : {max(latencies)}ms")
        print(f"    O'rta: {int(sum(latencies)/len(latencies))}ms")

    return passed, failed, total


def save_report(passed, failed, total):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "timestamp": now,
        "base_url": BASE_URL,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "percent": int(passed / total * 100) if total else 0,
        },
        "results": results,
    }
    path = "C:/AIDA1-main/test_results.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n  📄 JSON hisobot saqlandi: {path}")


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "═" * 60)
    print("  🤖 AIDA — BARCHA MODELLAR TEST SKRIPTI")
    print(f"  Sana  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Server: {BASE_URL}")
    print("═" * 60)

    server_ok = test_server_status()
    if not server_ok:
        print("\n  ❌ Server ishlamayapti! Avval serverni ishga tushiring:")
        print("     .venv\\Scripts\\python manage.py runserver")
        exit(1)

    test_provider_health()
    test_all_providers()
    test_aida_beta()
    test_models_list()
    test_fallback()

    passed, failed, total = print_summary()
    save_report(passed, failed, total)

    print("\n  Test yakunlandi!\n")
