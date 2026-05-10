FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies and download spaCy model
RUN uv sync --frozen --no-cache && uv run python -m spacy download en_core_web_sm

# Copy project files
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "python", "main.py"]
