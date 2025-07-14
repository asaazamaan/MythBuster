FROM python:3.11-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    g++ \
    docker.io \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install basic requirements first
COPY requirements.txt .

# Install packages in stages to avoid timeouts
RUN pip install --no-cache-dir --upgrade pip

# Install basic packages first
RUN pip install --no-cache-dir \
    fastapi==0.115.5 \
    uvicorn==0.32.0 \
    python-dotenv==1.0.1 \
    psycopg2==2.9.10 \
    pytest==8.3.3

# Install ML packages separately with longer timeout
RUN pip install --no-cache-dir --timeout=1000 \
    torch==2.1.2 \
    torchaudio==2.1.2 \
    transformers==4.36.2

# Install remaining packages
RUN pip install --no-cache-dir \
    yt-dlp==2023.12.30 \
    datasets==2.15.0

# Install all other remaining packages
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE $API_SERVER_PORT

ENV ENV_MODE=dev

CMD if [ "$ENV_MODE" = "prod" ]; then \
    uvicorn app:app --host 0.0.0.0 --port $API_SERVER_PORT --workers 4; \
    elif [ "$ENV_MODE" = "dev" ]; then \
    pytest tests/ && python -m uvicorn app:app --reload --host 0.0.0.0 --port $API_SERVER_PORT; \
    else \
    echo "Unknown ENV_MODE: $ENV_MODE" && exit 1; \
    fi