#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import json
import os
import sys
from pathlib import Path


RUNTIME_FILE = Path(__file__).resolve().parent / ".aida_runtime.json"


def _load_last_runserver_address() -> str | None:
    if not RUNTIME_FILE.exists():
        return None
    try:
        payload = json.loads(RUNTIME_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    address = str(payload.get("runserver_address", "")).strip()
    return address or None


def _save_last_runserver_address(address: str) -> None:
    payload = {"runserver_address": address}
    RUNTIME_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _normalize_runserver_args(argv: list[str]) -> list[str]:
    if len(argv) < 2 or argv[1] != "runserver":
        return argv

    explicit_address = None
    for item in argv[2:]:
        if not item.startswith("-"):
            explicit_address = item
            break

    if explicit_address:
        _save_last_runserver_address(explicit_address)
        return argv

    remembered = _load_last_runserver_address()
    if remembered:
        return [*argv, remembered]
    return argv


def main():
    """Run administrative tasks."""
    from AIDA.env import load_dotenv

    load_dotenv(".env")
    sys.argv = _normalize_runserver_args(sys.argv)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AIDA.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
