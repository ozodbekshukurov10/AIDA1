from __future__ import annotations

from AIDA.env import load_dotenv
from webapp.aida_controller import controller


def main() -> None:
    load_dotenv(".env")
    print("AIDA voice stub is active.")
    print("Voice dependencies were not bundled into this repo, so this script uses text mode.\n")

    while True:
        prompt = input("voice-text> ").strip()
        if prompt.lower() in {"exit", "quit"}:
            print("Voice session closed.")
            return
        if not prompt:
            continue

        response = controller.chat(prompt)
        print(f"\naida> {response['message']}\n")


if __name__ == "__main__":
    main()
