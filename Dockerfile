# Use a Python 3.10 base image (contains build tools like gcc/g++)
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

# Create a non-root user for Hugging Face Spaces compatibility
RUN useradd -m -u 1000 user && chown -R user:user /app
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Copy the rest of the application files as user
COPY --chown=user:user . .

# Make startup script executable
RUN chmod +x scripts/run_all.sh

# Expose ports for FastAPI (8000) and Streamlit (7860 for Hugging Face)
EXPOSE 8000
EXPOSE 7860

# CMD to start all services
CMD ["/bin/sh", "scripts/run_all.sh"]
