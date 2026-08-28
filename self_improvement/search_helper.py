# -*- coding: utf-8 -*-
"""
AIDA Web Search Assistant (RAG Helper)
=======================================
DuckDuckGo HTML orqali internetdan ma'lumotlarni qidiradi va 
barcha modellar (Gemini va Ollama) uchun yangi bilim (fresh context) tayyorlaydi.
"""
import urllib.parse, re, logging
import httpx

logger = logging.getLogger("aida.search_helper")


def search_web(query: str, max_results: int = 4) -> str:
    """
    DuckDuckGo orqali qidiruv o'tkazadi va natijalarni konsolidatsiya qiladi.
    """
    logger.info(f"[SearchAssistant] Internetda qidirilmoqda: '{query}'")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # DuckDuckGo HTML versiyasi
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    
    try:
        resp = httpx.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        html = resp.text
        
        # Regex orqali natijalarni ajratish
        # DDG HTML format: <td class="result-snippet">...</td> va <a class="result__snippet"...
        snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)
        titles = re.findall(r'<a class="result__url"[^>]*>(.*?)</a>', html, re.DOTALL)
        
        if not snippets:
            # Muqobil regex (class="result-snippet")
            snippets = re.findall(r'<td class="result-snippet"[^>]*>(.*?)</td>', html, re.DOTALL)
            
        results = []
        for i in range(min(len(snippets), max_results)):
            snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip()  # strip HTML tags
            title = re.sub(r'<[^>]+>', '', titles[i]).strip() if i < len(titles) else "Internet Manba"
            results.append(f"Manba: {title}\nMa'lumot: {snippet}")
            
        if not results:
            return "Internetdan tegishli ma'lumot topilmadi."
            
        context_text = "\n\n".join(results)
        logger.info(f"[SearchAssistant] Internetdan {len(results)} ta ma'lumot yuklandi.")
        return context_text
        
    except Exception as e:
        logger.error(f"[SearchAssistant] Qidiruvda xato: {e}")
        return f"Internet qidiruv xatosi: {str(e)}"
