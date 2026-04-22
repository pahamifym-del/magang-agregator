FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Beritahu Playwright untuk simpan browser di folder yang jelas
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# Install dependensi sistem untuk Playwright + PostgreSQL
# Kita install manual supaya tidak bergantung pada playwright install-deps
# yang bermasalah di Debian terbaru
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    # Dependensi Chromium
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# Copy dan install Python dependencies
COPY requirements/ requirements/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements/development.txt

# Install hanya browser Chromium (tanpa install-deps karena sudah manual di atas)
RUN python -m playwright install chromium

# Copy semua kode
COPY . .

EXPOSE 8000