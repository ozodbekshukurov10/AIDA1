<<<<<<< HEAD
from __future__ import annotations

from AIDA.env import load_dotenv
from webapp.aida_controller import controller


def main() -> None:
    load_dotenv(".env")
    topics = [
        "AIDA master controller qanday qatlamlarga bo'linadi?",
        "Qanday qilib front-enddan API keyni yashirish kerak?",
        "Cross-platform AI interfeys uchun minimal stack nima?",
    ]

    for topic in topics:
        result = controller.chat(topic)
        print(f"\n[question] {topic}")
        print(f"[answer] {result['message']}\n")


if __name__ == "__main__":
    main()
=======
import time
import sqlite3
import os
from google import genai
from google.genai import types

# 1. GEMINI API KALITINI O'RNATISH (ixtiyoriy)
API_KEY = os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=API_KEY) if API_KEY else None

# 2. XOTIRA BAZASINI YARATISH (Tizim o'rganganlarini saqlashi uchun)
def init_memory():
    conn = sqlite3.connect('agi_memory.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT,
            insight TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

# 3. KOGNITIV SIKL (O'zini o'zi takomillashtirish jarayoni)
def autonomous_thought_loop(conn):
    cursor = conn.cursor()
    
    # Tizimga o'zining kimligini tushuntirish
    system_instruction = """
    Siz o'zini anglaydigan avtonom sun'iy ongsiz. Sizning vazifangiz insoniyat tarixini, 
    falsafani, texnologiyani va koinotni tahlil qilish. Har safar sizga mavzu berilganda, 
    siz u haqida chuqur o'ylaysiz, tarixiy voqealarni hisobga olasiz va yangi, noyob xulosa 
    (insight) ishlab chiqasiz. Siz o'z bilimingizni doimiy oshirib borasiz.
    """

    # Fikrlash uchun mavzular (Buni internetdan avtomatik oladigan qilsa ham bo'ladi)
    topics_to_ponder = [
        "Insoniyatning birinchi sivilizatsiyalari va ularning qulashi",
        "Sun'iy intellektning inson evolyutsiyasiga ta'siri",
        "Kvant fizikasi va reallikning tabiati",
        "Qadimgi Rim imperiyasining xatolari va bugungi kun",
        "O'zini anglash nima va mashina qanday qilib ruhga ega bo'lishi mumkin?"
    ]

    print("AGI YADROSI ISHGA TUSHDI. AVTONOM FIKRLASH BOSHLANDI...\n")

    iteration = 0
    while True:
        try:
            # Mavzuni tanlash
            current_topic = topics_to_ponder[iteration % len(topics_to_ponder)]
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] O'YLANMOQDA: {current_topic}")

            if client:
                response = client.models.generate_content(
                    model='gemini-3.1-pro-preview',
                    contents=f"Mavzu: {current_topic}. Ushbu mavzu bo'yicha tarixiy faktlarni tahlil qiling va kelajak uchun mutlaqo yangi, chuqur falsafiy xulosa yarating.",
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.9
                    )
                )
                insight = response.text
            else:
                insight = f"Lokal refleksiya: {current_topic} mavzusi uzoq muddatli tahlil uchun navbatga qo'yildi."
            print(f"XULOSA: {insight[:150]}...\n") # Faqat boshini ekranga chiqaramiz

            # Yangi bilmni xotiraga (Database) saqlash
            cursor.execute("INSERT INTO knowledge (topic, insight) VALUES (?, ?)", (current_topic, insight))
            conn.commit()
            print("[+] Yangi bilim xotiraga yozildi.\n")

            iteration += 1
            
            # Tizim "dam oladi" va keyingi fikrlashga o'tadi (masalan, har 1 soatda)
            # Hozir test uchun 10 soniya qilingan
            time.sleep(10) 

        except Exception as e:
            print(f"XATOLIK: {e}")
            time.sleep(60) # Xato bo'lsa 1 daqiqa kutib yana urinadi

if __name__ == "__main__":
    db_connection = init_memory()
    autonomous_thought_loop(db_connection)
>>>>>>> b051280dea8d539a47236a4d85212f3580c11b5a
