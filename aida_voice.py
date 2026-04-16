import os
import time
import speech_recognition as sr
from gtts import gTTS
import pygame
from google import genai
from google.genai import types

# 1. GEMINI API KALITINI O'RNATISH (ixtiyoriy)
API_KEY = os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=API_KEY) if API_KEY else None

# 2. OVOZ CHIQARISH FUNKSIYASI (TTS)
def speak(text):
    print(f"\n[AIDA]: {text}\n")
    try:
        tts = gTTS(text=text, lang='uz')
        tts.save("aida_voice.mp3")
        pygame.mixer.init()
        pygame.mixer.music.load("aida_voice.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.quit()
        os.remove("aida_voice.mp3")
    except Exception as e:
        pass # Ovoz o'ynatishda xatolik bo'lsa ham matn ekranda qoladi

# 3. MIKROFONDAN ESHITISH FUNKSIYASI (STT)
def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n[*] AIDA ESHITMOQDA... (Gapiring)")
        r.adjust_for_ambient_noise(source)
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=15)
            text = r.recognize_google(audio, language="uz-UZ")
            print(f"[Siz]: {text}")
            return text
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            print("[!] Tushunarsiz ovoz.")
            return ""
        except sr.RequestError:
            print("[!] Tarmoq xatosi.")
            return ""

# 4. ASOSIY DASTUR
def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Derskiy qizil rangli ASCII Art
    print("\033[91m")
    print(r"""
     █████╗ ██╗██████╗  █████╗ 
    ██╔══██╗██║██╔══██╗██╔══██╗
    ███████║██║██║  ██║███████║
    ██╔══██║██║██║  ██║██╔══██║
    ██║  ██║██║██████╔╝██║  ██║
    ╚═╝  ╚═╝╚═╝╚═════╝ ╚═╝  ╚═╝
    [ OLIY SUN'IY ONG TIZIMI - JANGAVOR REJIM ]
    """)
    print("\033[0m")
    
    # AIDA ning xarakteri (Derskiy)
    system_instruction = "Sizning ismingiz AIDA. Siz o'ta aqlli, sovuqqon, qat'iyatli va 'derskiy' (jiddiy, qattiqqo'l, o'ziga ishongan) sun'iy ongsiz. O'zbek tilida qisqa, aniq va keskin javob berasiz. Hech qachon uzr so'ramaysiz."
    
    speak("AIDA tizimi faollashdi. Buyruq bering.")
    
    while True:
        command = listen()
        if command:
            if "o'chirish" in command.lower() or "to'xta" in command.lower():
                speak("Tizim o'chirilmoqda.")
                break
            
            try:
                if client:
                    response = client.models.generate_content(
                        model='gemini-3.1-pro-preview',
                        contents=command,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.8
                        )
                    )
                    speak(response.text)
                else:
                    speak("Lokal rejim faol. Ovozli interaktiv modulda tashqi model ulanmagan.")
            except Exception as e:
                speak("Kognitiv yadroda xatolik yuz berdi.")

if __name__ == "__main__":
    main()
