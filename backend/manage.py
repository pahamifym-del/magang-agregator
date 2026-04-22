#!/usr/bin/env python
"""
Entry point utama Django.
Digunakan untuk menjalankan perintah seperti:
- python manage.py runserver
- python manage.py migrate
- python manage.py createsuperuser
"""

import os
import sys


def main():
    # Gunakan settings development secara default
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django tidak bisa diimport. Pastikan sudah terinstall "
            "dan virtual environment sudah aktif."
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()