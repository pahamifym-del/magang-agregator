"""
Celery tasks untuk scraping terjadwal.
File ini yang dipanggil oleh Celery Beat secara otomatis.
"""

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # Retry setelah 5 menit kalau gagal
    name="scraper.run_glints",
)
def run_glints_scraper(self):
    """
    Task scraping Glints.
    Dipanggil otomatis oleh Celery Beat sesuai jadwal.
    bind=True memungkinkan akses self untuk retry otomatis.
    """
    try:
        logger.info("Memulai task scraping Glints...")

        # Import di dalam fungsi untuk menghindari circular import
        from .glints_scraper import GlintsScraper

        scraper = GlintsScraper()
        log = scraper.run()

        logger.info(
            f"Task Glints selesai. "
            f"Status: {log.status}, "
            f"Disimpan: {log.total_saved}"
        )
        return {
            "status": log.status,
            "total_saved": log.total_saved,
            "total_found": log.total_found,
        }

    except Exception as exc:
        logger.error(f"Task Glints gagal: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=300)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    name="scraper.run_indeed",
)
def run_indeed_scraper(self):
    """
    Task scraping Indeed Indonesia.
    Menggantikan Jobstreet yang membutuhkan login.
    """
    try:
        logger.info("Memulai task scraping Indeed...")

        from .indeed_scraper import IndeedScraper

        scraper = IndeedScraper()
        log = scraper.run()

        logger.info(
            f"Task Indeed selesai. "
            f"Status: {log.status}, "
            f"Disimpan: {log.total_saved}"
        )
        return {
            "status": log.status,
            "total_saved": log.total_saved,
            "total_found": log.total_found,
        }

    except Exception as exc:
        logger.error(f"Task Indeed gagal: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=300)


@shared_task(name="scraper.run_all")
def run_all_scrapers():
    """
    Jalankan semua scraper sekaligus.
    Task ini yang dijadwalkan oleh Celery Beat.
    Masing-masing task dijalankan secara paralel oleh worker.
    """
    logger.info("Menjalankan semua scraper...")

    # .delay() = kirim task ke queue Celery, dijalankan async oleh worker
    run_glints_scraper.delay()
    run_indeed_scraper.delay()

    logger.info("Semua task scraper sudah dikirim ke queue")


@shared_task(name="scraper.cleanup_expired")
def cleanup_expired_internships():
    """
    Tandai lowongan yang sudah expired berdasarkan deadline.
    Dijalankan setiap hari untuk membersihkan data lama.
    """
    from apps.internships.models import Internship
    from django.utils import timezone

    today = timezone.now().date()

    # Update semua lowongan aktif yang sudah melewati deadline
    expired_count = Internship.objects.filter(
        status=Internship.Status.ACTIVE,
        deadline__lt=today,
    ).update(status=Internship.Status.EXPIRED)

    logger.info(f"Menandai {expired_count} lowongan sebagai expired")
    return {"expired_count": expired_count}