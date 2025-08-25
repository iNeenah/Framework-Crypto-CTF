# Dockerfile for Advanced Crypto CTF Framework
FROM python:3.9-slim

LABEL maintainer="iNeenah"
LABEL description="Advanced ML-Powered CTF Cryptography Solver Framework"
LABEL version="1.0.0"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libgmp-dev \
    libmpfr-dev \
    libmpc-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create necessary directories
RUN mkdir -p data/expert_writeups models/expert challenges/uploaded challenges/solved

# Expose port (if web interface is implemented)
EXPOSE 8000

# Default command
CMD ["python", "main.py"]