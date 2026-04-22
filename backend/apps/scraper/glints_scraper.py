"""
Scraper untuk Glints Indonesia.
Menggunakan query GraphQL searchJobsV3 yang ditemukan dari browser DevTools.

Catatan arsitektur:
- TIDAK melakukan request per-job untuk detail, karena menyebabkan rate limiting (403)
- Data dari search sudah cukup untuk ditampilkan di platform
- Deskripsi lengkap dapat diakses via link ke halaman Glints
"""

import logging
import time
from datetime import datetime
from typing import Optional

from apps.internships.models import Internship
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

GLINTS_GRAPHQL_URL = "https://glints.com/api/v2-alc/graphql"

# Keyword pencarian — kombinasi ini memaksimalkan cakupan lowongan magang IT
SEARCH_KEYWORDS = [
    "software engineer intern",
    "frontend intern",
    "backend intern",
    "data analyst intern",
    "ui ux intern",
    "mobile developer intern",
    "fullstack intern",
    "it intern",
    "web developer intern",
    "data science intern",
]

PAGE_SIZE = 30  # Maksimal per halaman
MAX_PAGES = 1   # Batas halaman per keyword (30 × 5 = 150 lowongan per keyword)

# Jeda request — penting untuk hindari rate limiting (403 Forbidden)
# Glints memblokir jika request terlalu cepat berurutan
DELAY_BETWEEN_PAGES = 5     # detik antar halaman dalam satu keyword
DELAY_BETWEEN_KEYWORDS = 6  # detik antar keyword berbeda


