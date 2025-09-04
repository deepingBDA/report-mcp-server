# Multi-stage build for better caching
FROM python:3.11-slim as base

# Install system dependencies and fonts
RUN apt-get update && apt-get install -y \
    git \
    curl \
    openssh-client \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    fontconfig \
    && fc-cache -fv \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies stage
FROM base as python-deps
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright stage (this takes the longest)
FROM python-deps as playwright-stage
RUN playwright install chromium \
    && playwright install-deps chromium \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/*

# Final stage
FROM playwright-stage
WORKDIR /app

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p data/reports data/logs

# Expose port
EXPOSE 8002

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]