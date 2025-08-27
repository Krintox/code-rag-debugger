# Use slim Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system deps (curl useful for health/debug)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Use environment variables from .env (docker-compose handles it)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
