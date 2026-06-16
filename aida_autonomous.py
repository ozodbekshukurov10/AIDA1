from __future__ import annotations

import time

from AIDA.env import load_dotenv
from webapp.aida_controller import controller


REFLECTION_TOPICS = [
    "AIDA uchun ko'p platformali deploy arxitekturasi",
    "Local va remote provider almashinuvi",
    "Foydalanuvchi xotirasini xavfsiz saqlash usuli",
    "Dashboard orqali AI operatsiyalarini boshqarish",
]


def main() -> None:
    load_dotenv(".env")
    print("AIDA autonomous reflection loop started.\n")

    for topic in REFLECTION_TOPICS:
        response = controller.chat(f"Ushbu mavzu bo'yicha qisqa briefing ber: {topic}")
        print(f"[topic] {topic}")
        print(f"[aida] {response['message']}\n")
        time.sleep(1)


if __name__ == "__main__":
    main()
