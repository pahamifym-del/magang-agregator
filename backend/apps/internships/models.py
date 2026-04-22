"""
Model database untuk data lowongan magang.
Setiap class di sini = 1 tabel di PostgreSQL.
"""

import uuid
from django.db import models
from django.utils import timezone


class Company(models.Model):
    """
    Tabel perusahaan.
    Dipisah dari lowongan supaya tidak duplikat data perusahaan
    yang punya banyak lowongan.
    """

    # Gunakan UUID sebagai primary key — lebih aman dari integer berurutan
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(
        max_length=255,
        verbose_name="Nama Perusahaan"
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        verbose_name="Slug",
        help_text="Versi URL-friendly dari nama perusahaan. Contoh: pt-maju-jaya"
    )
    logo_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="URL Logo"
    )
    website = models.URLField(
        blank=True,
        null=True,
        verbose_name="Website Perusahaan"
    )
    industry = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Industri",
        help_text="Contoh: Teknologi, Perbankan, E-Commerce"
    )
    location = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Lokasi Perusahaan"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Perusahaan"
        verbose_name_plural = "Perusahaan"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Internship(models.Model):
    """
    Tabel lowongan magang — tabel utama project ini.
    """

    # ========================
    # PILIHAN (CHOICES)
    # ========================

    class Source(models.TextChoices):
        GLINTS = "glints", "Glints"
        INDEED = "indeed", "Indeed"



    class Status(models.TextChoices):
        """Status verifikasi lowongan."""
        PENDING = "pending", "Menunggu Verifikasi"
        ACTIVE = "active", "Aktif"
        EXPIRED = "expired", "Kadaluarsa"
        REJECTED = "rejected", "Ditolak"

    class WorkType(models.TextChoices):
        """Tipe kerja."""
        ONSITE = "onsite", "On-site"
        REMOTE = "remote", "Remote"
        HYBRID = "hybrid", "Hybrid"
        UNKNOWN = "unknown", "Tidak Diketahui"

    class EducationLevel(models.TextChoices):
        """Jenjang pendidikan."""
        D3 = "d3", "D3"
        D4 = "d4", "D4"
        S1 = "s1", "S1"
        ALL = "all", "Semua Jenjang"
        UNKNOWN = "unknown", "Tidak Diketahui"

    # ========================
    # FIELD UTAMA
    # ========================

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relasi ke perusahaan — kalau perusahaan dihapus, lowongannya ikut terhapus
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="internships",
        verbose_name="Perusahaan"
    )

    title = models.CharField(
        max_length=255,
        verbose_name="Judul Lowongan",
        help_text="Contoh: Junior Web Developer Intern"
    )
    slug = models.SlugField(
        max_length=300,
        unique=True,
        verbose_name="Slug URL"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Deskripsi Pekerjaan"
    )
    requirements = models.TextField(
        blank=True,
        verbose_name="Persyaratan"
    )

    # ========================
    # LOKASI & TIPE KERJA
    # ========================

    location = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Lokasi"
    )
    work_type = models.CharField(
        max_length=20,
        choices=WorkType.choices,
        default=WorkType.UNKNOWN,
        verbose_name="Tipe Kerja"
    )

    # ========================
    # PENDIDIKAN & JURUSAN
    # ========================

    education_level = models.CharField(
        max_length=20,
        choices=EducationLevel.choices,
        default=EducationLevel.UNKNOWN,
        verbose_name="Jenjang Pendidikan"
    )

    # Jurusan yang relevan — disimpan sebagai array string di PostgreSQL
    # Contoh: ["Teknologi Informasi", "Informatika", "Sistem Informasi"]
    relevant_majors = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Jurusan Relevan",
        help_text="Daftar jurusan yang relevan dengan lowongan ini"
    )

    # ========================
    # GAJI
    # ========================

    salary_min = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Gaji Minimum (Rp)"
    )
    salary_max = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Gaji Maksimum (Rp)"
    )
    is_salary_visible = models.BooleanField(
        default=False,
        verbose_name="Gaji Ditampilkan?"
    )

    # ========================
    # SUMBER DATA
    # ========================

    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        verbose_name="Sumber"
    )
    source_url = models.URLField(
        max_length=500,
        unique=True,           # URL asli tidak boleh duplikat — ini juga cara deteksi duplikat
        verbose_name="URL Sumber",
        help_text="URL asli lowongan di Jobstreet/Glints"
    )
    source_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="ID di Sumber",
        help_text="ID lowongan di platform asalnya"
    )

    # ========================
    # STATUS & VERIFIKASI
    # ========================

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Status",
        db_index=True           # Index supaya query filter status lebih cepat
    )
    rejection_reason = models.TextField(
        blank=True,
        verbose_name="Alasan Penolakan",
        help_text="Diisi kalau status = rejected"
    )

    # ========================
    # TANGGAL
    # ========================

    posted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Tanggal Posting"
    )
    deadline = models.DateField(
        null=True,
        blank=True,
        verbose_name="Batas Pendaftaran"
    )
    scraped_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Tanggal Di-scrape"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ========================
    # STATISTIK
    # ========================

    view_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Jumlah Dilihat"
    )

    class Meta:
        verbose_name = "Lowongan Magang"
        verbose_name_plural = "Lowongan Magang"
        # Urutkan: terbaru dulu, lalu yang paling banyak dilihat
        ordering = ["-posted_at", "-view_count"]
        indexes = [
            # Index untuk query yang sering dipakai
            models.Index(fields=["status", "source"]),
            models.Index(fields=["status", "posted_at"]),
            models.Index(fields=["deadline"]),
        ]

    def __str__(self):
        return f"{self.title} — {self.company.name}"

    @property
    def is_expired(self) -> bool:
        """Cek apakah lowongan sudah kadaluarsa berdasarkan deadline."""
        if self.deadline is None:
            return False
        return self.deadline < timezone.now().date()

    @property
    def salary_range(self) -> str:
        """Tampilkan range gaji dalam format yang mudah dibaca."""
        if not self.is_salary_visible:
            return "Tidak disebutkan"
        if self.salary_min and self.salary_max:
            return f"Rp {self.salary_min:,} – Rp {self.salary_max:,}"
        if self.salary_min:
            return f"Mulai Rp {self.salary_min:,}"
        if self.salary_max:
            return f"Hingga Rp {self.salary_max:,}"
        return "Tidak disebutkan"


