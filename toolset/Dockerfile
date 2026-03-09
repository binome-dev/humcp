# Toolset (HuMCP) Dockerfile for development with hot reload
FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    # For pytesseract OCR
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Install uv (fast package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    UV_SYSTEM_PYTHON=1

# Copy dependency files first for better caching
# Include README.md as it's referenced in pyproject.toml
COPY toolset/pyproject.toml toolset/README.md ./

# Install toolset and its dependencies (creates .venv)
# --no-sources ignores workspace references for shared
RUN uv sync --no-cache --no-sources

# Copy shared package and install into the venv (not system Python)
COPY shared /tmp/shared
RUN uv pip install --no-cache --python /app/.venv/bin/python /tmp/shared && rm -rf /tmp/shared

# Put the venv on PATH so uvicorn is directly runnable
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY toolset/ .

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8003/ || exit 1

# Run with hot reload for development
# Use uvicorn directly (not uv run) to avoid re-parsing workspace sources
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8003", "--reload"]