class GlintsScraper(BaseScraper):
    source_name = "glints"

    # Query GraphQL — field-field yang terbukti valid dari pengujian DevTools
    SEARCH_QUERY = """
    query searchJobsV3($data: JobSearchConditionInput!) {
      searchJobsV3(data: $data) {
        jobsInPage {
          id
          title
          workArrangementOption
          status
          createdAt
          updatedAt
          shouldShowSalary
          educationLevel
          type
          salaryEstimate {
            minAmount
            maxAmount
            CurrencyCode
          }
          company {
            id
            name
            logo
            industry {
              id
              name
            }
          }
          city {
            id
            name
          }
          country {
            code
            name
          }
          skills {
            skill {
              id
              name
            }
            mustHave
          }
        }
        hasMore
      }
    }
    """

    def scrape(self) -> list[dict]:
        """
        Entry point utama scraper.
        Iterasi semua keyword, kumpulkan hasil, lalu hapus duplikat.
        """
        all_internships = []

        for keyword in SEARCH_KEYWORDS:
            logger.info(f"Glints: mulai scraping keyword='{keyword}'")
            internships = self._scrape_keyword(keyword)
            all_internships.extend(internships)
            # Jeda antar keyword agar tidak kena rate limit
            time.sleep(DELAY_BETWEEN_KEYWORDS)

        # Hapus duplikat berdasarkan source_id (ID unik dari Glints)
        seen_ids = set()
        unique = []
        for item in all_internships:
            sid = item.get("source_id", "")
            if sid and sid not in seen_ids:
                seen_ids.add(sid)
                unique.append(item)

        logger.info(f"Glints: total unik = {len(unique)} lowongan")
        return unique

    def _scrape_keyword(self, keyword: str) -> list[dict]:
        """
        Scrape semua halaman untuk satu keyword.
        Berhenti jika tidak ada halaman berikutnya atau terjadi error.
        """
        internships = []

        for page_num in range(1, MAX_PAGES + 1):
            try:
                response = self.client.post(
                    GLINTS_GRAPHQL_URL,
                    json={
                        "operationName": "searchJobsV3",
                        "query": self.SEARCH_QUERY,
                        "variables": {
                            "data": {
                                # PENTING: field yang benar adalah "SearchTerm" (kapital S dan T)
                                # bukan "keyword" — ditemukan dari DevTools browser
                                "SearchTerm": keyword,
                                "CountryCode": "ID",
                                "includeExternalJobs": True,
                                "pageSize": PAGE_SIZE,
                                "page": page_num,
                                # PENTING: field filter tipe kerja adalah "type", bukan "jobTypeFilters"
                                "type": ["INTERNSHIP"],
                            }
                        }
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "*/*",
                        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                        "Origin": "https://glints.com",
                        "Referer": "https://glints.com/id/opportunities/jobs/explore",
                        "x-glints-country": "ID",
                        # Header berikut membuat request terlihat lebih seperti browser asli
                        "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124"',
                        "sec-ch-ua-mobile": "?0",
                        "sec-ch-ua-platform": '"Windows"',
                        "sec-fetch-dest": "empty",
                        "sec-fetch-mode": "cors",
                        "sec-fetch-site": "same-origin",
                    }
                )

                response.raise_for_status()
                data = response.json()

                # Navigasi ke data hasil pencarian
                search_result = data.get("data", {}).get("searchJobsV3", {})
                jobs = search_result.get("jobsInPage", [])
                has_more = search_result.get("hasMore", False)

                if not jobs:
                    logger.info(
                        f"Glints: tidak ada hasil untuk keyword='{keyword}' hal={page_num}"
                    )
                    break

                logger.info(
                    f"Glints: {len(jobs)} lowongan (keyword='{keyword}', hal={page_num})"
                )

                # Parse setiap lowongan
                for job in jobs:
                    parsed = self._parse_job(job)
                    if parsed:
                        internships.append(parsed)

                # Berhenti kalau sudah halaman terakhir
                if not has_more:
                    logger.info(
                        f"Glints: tidak ada halaman berikutnya, berhenti di hal={page_num}"
                    )
                    break

                # Jeda antar halaman — 5 detik untuk hindari 403
                time.sleep(DELAY_BETWEEN_PAGES)

            except Exception as e:
                logger.error(
                    f"Glints: error scraping keyword='{keyword}' hal={page_num}: {e}",
                    exc_info=True
                )
                break

        return internships

    def _parse_job(self, job: dict) -> Optional[dict]:
        """
        Ubah data mentah dari GraphQL menjadi format standar platform.
        Return None kalau data tidak valid.
        """
        try:
            # ID unik dari Glints — wajib ada
            job_id = job.get("id", "")
            if not job_id:
                return None

            # Judul lowongan — wajib ada
            title = job.get("title", "").strip()
            if not title:
                return None

            # --- Data Perusahaan ---
            company = job.get("company") or {}
            company_name = company.get("name", "")
            company_logo = company.get("logo")  # URL logo, bisa None
            industry_data = company.get("industry") or {}
            industry = industry_data.get("name", "")

            # --- Lokasi ---
            city_data = job.get("city") or {}
            location = city_data.get("name", "")

            # --- Tipe Kerja (Remote/Hybrid/Onsite) ---
            work_arrangement = job.get("workArrangementOption", "")
            work_type = self._map_work_type(work_arrangement)

            # --- Gaji ---
            salary_data = job.get("salaryEstimate") or {}
            salary_min = salary_data.get("minAmount")
            salary_max = salary_data.get("maxAmount")
            # Tampilkan gaji hanya kalau Glints mengizinkan DAN datanya ada
            is_salary_visible = bool(
                job.get("shouldShowSalary") and (salary_min or salary_max)
            )

            # --- Skills sebagai requirements ---
            skills_raw = job.get("skills") or []
            skill_names = [
                s.get("skill", {}).get("name", "")
                for s in skills_raw
                if s.get("skill", {}).get("name")
            ]
            requirements = ", ".join(skill_names) if skill_names else ""

            # --- URL Lowongan ---
            source_url = f"https://glints.com/id/opportunities/jobs/{job_id}"

            # --- Tanggal Posting ---
            posted_at = None
            created_at_str = job.get("createdAt", "")
            if created_at_str:
                try:
                    # Format ISO 8601 dari Glints: "2026-04-21T06:36:49.799Z"
                    posted_at = datetime.fromisoformat(
                        created_at_str.replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError):
                    pass

            # --- Jenjang Pendidikan ---
            edu_raw = job.get("educationLevel", "")
            education_level = self._map_education_level(edu_raw)

            return {
                "title": title,
                "company_name": company_name,
                "company_logo_url": company_logo,
                # Deskripsi kosong — tidak fetch detail untuk hindari rate limit
                # User dapat klik source_url untuk lihat deskripsi lengkap
                "description": "",
                "requirements": requirements,
                "location": location,
                "work_type": work_type,
                "education_level": education_level,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "is_salary_visible": is_salary_visible,
                "source_url": source_url,
                "source_id": job_id,
                "posted_at": posted_at,
                "deadline": None,  # Tidak tersedia dari search API
                "industry": industry,
            }

        except Exception as e:
            logger.error(f"Glints: error parsing job: {e}", exc_info=True)
            return None

    # -------------------------------------------------------------------------
    # Helper methods
    # -------------------------------------------------------------------------

    def _map_work_type(self, work_arrangement: str) -> str:
        """Konversi nilai workArrangementOption Glints ke format internal."""
        mapping = {
            "REMOTE": Internship.WorkType.REMOTE,
            "HYBRID": Internship.WorkType.HYBRID,
            "ONSITE": Internship.WorkType.ONSITE,
        }
        key = work_arrangement.upper() if work_arrangement else ""
        return mapping.get(key, Internship.WorkType.UNKNOWN)

    def _map_education_level(self, edu_level: str) -> str:
        """Konversi nilai educationLevel Glints ke format internal."""
        edu_upper = edu_level.upper() if edu_level else ""

        if "D3" in edu_upper or "DIPLOMA_3" in edu_upper:
            return Internship.EducationLevel.D3
        if "D4" in edu_upper or "DIPLOMA_4" in edu_upper:
            return Internship.EducationLevel.D4
        if "S1" in edu_upper or "BACHELOR" in edu_upper:
            return Internship.EducationLevel.S1

        return Internship.EducationLevel.UNKNOWN