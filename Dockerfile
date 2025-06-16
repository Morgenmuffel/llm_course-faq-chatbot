# ===================================
# FILE: Dockerfile
# ===================================
FROM python:3.11.8-slim-bookworm

WORKDIR /app

# Update system packages to address vulnerabilities
RUN apt-get update && apt-get upgrade -y && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Clean pip installation to prevent version conflicts
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    # Remove any pre-installed conflicting packages
    pip uninstall -y openai httpx || true && \
    # Install dependencies with specific resolver and no-deps for problematic packages
    pip install --no-cache-dir --force-reinstall -r requirements.txt && \
    # Verify the correct versions are installed
    pip show openai httpx

# Copy verification script and application code
COPY verify_deps.py .
COPY . .

# Run dependency verification during build
RUN python verify_deps.py

# Expose Streamlit port
EXPOSE 8501

# Command to run the application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
