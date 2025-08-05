# Base system dependencies
FROM python:3.11-slim as system-base

# Install system dependencies for OpenCV and ML libraries
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# CUDA libraries layer
FROM system-base as cuda-base
RUN pip install --no-cache-dir \
    nvidia-cublas-cu12==12.4.5.8 \
    nvidia-cufft-cu12==11.2.1.3 \
    nvidia-curand-cu12==10.3.5.147 \
    nvidia-cusolver-cu12==11.6.1.9 \
    nvidia-cusparse-cu12==12.3.1.170 \
    nvidia-cusparselt-cu12==0.6.2 \
    nvidia-nccl-cu12==2.21.5 \
    nvidia-nvtx-cu12==12.4.127 \
    nvidia-nvjitlink-cu12==12.4.127 \
    nvidia-cuda-nvrtc-cu12==12.4.127 \
    nvidia-cuda-runtime-cu12==12.4.127 \
    nvidia-cuda-cupti-cu12==12.4.127 \
    nvidia-cudnn-cu12==9.1.0.70

# PyTorch layer (depends on CUDA)
FROM cuda-base as pytorch-base
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