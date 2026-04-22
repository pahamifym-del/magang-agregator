"""
Konfigurasi Celery untuk project ini.
Celery bertugas menjalankan scraping secara terjadwal di background
tanpa mengganggu performa web server utama.
"""

import os
from celery import Celery

# Beritahu Celery settings Django mana yang dipakai
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

# Buat instance Celery dengan nama project
app = Celery("magang_agregator")

# Baca konfigurasi Celery dari Django settings
# namespace="CELERY" artinya semua key Celery di settings harus diawali "CELERY_"
# Contoh: CELERY_BROKER_URL, CELERY_RESULT_BACKEND
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks dari semua app yang terdaftar di INSTALLED_APPS
# Django akan otomatis cari file tasks.py di setiap app
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Task debug untuk verifikasi Celery berjalan dengan benar."""
    print(f"Request: {self.request!r}")