# Use a Python 3.10 slim base image
FROM python:3.10-slim

# Install OpenJDK 11 and utility packages
RUN apt-get update && apt-get install -y \
    openjdk-11-jre-headless \
    curl \
    tar \
    procps \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for Hugging Face Spaces compatibility
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Copy requirements first to leverage Docker cache
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy the rest of the application files
COPY --chown=user:user . .

# Make startup script executable
RUN chmod +x scripts/run_all.sh

# Expose ports for FastAPI (8000) and Streamlit (7860 for Hugging Face)
EXPOSE 8000
EXPOSE 7860

# CMD to start all services
CMD ["/bin/sh", "scripts/run_all.sh"]
