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
