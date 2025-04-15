FROM python:3.11-slim AS builder
WORKDIR /app

# Install system dependencies - combine update and install in one RUN to reduce cache layers
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry and add to PATH
ENV POETRY_HOME=/opt/poetry
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && cd /usr/local/bin \
    && ln -s /opt/poetry/bin/poetry poetry

# Copy only the files needed for dependency installation to leverage layer caching
# Changes to only application code won't trigger dependency reinstallation
COPY pyproject.toml poetry.lock* ./

# Install dependencies - cached unless pyproject.toml or poetry.lock changes
# --no-root flag prevents installing the project in editable mode
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Application stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy only the necessary files from builder
# These layers are cached unless dependencies change
# We only copy the installed packages and binaries
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code - cached unless application code changes
# It's placed after dependency installation to optimize caching
COPY . .

# Set environment variables - cached and rarely change
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]