class ScrapingLog(models.Model):
    """
    Log setiap kali scraper berjalan.
    Berguna untuk monitoring — berapa lowongan berhasil diambil,
    berapa yang gagal, error apa yang terjadi.
    """

    class RunStatus(models.TextChoices):
        RUNNING = "running", "Sedang Berjalan"
        SUCCESS = "success", "Berhasil"
        FAILED = "failed", "Gagal"
        PARTIAL = "partial", "Sebagian Berhasil"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    source = models.CharField(
        max_length=20,
        choices=Internship.Source.choices,
        verbose_name="Sumber"
    )
    status = models.CharField(
        max_length=20,
        choices=RunStatus.choices,
        default=RunStatus.RUNNING,
        verbose_name="Status Run"
    )

    # Statistik scraping
    total_found = models.IntegerField(default=0, verbose_name="Total Ditemukan")
    total_saved = models.IntegerField(default=0, verbose_name="Total Disimpan")
    total_duplicate = models.IntegerField(default=0, verbose_name="Total Duplikat")
    total_rejected = models.IntegerField(default=0, verbose_name="Total Ditolak")

    # Error message kalau gagal
    error_message = models.TextField(blank=True, verbose_name="Pesan Error")

    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Log Scraping"
        verbose_name_plural = "Log Scraping"
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.source} — {self.started_at.strftime('%Y-%m-%d %H:%M')} — {self.status}"

    @property
    def duration_seconds(self) -> int | None:
        """Hitung durasi scraping dalam detik."""
        if self.finished_at and self.started_at:
            return int((self.finished_at - self.started_at).total_seconds())
        return None