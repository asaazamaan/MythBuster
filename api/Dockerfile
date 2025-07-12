FROM python:3.13-slim AS base

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    docker.io \
    && rm -rf /var/lib/apt/li

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE $API_SERVER_PORT

ENV ENV_MODE=dev

# Use Uvicorn as the ASGI server in production and run FastAPI in development

CMD if [ "$ENV_MODE" = "prod" ]; then \
    uvicorn app:app --host 0.0.0.0 --port $API_SERVER_PORT --workers 4; \
    elif [ "$ENV_MODE" = "dev" ]; then \
    pytest tests/ && python -m uvicorn app:app --reload --host 0.0.0.0 --port $API_SERVER_PORT; \
    else \
    echo "Unknown ENV_MODE: $ENV_MODE" && exit 1; \
    fi
