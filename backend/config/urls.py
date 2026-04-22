"""
URL routing utama project.
Semua URL dari seluruh app didaftarkan di sini.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin Django — akses di /admin/
    path("admin/", admin.site.urls),

    # Semua API endpoint diawali /api/v1/
    # v1 = versioning — kalau nanti ada breaking change, bisa buat v2
    path("api/v1/", include("config.api_urls")),
]

# Tambahan khusus development
if settings.DEBUG:
    # Serve file media (upload) saat development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Debug Toolbar
    import debug_toolbar
    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns