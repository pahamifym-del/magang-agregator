"""
Model custom user.
Extend AbstractUser bawaan Django supaya bisa tambah field sendiri
tanpa bikin ulang sistem autentikasi.
"""

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model.
    Selalu buat custom user model dari awal — sangat susah diubah nanti
    kalau sudah pakai AbstractUser bawaan Django.
    """

    # Ganti primary key ke UUID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Email sebagai login utama (bukan username)
    email = models.EmailField(
        unique=True,
        verbose_name="Email"
    )

    # Field tambahan
    avatar_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="URL Avatar"
    )

    # Jurusan user — untuk personalisasi rekomendasi lowongan
    major = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Jurusan",
        help_text="Contoh: Teknologi Informasi"
    )

    # Notifikasi email
    email_notifications = models.BooleanField(
        default=True,
        verbose_name="Notifikasi Email?"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Gunakan email sebagai field login
    USERNAME_FIELD = "email"

    # username tetap required tapi bukan untuk login
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "Pengguna"
        verbose_name_plural = "Pengguna"

    def __str__(self):
        return self.email


class SavedInternship(models.Model):
    """
    Lowongan yang disimpan user (bookmark).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="saved_internships",
        verbose_name="Pengguna"
    )

    # Import string supaya tidak circular import
    internship = models.ForeignKey(
        "internships.Internship",
        on_delete=models.CASCADE,
        related_name="saved_by",
        verbose_name="Lowongan"
    )

    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Lowongan Tersimpan"
        verbose_name_plural = "Lowongan Tersimpan"
        # Satu user tidak bisa simpan lowongan yang sama dua kali
        unique_together = ["user", "internship"]
        ordering = ["-saved_at"]

    def __str__(self):
        return f"{self.user.email} — {self.internship.title}"