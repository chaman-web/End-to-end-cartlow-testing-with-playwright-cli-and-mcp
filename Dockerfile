# ── Stage 1: Base image ────────────────────────────────────────────────────────
FROM python:3.12-slim AS base

# Prevent .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ── Stage 2: System dependencies ──────────────────────────────────────────────
FROM base AS system-deps

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl gnupg ca-certificates \
    # Playwright browser dependencies
    libnss3 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 \
    libasound2 libpango-1.0-0 libcairo2 \
    libx11-6 libx11-xcb1 libxcb1 libxext6 \
    libglib2.0-0 libdbus-1-3 \
    fonts-liberation fonts-noto-color-emoji \
    # Virtual display (headless fallback)
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# ── Stage 3: Python dependencies ──────────────────────────────────────────────
FROM system-deps AS python-deps

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (chromium + firefox only — skip webkit to save space)
RUN python -m playwright install chromium firefox && \
    python -m playwright install-deps chromium firefox

# ── Stage 4: Final image ───────────────────────────────────────────────────────
FROM python-deps AS final

WORKDIR /app

# Copy project files (respects .dockerignore)
COPY . .

# Create output directories
RUN mkdir -p reports/screenshots

# ── Environment defaults (override at runtime via -e flags) ───────────────────
ENV ENV=staging \
    HEADLESS=true \
    SLOW_MO=0 \
    TEST_EMAIL="" \
    TEST_PASSWORD=""

# ── Health check — verify pytest is importable ────────────────────────────────
RUN python -m pytest --version

# ── Default command: run full test suite headless ─────────────────────────────
# Override at runtime:
#   docker run cartlow-playwright python -m pytest "tests/intl regression" --browser chromium -n 4
CMD ["python", "-m", "pytest", "tests/", \
     "--browser", "chromium", \
     "-n", "4", \
     "--dist=loadfile", \
     "-v", \
     "--tb=short", \
     "--html=reports/report.html", \
     "--self-contained-html", \
     "--junit-xml=reports/results.xml"]
