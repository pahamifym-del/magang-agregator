"""
Filter relevansi lowongan berdasarkan jurusan IT.

Strategi filter (2 lapis):
1. Cek judul — kalau ada keyword IT spesifik di judul, langsung lolos
2. Cek deskripsi/requirements — pakai keyword yang lebih ketat
   (keyword umum seperti "database" tidak dihitung di sini)
"""

import re
import logging

logger = logging.getLogger(__name__)

# ============================================================
# KEYWORD LAPIS 1 — Cek di JUDUL (lebih longgar)
# Kalau judul mengandung salah satu ini, langsung lolos
# ============================================================
TITLE_KEYWORDS = [
    # Nama jurusan eksplisit
    "teknologi informasi", "teknik informatika",
    "sistem informasi", "ilmu komputer", "teknik komputer",
    "rekayasa perangkat lunak", "manajemen informatika",
    "informatika", "komputer",

    # Singkatan jurusan
    r"\bti\b", r"\bif\b", r"\bsi\b", r"\bcs\b",
    r"\bik\b", r"\btk\b", r"\brpl\b", r"\bmi\b",

    # Posisi IT yang jelas
    r"\bit\b",  # "IT Intern", "IT Support"
    "software", "programmer", "developer", "coding",
    "frontend", "back.?end", "fullstack", "full.?stack",
    "web developer", "mobile developer", "android", "ios",
    "data analyst", "data science", "data engineer",
    "machine learning", "artificial intelligence",
    "cyber", "network engineer", "cloud engineer",
    "devops", "system analyst", "database administrator",
    "information technology", "computer science",
    # Tambahan — posisi IT yang umum untuk mahasiswa
    "ui.?ux", "ui/ux", "user interface", "user experience",
    "product designer", "ux designer", "ui designer",
    "ux researcher", "ux writer",
]

# ============================================================
# KEYWORD LAPIS 2 — Cek di DESKRIPSI/REQUIREMENTS (lebih ketat)
# Hanya keyword yang benar-benar spesifik IT
# Keyword umum seperti "database", "software", "engineer" dihapus
# karena bisa muncul di lowongan non-IT
# ============================================================
DESCRIPTION_KEYWORDS = [
    # Nama jurusan eksplisit — paling kuat
    "teknologi informasi", "teknik informatika",
    "sistem informasi", "ilmu komputer", "teknik komputer",
    "rekayasa perangkat lunak", "manajemen informatika",
    "informatika", "komputer",
    "information technology", "computer science",

    # Singkatan jurusan dengan word boundary
    r"\bti\b", r"\bif\b", r"\bsi\b", r"\bcs\b",
    r"\bik\b", r"\btk\b", r"\brpl\b", r"\bmi\b",

    # Skill teknis yang sangat spesifik IT
    "programming", "coding", "python", "javascript", "java",
    r"\bphp\b", "react", "vue", "angular", r"node\.?js",
    "machine learning", "deep learning", "artificial intelligence",
    r"\bai\b", r"\bml\b",
    "cyber security", "cybersecurity",
    r"\bapi\b", "microservice", "kubernetes", "docker",
    "data science", "data analyst", "data engineer",
    "android", r"\bios\b", "flutter", "kotlin", "swift",
    "linux", "devops",
]


def check_relevance(text: str, title: str = "") -> tuple[bool, list[str]]:
    """
    Cek apakah lowongan relevan dengan jurusan IT.

    Strategi 2 lapis:
    - Lapis 1: cek judul dengan keyword yang lebih luas
    - Lapis 2: cek deskripsi dengan keyword yang lebih ketat

    Args:
        text: Gabungan deskripsi + requirements
        title: Judul lowongan (dicek terpisah dengan kriteria lebih longgar)

    Returns:
        tuple: (is_relevant: bool, matched_keywords: list[str])
    """
    matched = []

    # === LAPIS 1: Cek judul ===
    if title:
        title_lower = title.lower()
        for keyword in TITLE_KEYWORDS:
            try:
                if re.search(keyword, title_lower, re.IGNORECASE):
                    matched.append(keyword)
                    break  # Satu match di judul sudah cukup
            except re.error as e:
                logger.warning(f"Regex error untuk keyword '{keyword}': {e}")
                continue

        if matched:
            logger.debug(f"Lowongan relevan via judul. Keyword cocok: {matched}")
            return True, matched

    # === LAPIS 2: Cek deskripsi/requirements ===
    if text:
        text_lower = text.lower()
        for keyword in DESCRIPTION_KEYWORDS:
            try:
                if re.search(keyword, text_lower, re.IGNORECASE):
                    matched.append(keyword)
            except re.error as e:
                logger.warning(f"Regex error untuk keyword '{keyword}': {e}")
                continue

    is_relevant = len(matched) > 0

    if is_relevant:
        logger.debug(f"Lowongan relevan via deskripsi. Keyword cocok: {matched[:3]}")
    else:
        logger.debug("Lowongan tidak relevan — tidak ada keyword jurusan IT")

    return is_relevant, matched


def extract_matched_majors(matched_keywords: list[str]) -> list[str]:
    """
    Ubah keyword yang cocok menjadi nama jurusan yang mudah dibaca.
    """
    keyword_to_major = {
        "teknologi informasi": "Teknologi Informasi",
        r"\bti\b": "Teknologi Informasi",
        "teknik informatika": "Teknik Informatika",
        r"\bif\b": "Teknik Informatika",
        "informatika": "Teknik Informatika",
        "sistem informasi": "Sistem Informasi",
        r"\bsi\b": "Sistem Informasi",
        "ilmu komputer": "Ilmu Komputer",
        r"\bcs\b": "Ilmu Komputer",
        r"\bik\b": "Ilmu Komputer",
        "computer science": "Ilmu Komputer",
        "teknik komputer": "Teknik Komputer",
        r"\btk\b": "Teknik Komputer",
        "rekayasa perangkat lunak": "Rekayasa Perangkat Lunak",
        r"\brpl\b": "Rekayasa Perangkat Lunak",
        "manajemen informatika": "Manajemen Informatika",
        r"\bmi\b": "Manajemen Informatika",
    }

    majors = set()
    for keyword in matched_keywords:
        if keyword in keyword_to_major:
            majors.add(keyword_to_major[keyword])

    if not majors and matched_keywords:
        majors.add("Teknologi Informasi (Umum)")

    return list(majors)