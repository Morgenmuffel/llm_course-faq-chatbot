# ===================================
# FILE: Dockerfile
# ===================================
FROM python:3.11.8-slim-bookworm

WORKDIR /app

# Update system packages to address vulnerabilities
RUN apt-get update && apt-get upgrade -y && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Aggressive dependency cleanup and installation
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    # Remove all potentially conflicting packages first
    pip uninstall -y openai httpx httpcore elasticsearch urllib3 requests certifi anyio sniffio || true && \
    # Clear pip cache completely
    pip cache purge && \
    # Install with no cache and specific order to prevent conflicts
    pip install --no-cache-dir --no-deps urllib3==1.26.18 && \
    pip install --no-cache-dir --no-deps certifi==2023.7.22 && \
    pip install --no-cache-dir --no-deps sniffio==1.3.0 && \
    pip install --no-cache-dir --no-deps anyio==4.2.0 && \
    pip install --no-cache-dir --no-deps httpcore==0.18.0 && \
    pip install --no-cache-dir --no-deps httpx==0.24.1 && \
    # Install remaining packages with dependencies
    pip install --no-cache-dir -r requirements.txt && \
    # Verify critical package versions
    pip show openai httpx httpcore | grep -E "^(Name|Version):"

# Copy verification script and application code
COPY verify_deps.py .
COPY . .

# Run dependency verification during build
RUN python verify_deps.py

# Expose Streamlit port
EXPOSE 8501

# Command to run the application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
