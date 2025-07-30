# Use PyTorch CPU-only base image
FROM pytorch/pytorch:latest-cpu

# Set working directory
WORKDIR /app

# Install system dependencies for OpenCV and ML libraries
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install additional backend dependencies
RUN pip install --no-cache-dir fastapi uvicorn

# Copy packages first (shared dependencies)
COPY packages/ ./packages/

# Copy backend-specific code
COPY backend/ ./backend/

# Copy data directory structure (for serving images and accessing configs)
COPY data/ ./data/

# Create directory for persistent data
RUN mkdir -p /app/data/images /app/data/analysis

# Expose FastAPI port
EXPOSE 8000

# Set timezone to Pacific
ENV TZ=America/Los_Angeles
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run the FastAPI backend
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]