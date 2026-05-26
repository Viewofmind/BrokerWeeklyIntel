# =============================================================================
# BrokerWeeklyIntel - Backend Dockerfile (Python FastAPI)
# =============================================================================
FROM python:3.11-slim

WORKDIR /app

# System deps for some Python packages (reportlab, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p data/historical reports

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=sqlite:///./data/broker_intel.db

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
