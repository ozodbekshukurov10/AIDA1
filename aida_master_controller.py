from __future__ import annotations

from AIDA.env import load_dotenv
from webapp.aida_controller import controller


def main() -> None:
    load_dotenv(".env")
    print("AIDA Master Controller")
    print("Type 'exit' to stop.\n")

    while True:
        prompt = input("you> ").strip()
        if prompt.lower() in {"exit", "quit"}:
            print("AIDA session closed.")
            return
        if not prompt:
            continue

        response = controller.chat(prompt)
        print(f"\naida> {response['message']}\n")


if __name__ == "__main__":
    main()
