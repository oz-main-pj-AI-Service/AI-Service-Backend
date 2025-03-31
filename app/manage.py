#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

pass


def main():
    """Run administrative tasks."""
    DIR = Path(__file__).resolve().parent.parent
    load_dotenv(DIR / ".env")
    django_env = os.getenv("DJANGO_ENV","dev")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"config.settings.{django_env}")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
