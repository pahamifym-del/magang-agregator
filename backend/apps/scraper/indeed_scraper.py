"""
Scraper untuk Indeed Indonesia.
Menggunakan Playwright + playwright-stealth untuk bypass deteksi bot.
"""

import logging
import re
import time
import random
from typing import Optional
from urllib.parse import urlencode

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from playwright_stealth import stealth_sync

from apps.internships.models import Internship
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

INDEED_BASE_URL = "https://id.indeed.com"

SEARCH_KEYWORDS = [
    "magang IT",
    "magang software engineer",
    "magang frontend developer",
    "magang backend developer",
    "magang data analyst",
    "magang UI UX",
    "magang web developer",
    "magang programmer",
    "internship IT",
    "internship software",
    "magang teknik informatika",
    "magang sistem informasi",
]

MAX_PAGES = 3
DELAY_BETWEEN_PAGES = 3
DELAY_BETWEEN_KEYWORDS = 5


class IndeedScraper(BaseScraper):
    source_name = "indeed"

    def scrape(self) -> list[dict]:
        all_internships = []

        for keyword in SEARCH_KEYWORDS:
            logger.info(f"Indeed: mulai scraping keyword='{keyword}'")
            try:
                results = self._scrape_keyword_fresh(keyword)
                all_internships.extend(results)
            except Exception as e:
                logger.error(f"Indeed: error keyword='{keyword}': {e}", exc_info=True)
            delay = DELAY_BETWEEN_KEYWORDS + random.uniform(5, 12)
            logger.info(f"Indeed: menunggu {delay:.1f}s")
            time.sleep(delay)

        seen_ids = set()
        unique = []
        for item in all_internships:
            sid = item.get("source_id", "")
            if sid and sid not in seen_ids:
                seen_ids.add(sid)
                unique.append(item)

        logger.info(f"Indeed: total unik = {len(unique)} lowongan")
        return unique

    def _scrape_keyword_fresh(self, keyword: str) -> list[dict]:
        internships = []
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox","--disable-setuid-sandbox","--disable-dev-shm-usage","--disable-gpu"]
            )
            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                locale="id-ID",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            )
            page = context.new_page()
            stealth_sync(page)
            try:
                internships = self._scrape_keyword(page, keyword)
            finally:
                browser.close()
        return internships
    def _scrape_keyword(self, page, keyword: str) -> list[dict]:
        internships = []

        for page_num in range(MAX_PAGES):
            offset = page_num * 16
            params = urlencode({
                "q": keyword,
                "l": "Indonesia",
                "start": offset,
                "sort": "date",
            })
            url = f"{INDEED_BASE_URL}/jobs?{params}"

            try:
                logger.info(f"Indeed: membuka {url}")
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(random.uniform(4, 8))

                title = page.title()
                if "tunggu" in title.lower() or "just a moment" in title.lower():
                    logger.warning("Indeed: Cloudflare challenge terdeteksi, berhenti")
                    break

                cards = page.query_selector_all(".job_seen_beacon")
                if not cards:
                    logger.info(f"Indeed: tidak ada card di halaman {page_num + 1}")
                    break

                logger.info(f"Indeed: {len(cards)} lowongan (keyword='{keyword}', hal={page_num + 1})")

                for card in cards:
                    parsed = self._parse_card(card)
                    if parsed:
                        internships.append(parsed)

                next_btn = page.query_selector("[data-testid='pagination-page-next']")
                if not next_btn:
                    logger.info("Indeed: tidak ada halaman berikutnya")
                    break

                time.sleep(DELAY_BETWEEN_PAGES + random.uniform(2, 5))

            except PlaywrightTimeout:
                logger.warning(f"Indeed: timeout di halaman {page_num + 1}")
                break
            except Exception as e:
                logger.error(f"Indeed: error keyword='{keyword}' hal={page_num + 1}: {e}", exc_info=True)
                break

        return internships

    def _parse_card(self, card) -> Optional[dict]:
        try:
            # Judul
            title_el = card.query_selector("h2 a span")
            title = title_el.inner_text().strip() if title_el else ""
            if not title:
                return None

            # URL dan ID — semua di dalam blok if link_el
            source_url = ""
            source_id = ""
            link_el = card.query_selector("h2 a")
            if link_el:
                href = link_el.get_attribute("href") or ""
                jk_match = re.search(r"jk=([a-f0-9]+)", href)
                if not jk_match:
                    logger.debug(f"Indeed: skip card, jk tidak ditemukan: {href[:80]}")
                    return None
                source_id = jk_match.group(1)
                source_url = f"{INDEED_BASE_URL}/viewjob?jk={source_id}"

            if not source_id:
                return None

            # Perusahaan
            company_el = card.query_selector("[data-testid='company-name']")
            company_name = company_el.inner_text().strip() if company_el else ""

            # Lokasi
            location_el = card.query_selector("[data-testid='text-location']")
            location = location_el.inner_text().strip() if location_el else ""

            # Gaji
            salary_el = card.query_selector(
                "[class*='salary'], [data-testid='attribute_snippet_testid']"
            )
            salary_text = salary_el.inner_text().strip() if salary_el else ""
            salary_min, salary_max = self._parse_salary(salary_text)
            is_salary_visible = bool(salary_text and salary_min)

            # Snippet deskripsi
            snippet_el = card.query_selector("[class*='snippet'], ul")
            snippet = snippet_el.inner_text().strip() if snippet_el else ""

            work_type = self._detect_work_type(snippet + " " + title)
            education_level = self._detect_education_level(snippet)

            return {
                "title": title,
                "company_name": company_name,
                "company_logo_url": None,
                "description": snippet,
                "requirements": "",
                "location": location,
                "work_type": work_type,
                "education_level": education_level,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "is_salary_visible": is_salary_visible,
                "source_url": source_url,
                "source_id": f"indeed_{source_id}",
                "posted_at": None,
                "deadline": None,
                "industry": "",
            }

        except Exception as e:
            logger.error(f"Indeed: error parsing card: {e}", exc_info=True)
            return None

    def _parse_salary(self, salary_text: str):
        if not salary_text:
            return None, None
        try:
            numbers = re.findall(r"[\d.]+", salary_text.replace(",", "."))
            amounts = []
            for n in numbers:
                cleaned = n.replace(".", "")
                if len(cleaned) >= 6:
                    amounts.append(int(cleaned))
            if len(amounts) >= 2:
                return min(amounts), max(amounts)
            elif len(amounts) == 1:
                return amounts[0], amounts[0]
        except (ValueError, AttributeError):
            pass
        return None, None

    def _detect_work_type(self, text: str) -> str:
        text_lower = text.lower()
        if any(w in text_lower for w in ["remote", "wfh", "work from home"]):
            if any(w in text_lower for w in ["hybrid", "onsite", "kantor"]):
                return Internship.WorkType.HYBRID
            return Internship.WorkType.REMOTE
        if "hybrid" in text_lower:
            return Internship.WorkType.HYBRID
        if any(w in text_lower for w in ["onsite", "on-site", "di kantor", "work from office"]):
            return Internship.WorkType.ONSITE
        return Internship.WorkType.UNKNOWN

    def _detect_education_level(self, text: str) -> str:
        text_lower = text.lower()
        if re.search(r"\bd3\b|\bd-3\b|diploma 3", text_lower):
            return Internship.EducationLevel.D3
        if re.search(r"\bd4\b|\bd-4\b|diploma 4", text_lower):
            return Internship.EducationLevel.D4
        if re.search(r"\bs1\b|\bs-1\b|sarjana", text_lower):
            return Internship.EducationLevel.S1
        return Internship.EducationLevel.UNKNOWN