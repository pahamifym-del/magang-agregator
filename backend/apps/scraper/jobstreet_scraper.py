"""
Scraper untuk Jobstreet Indonesia.
Jobstreet menggunakan JavaScript untuk render konten,
jadi kita pakai Playwright untuk mengontrol browser Chromium.
"""

import json
import logging
import time
import re
from datetime import datetime, date
from typing import Optional

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from django.utils import timezone

from .base_scraper import BaseScraper
from apps.internships.models import Internship

logger = logging.getLogger(__name__)

# Keyword pencarian di Jobstreet
SEARCH_KEYWORDS = ["magang", "internship", "intern"]

# Kota-kota besar di Indonesia yang kita target
TARGET_CITIES = ["jakarta", "surabaya", "bandung", "yogyakarta", "semarang", ""]

# Maksimal halaman per keyword (1 halaman = ~20 lowongan)
MAX_PAGES = 3


class JobstreetScraper(BaseScraper):
    """
    Scraper Jobstreet menggunakan Playwright.
    Playwright mengontrol browser Chromium seperti manusia
    yang membuka website — menghindari deteksi bot sederhana.
    """

    source_name = "jobstreet"

    def scrape(self) -> list[dict]:
        """Jalankan scraping dari semua keyword dan kota."""
        all_internships = []

        # Jalankan Playwright
        with sync_playwright() as p:
            # Launch browser Chromium dalam mode headless (tanpa tampilan GUI)
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",  # Penting untuk Docker
                    "--disable-gpu",
                ]
            )

            # Buat context baru (seperti membuka tab browser baru)
            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                locale="id-ID",
            )
            page = context.new_page()

            try:
                for keyword in SEARCH_KEYWORDS:
                    for city in TARGET_CITIES[:3]:  # Batasi 3 kota saja
                        internships = self._scrape_keyword(page, keyword, city)
                        all_internships.extend(internships)

                        # Delay supaya tidak dianggap bot
                        time.sleep(3)

            except Exception as e:
                logger.error(f"Error scraping Jobstreet: {e}", exc_info=True)
            finally:
                browser.close()

        # Hapus duplikat berdasarkan source_url
        seen_urls = set()
        unique_internships = []
        for item in all_internships:
            url = item.get("source_url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_internships.append(item)

        logger.info(f"Total unik dari Jobstreet: {len(unique_internships)}")
        return unique_internships

    def _scrape_keyword(self, page, keyword: str, city: str) -> list[dict]:
        """Scrape lowongan untuk satu kombinasi keyword + kota."""
        internships = []

        for page_num in range(1, MAX_PAGES + 1):
            try:
                # Bangun URL pencarian Jobstreet
                # Format: https://www.jobstreet.co.id/id/jobs/keyword-kota-page
                city_part = f"-{city}" if city else ""
                url = (
                    f"https://www.jobstreet.co.id/id/jobs/"
                    f"{keyword.replace(' ', '-')}{city_part}-jobs"
                    f"?pg={page_num}"
                )

                logger.info(f"Scraping Jobstreet: {url}")

                # Buka halaman
                page.goto(url, wait_until="networkidle", timeout=30000)

                # Tunggu card lowongan muncul
                try:
                    page.wait_for_selector(
                        "[data-testid='job-card']",
                        timeout=10000
                    )
                except PlaywrightTimeout:
                    logger.warning(f"Timeout menunggu card di halaman {page_num}")
                    break

                # Ambil semua card lowongan
                job_cards = page.query_selector_all("[data-testid='job-card']")

                if not job_cards:
                    logger.info(f"Tidak ada lowongan di halaman {page_num}")
                    break

                logger.info(
                    f"Ditemukan {len(job_cards)} lowongan "
                    f"(keyword={keyword}, kota={city}, hal={page_num})"
                )

                for card in job_cards:
                    data = self._parse_job_card(page, card)
                    if data:
                        internships.append(data)

                # Delay antar halaman
                time.sleep(2)

            except PlaywrightTimeout:
                logger.warning(f"Timeout di halaman {page_num}, lanjut ke keyword berikutnya")
                break
            except Exception as e:
                logger.error(f"Error di halaman {page_num}: {e}", exc_info=True)
                break

        return internships

    def _parse_job_card(self, page, card) -> Optional[dict]:
        """
        Parse satu card lowongan dari Jobstreet.
        Ekstrak semua informasi yang kita butuhkan.
        """
        try:
            # Judul lowongan
            title_el = card.query_selector("[data-testid='job-title']")
            title = title_el.inner_text().strip() if title_el else ""

            if not title:
                return None

            # URL lowongan
            link_el = card.query_selector("a[data-testid='job-title']")
            source_url = ""
            if link_el:
                href = link_el.get_attribute("href")
                if href:
                    # Pastikan URL lengkap
                    if href.startswith("http"):
                        source_url = href
                    else:
                        source_url = f"https://www.jobstreet.co.id{href}"

            if not source_url:
                return None

            # Nama perusahaan
            company_el = card.query_selector("[data-testid='company-name']")
            company_name = company_el.inner_text().strip() if company_el else ""

            # Lokasi
            location_el = card.query_selector("[data-testid='job-location']")
            location = location_el.inner_text().strip() if location_el else ""

            # Gaji (kalau ada)
            salary_el = card.query_selector("[data-testid='job-salary']")
            salary_text = salary_el.inner_text().strip() if salary_el else ""
            salary_min, salary_max = self._parse_salary(salary_text)
            is_salary_visible = bool(salary_text)

            # Ambil ID dari URL
            source_id = self._extract_job_id(source_url)

            # Buka halaman detail untuk ambil deskripsi lengkap
            description, requirements, work_type, education_level = (
                self._get_job_detail(page, source_url)
            )

            return {
                "title": title,
                "company_name": company_name,
                "company_logo_url": None,
                "description": description,
                "requirements": requirements,
                "location": location,
                "work_type": work_type,
                "education_level": education_level,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "is_salary_visible": is_salary_visible,
                "source_url": source_url,
                "source_id": source_id,
                "posted_at": timezone.now(),
                "deadline": None,
                "industry": "",
            }

        except Exception as e:
            logger.error(f"Error parsing card: {e}", exc_info=True)
            return None

    def _get_job_detail(
        self, page, url: str
    ) -> tuple[str, str, str, str]:
        """
        Buka halaman detail lowongan dan ambil informasi lengkap.
        Returns: (description, requirements, work_type, education_level)
        """
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)

            # Tunggu konten halaman detail
            try:
                page.wait_for_selector(
                    "[data-testid='job-detail-section']",
                    timeout=10000
                )
            except PlaywrightTimeout:
                pass

            # Ambil seluruh teks deskripsi
            desc_el = page.query_selector("[data-testid='job-detail-section']")
            full_text = desc_el.inner_text() if desc_el else ""

            # Pisahkan deskripsi dan persyaratan
            description, requirements = self._split_desc_requirements(full_text)

            # Deteksi tipe kerja
            work_type = self._detect_work_type(full_text)

            # Deteksi jenjang pendidikan
            education_level = self._detect_education_level(full_text)

            # Delay sopan setelah buka halaman detail
            time.sleep(1.5)

            return description, requirements, work_type, education_level

        except Exception as e:
            logger.error(f"Error ambil detail {url}: {e}", exc_info=True)
            return "", "", Internship.WorkType.UNKNOWN, Internship.EducationLevel.UNKNOWN

    def _split_desc_requirements(self, full_text: str) -> tuple[str, str]:
        """
        Pisahkan teks lengkap menjadi deskripsi dan persyaratan.
        Cari kata kunci seperti "Persyaratan", "Requirements", "Kualifikasi".
        """
        req_markers = [
            "persyaratan", "requirements", "kualifikasi",
            "qualification", "kriteria", "syarat"
        ]

        text_lower = full_text.lower()
        split_pos = len(full_text)  # Default: semua jadi deskripsi

        for marker in req_markers:
            pos = text_lower.find(marker)
            if pos > 0 and pos < split_pos:
                split_pos = pos

        description = full_text[:split_pos].strip()
        requirements = full_text[split_pos:].strip()

        return description, requirements

    def _detect_work_type(self, text: str) -> str:
        """Deteksi tipe kerja dari teks."""
        text_lower = text.lower()

        if any(w in text_lower for w in ["remote", "wfh", "work from home"]):
            if any(w in text_lower for w in ["hybrid", "onsite", "on-site", "kantor"]):
                return Internship.WorkType.HYBRID
            return Internship.WorkType.REMOTE

        if any(w in text_lower for w in ["hybrid"]):
            return Internship.WorkType.HYBRID

        if any(w in text_lower for w in ["onsite", "on-site", "di kantor", "work from office"]):
            return Internship.WorkType.ONSITE

        return Internship.WorkType.UNKNOWN

    def _detect_education_level(self, text: str) -> str:
        """Deteksi jenjang pendidikan dari teks."""
        text_lower = text.lower()

        if re.search(r"\bd3\b|\bd-3\b|diploma 3", text_lower):
            return Internship.EducationLevel.D3

        if re.search(r"\bd4\b|\bd-4\b|diploma 4", text_lower):
            return Internship.EducationLevel.D4

        if re.search(r"\bs1\b|\bs-1\b|sarjana", text_lower):
            return Internship.EducationLevel.S1

        if "semua jenjang" in text_lower or "semua jurusan" in text_lower:
            return Internship.EducationLevel.ALL

        return Internship.EducationLevel.UNKNOWN

    def _extract_job_id(self, url: str) -> str:
        """Ekstrak ID lowongan dari URL Jobstreet."""
        # URL format: .../job/123456789
        match = re.search(r"/job/(\d+)", url)
        if match:
            return match.group(1)

        # Fallback: pakai hash dari URL
        import hashlib
        return hashlib.md5(url.encode()).hexdigest()[:12]