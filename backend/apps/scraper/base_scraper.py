"""
Base class untuk semua scraper.
Berisi logika yang sama antara Jobstreet dan Glints
supaya tidak ada kode duplikat.
"""

import logging
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

import httpx
from django.utils import timezone
from django.utils.text import slugify

from apps.internships.models import Company, Internship, ScrapingLog
from .filters import check_relevance, extract_matched_majors

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Abstract base class untuk scraper.
    ABC = Abstract Base Class — class ini tidak bisa diinstansiasi langsung,
    harus di-inherit dulu oleh class turunan (JobstreetScraper, GlintsScraper).
    """

    # Nama sumber — wajib diisi oleh class turunan
    source_name: str = ""

    def __init__(self):
        # HTTP client dengan timeout dan header yang wajar
        self.client = httpx.Client(
            timeout=30.0,
            headers={
                # Pura-pura jadi browser supaya tidak langsung diblokir
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
            follow_redirects=True,
        )
        self.log: Optional[ScrapingLog] = None

    def run(self) -> ScrapingLog:
        """
        Jalankan proses scraping lengkap.
        Method ini dipanggil oleh Celery task.
        """
        logger.info(f"Memulai scraping dari {self.source_name}...")

        # Buat log entry di database
        self.log = ScrapingLog.objects.create(
            source=self.source_name,
            status=ScrapingLog.RunStatus.RUNNING,
        )

        try:
            # Panggil method scraping utama (diimplementasi di class turunan)
            internships_data = self.scrape()

            total_found = len(internships_data)
            total_saved = 0
            total_duplicate = 0
            total_rejected = 0

            for data in internships_data:
                result = self._process_internship(data)
                if result == "saved":
                    total_saved += 1
                elif result == "duplicate":
                    total_duplicate += 1
                elif result == "rejected":
                    total_rejected += 1

            # Update log dengan hasil akhir
            self.log.status = ScrapingLog.RunStatus.SUCCESS
            self.log.total_found = total_found
            self.log.total_saved = total_saved
            self.log.total_duplicate = total_duplicate
            self.log.total_rejected = total_rejected
            self.log.finished_at = timezone.now()
            self.log.save()

            logger.info(
                f"Scraping {self.source_name} selesai. "
                f"Ditemukan: {total_found}, "
                f"Disimpan: {total_saved}, "
                f"Duplikat: {total_duplicate}, "
                f"Ditolak: {total_rejected}"
            )

        except Exception as e:
            # Kalau ada error tak terduga, catat di log
            logger.error(f"Scraping {self.source_name} gagal: {e}", exc_info=True)
            self.log.status = ScrapingLog.RunStatus.FAILED
            self.log.error_message = str(e)
            self.log.finished_at = timezone.now()
            self.log.save()

        finally:
            # Selalu tutup HTTP client setelah selesai
            self.client.close()

        return self.log

    def _process_internship(self, data: dict) -> str:
        """
        Proses satu data lowongan — validasi, filter, simpan.

        Returns:
            "saved" — berhasil disimpan
            "duplicate" — sudah ada di database
            "rejected" — tidak relevan / tidak valid
        """
        try:
            # 1. Cek duplikat berdasarkan URL sumber
            source_url = data.get("source_url", "")
            if not source_url:
                logger.warning("Lowongan tanpa URL dibuang")
                return "rejected"

            if Internship.objects.filter(source_url=source_url).exists():
                logger.debug(f"Duplikat ditemukan: {source_url}")
                return "duplicate"

          # 2. Cek relevansi jurusan — pisahkan judul dan deskripsi
            # supaya filter lapis 1 (judul) bisa berjalan dengan benar
            title = data.get("title", "")
            text_to_check = " ".join([
                data.get("description", ""),
                data.get("requirements", ""),
            ])

            is_relevant, matched_keywords = check_relevance(text_to_check, title=title)

            if not is_relevant:
                logger.debug(f"Lowongan tidak relevan: {data.get('title', '')}")
                return "rejected"

            # 3. Ambil atau buat data perusahaan
            company = self._get_or_create_company(data)

            # 4. Buat slug unik untuk lowongan
            base_slug = slugify(f"{data.get('title', '')} {company.name}")
            slug = self._make_unique_slug(base_slug)

            # 5. Simpan lowongan ke database
            Internship.objects.create(
                company=company,
                title=data.get("title", ""),
                slug=slug,
                description=data.get("description", ""),
                requirements=data.get("requirements", ""),
                location=data.get("location", ""),
                work_type=data.get("work_type", Internship.WorkType.UNKNOWN),
                education_level=data.get(
                    "education_level", Internship.EducationLevel.UNKNOWN
                ),
                relevant_majors=extract_matched_majors(matched_keywords),
                salary_min=data.get("salary_min"),
                salary_max=data.get("salary_max"),
                is_salary_visible=data.get("is_salary_visible", False),
                source=self.source_name,
                source_url=source_url,
                source_id=data.get("source_id", ""),
                posted_at=data.get("posted_at"),
                deadline=data.get("deadline"),
                status=Internship.Status.PENDING,
            )

            logger.info(f"Disimpan: {data.get('title', '')} @ {company.name}")
            return "saved"

        except Exception as e:
            logger.error(
                f"Error memproses lowongan '{data.get('title', '')}': {e}",
                exc_info=True
            )
            return "rejected"

    def _get_or_create_company(self, data: dict) -> Company:
        """
        Ambil perusahaan dari database kalau sudah ada,
        atau buat baru kalau belum.
        """
        company_name = data.get("company_name", "").strip()
        if not company_name:
            company_name = "Perusahaan Tidak Diketahui"

        company_slug = slugify(company_name)

        # get_or_create mengembalikan tuple (object, created)
        # created = True kalau baru dibuat, False kalau sudah ada
        company, created = Company.objects.get_or_create(
            slug=company_slug,
            defaults={
                "name": company_name,
                "logo_url": data.get("company_logo_url"),
                "location": data.get("location", ""),
                "industry": data.get("industry", ""),
            }
        )

        if created:
            logger.debug(f"Perusahaan baru dibuat: {company_name}")

        return company

    def _make_unique_slug(self, base_slug: str) -> str:
        """
        Buat slug yang unik.
        Kalau slug sudah ada, tambahkan angka di belakangnya.
        Contoh: "web-developer-pt-maju" -> "web-developer-pt-maju-2"
        """
        slug = base_slug
        counter = 2

        while Internship.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug

    def _parse_salary(self, salary_text: str) -> tuple[Optional[int], Optional[int]]:
        """
        Parse teks gaji menjadi angka min dan max.
        Contoh: "Rp 3.000.000 - Rp 5.000.000" -> (3000000, 5000000)
        """
        import re

        if not salary_text:
            return None, None

        # Hapus karakter non-numerik kecuali titik dan strip
        numbers = re.findall(r"[\d.]+", salary_text.replace(",", "."))

        try:
            # Bersihkan titik pemisah ribuan
            parsed = [int(n.replace(".", "")) for n in numbers if len(n) > 2]

            if len(parsed) >= 2:
                return min(parsed), max(parsed)
            elif len(parsed) == 1:
                return parsed[0], None
        except (ValueError, AttributeError):
            pass

        return None, None

    @abstractmethod
    def scrape(self) -> list[dict]:
        """
        Method utama scraping — WAJIB diimplementasi oleh class turunan.
        Harus mengembalikan list of dict dengan struktur:
        {
            "title": str,
            "company_name": str,
            "company_logo_url": str | None,
            "description": str,
            "requirements": str,
            "location": str,
            "work_type": str,  # onsite/remote/hybrid/unknown
            "education_level": str,  # d3/d4/s1/all/unknown
            "salary_min": int | None,
            "salary_max": int | None,
            "is_salary_visible": bool,
            "source_url": str,
            "source_id": str,
            "posted_at": datetime | None,
            "deadline": date | None,
            "industry": str,
        }
        """
        pass