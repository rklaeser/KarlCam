# Use Python base image and install PyTorch CPU
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY pipeline/requirements.txt .

# Install Python dependencies (with CPU-specific PyTorch)
RUN pip install --no-cache-dir -r requirements.txt -f https://download.pytorch.org/whl/cpu/torch_stable.html

# Copy packages first (shared dependencies)
COPY packages/ ./packages/

# Copy pipeline-specific code
COPY pipeline/*.py ./

# Copy data directory structure
COPY data/ ./data/

# Create directory for persistent data
RUN mkdir -p /app/data/images

# Set timezone to Pacific
ENV TZ=America/Los_Angeles
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Run the collector
CMD ["python", "-u", "collect_fogcam_images.py"]