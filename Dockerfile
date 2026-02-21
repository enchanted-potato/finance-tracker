FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

ENV PYTHONPATH=/app

EXPOSE 8501

CMD ["uv", "run", "streamlit", "run", "frontend/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
