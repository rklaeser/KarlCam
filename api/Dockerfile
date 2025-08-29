FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY api/requirements.txt ./

# Install dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY api/main.py ./

# Run with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]