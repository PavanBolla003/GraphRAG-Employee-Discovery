# Use a Python 3.10 base image (contains standard development tools)
FROM python:3.10

# Install OpenJDK 11 and utility packages as root
RUN apt-get update && apt-get install -y \
    openjdk-11-jre-headless \
    curl \
    tar \
    procps \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies globally as root
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# Grant full read/write/execute permissions on /app for the runtime non-root user (UID 1000)
RUN chmod -R 777 /app

# Set Home directory to /app so that pip/cache operations write to a writable path
ENV HOME=/app \
    PATH=/app/.local/bin:$PATH

# Make startup script executable
RUN chmod +x scripts/run_all.sh

# Expose ports for FastAPI (8000) and Streamlit (7860 for Hugging Face)
EXPOSE 8000
EXPOSE 7860

# CMD to start all services
CMD ["/bin/sh", "scripts/run_all.sh"]
