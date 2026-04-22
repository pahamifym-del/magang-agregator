"""
Kumpulan semua URL API.
Dipisah dari urls.py utama supaya lebih rapi.
"""

from django.urls import path, include

urlpatterns = [
    # Endpoint autentikasi: /api/v1/auth/...
    path("auth/", include("apps.users.urls")),

    # Endpoint lowongan: /api/v1/internships/...
    path("internships/", include("apps.internships.urls")),

    # Endpoint scraper (admin only): /api/v1/scraper/...
    path("scraper/", include("apps.scraper.urls")),
]