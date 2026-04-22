"""
Model untuk konfigurasi scraper.
Disimpan di database supaya bisa diubah tanpa deploy ulang.
"""

import uuid
from django.db import models


class ScraperConfig(models.Model):
    """
    Konfigurasi scraper per sumber.
    Contoh: interval scraping, apakah aktif, keyword pencarian.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    source = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Sumber"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktif?"
    )

    # Interval scraping dalam menit
    # Default: 360 menit = 6 jam
    interval_minutes = models.PositiveIntegerField(
        default=360,
        verbose_name="Interval Scraping (menit)"
    )

    # Keyword yang dipakai saat scraping
    # Disimpan sebagai JSON array
    # Contoh: ["magang", "internship", "intern"]
    search_keywords = models.JSONField(
        default=list,
        verbose_name="Keyword Pencarian"
    )

    # Maksimal halaman yang di-scrape per run
    max_pages = models.PositiveIntegerField(
        default=5,
        verbose_name="Maksimal Halaman"
    )

    # Delay antar request dalam detik (supaya tidak kena rate limit)
    request_delay_seconds = models.FloatField(
        default=2.0,
        verbose_name="Delay Antar Request (detik)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Konfigurasi Scraper"
        verbose_name_plural = "Konfigurasi Scraper"

    def __str__(self):
        status = "Aktif" if self.is_active else "Nonaktif"
        return f"{self.source} ({status})"