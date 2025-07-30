# Use Python 3.11 slim image
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
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

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