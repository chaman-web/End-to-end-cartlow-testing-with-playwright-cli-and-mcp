# Base image with Python 3.12
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Playwright browsers
RUN apt-get update && apt-get install -y \
    wget curl gnupg xvfb \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 \
    libasound2 libpango-1.0-0 libcairo2 \
    libx11-6 libx11-xcb1 libxcb1 libxext6 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium firefox
RUN playwright install-deps chromium firefox

# Copy all project files
COPY . .

# Create reports directory
RUN mkdir -p reports

# Default: run all tests headless
CMD ["python", "-m", "pytest", "tests/", \
     "-v", \
     "--tb=short", \
     "--html=reports/report.html", \
     "--self-contained-html", \
     "--junit-xml=reports/results.xml"]
