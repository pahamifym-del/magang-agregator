"""
Settings khusus untuk environment production (server).
Aktif saat DJANGO_SETTINGS_MODULE=config.settings.production
"""

from decouple import config
from .base import *  # noqa: F401, F403

# ========================
# SECURITY — wajib aktif di production
# ========================
DEBUG = False

# Paksa semua request menggunakan HTTPS
SECURE_SSL_REDIRECT = True

# Beritahu browser untuk selalu pakai HTTPS (1 tahun)
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Cookie hanya dikirim lewat HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# ========================
# CORS — hanya izinkan domain frontend yang terdaftar
# ========================
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    # Contoh default — ganti dengan domain kamu
    default="https://yourdomain.com,https://www.yourdomain.com",
    cast=lambda v: [s.strip() for s in v.split(",")],
)

# ========================
# STATIC FILES — WhiteNoise untuk serve static tanpa Nginx
# ========================
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ========================
# SENTRY — monitoring error di production
# ========================
SENTRY_DSN = config("SENTRY_DSN", default="")

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
        ],
        # Rekam 10% dari semua request untuk performance monitoring
        traces_sample_rate=0.1,
        # Jangan kirim info user ke Sentry (privacy)
        send_default_pii=False,
    )

# ========================
# EMAIL — pakai SMTP asli di production
# ========================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")