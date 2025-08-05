# Shared base image with PyTorch - this is the expensive layer
FROM python:3.11-slim as pytorch-base

# Install system dependencies for OpenCV and ML libraries
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch and torchvision (CPU version) - shared across all services
RUN pip install --no-cache-dir torch==2.6.0 torchvision==0.21.0 -f https://download.pytorch.org/whl/cpu/torch_stable.html

# Set working directory
WORKDIR /app

# Set timezone to Pacific
ENV TZ=America/Los_Angeles
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Pipeline service
FROM pytorch-base as pipeline

# Copy requirements and install pipeline-specific dependencies
COPY pipeline/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy packages first (shared dependencies)
COPY packages/ ./packages/

# Copy pipeline-specific code
COPY pipeline/*.py ./

# Copy data directory structure
COPY data/ ./data/

# Create directory for persistent data
RUN mkdir -p /app/data/images

# Run the collector
CMD ["python", "-u", "collect_fogcam_images.py"]

# Backend service
FROM pytorch-base as backend

# Copy requirements and install backend-specific dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

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

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run the FastAPI backend
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]