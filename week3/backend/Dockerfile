FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy configuration manifests
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

# Copy everything from your local backend folder into the container's /app folder
COPY . .

EXPOSE 8000

# Tell Uvicorn to run main.py right from the root /app directory
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]