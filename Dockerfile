FROM python:3.11-slim

# Install system dependencies (git + build essentials)
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source code
COPY . .

# Expose port
EXPOSE 3000

# Start the app with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
