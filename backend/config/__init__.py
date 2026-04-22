# Menandakan folder 'config' sebagai Python package.
# Sekaligus memberitahu Django untuk load Celery saat startup.

from .celery import app as celery_app

__all__ = ("celery_app",)