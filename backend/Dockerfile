FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
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

COPY requirements/ requirements/

# Dengan ini:
ARG ENVIRONMENT=production
RUN pip install --no-cache-dir --upgrade pip && \
    if [ "$ENVIRONMENT" = "development" ]; then \
        pip install --no-cache-dir -r requirements/development.txt; \
    else \
        pip install --no-cache-dir -r requirements/production.txt; \
    fi

# Patch playwright_stealth
RUN python -c "\
path = '/usr/local/lib/python3.12/site-packages/playwright_stealth/stealth.py'; \
f = open(path); content = f.read(); f.close(); \
content = content.replace('import pkg_resources', 'import importlib.resources as _ir\nclass _FPR:\n    def resource_string(self, p, r):\n        return _ir.files(p).joinpath(r).read_bytes()\npkg_resources = _FPR()'); \
f = open(path, \"w\"); f.write(content); f.close(); \
print('playwright_stealth patched!')"

RUN python -m playwright install chromium

COPY . .

EXPOSE 8000