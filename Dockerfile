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

# Set up working directory exactly as in official HF templates
WORKDIR /code

# Copy requirements and install
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy all application files
COPY . .

# Grant full read/write/execute permissions on /code for HF runtime UID 1000
RUN chmod -R 777 /code

# Set Home directory to /code so that pip/cache operations write to a writable path
ENV HOME=/code \
    PATH=/code/.local/bin:$PATH

# Make startup script executable
RUN chmod +x /code/scripts/run_all.sh

# Expose Streamlit port (7860 for Hugging Face)
EXPOSE 7860

# CMD to start all services
CMD ["/bin/sh", "/code/scripts/run_all.sh"]
