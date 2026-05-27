FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create necessary directories
RUN mkdir -p data/corpus data/indices data/results logs

# Set environment
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Expose port (for future API)
EXPOSE 8000

# Run CLI by default
ENTRYPOINT ["python", "-m", "src.cli"]
CMD ["--help"]
