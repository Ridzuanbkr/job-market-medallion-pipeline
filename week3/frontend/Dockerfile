FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy package configurations
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

# Copy everything (including your src/ templates folder)
COPY . .

EXPOSE 8501

# Run your frontend FastAPI app on port 8501
CMD ["uv", "run", "uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8501"]