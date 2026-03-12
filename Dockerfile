# --- Stage 1: Build Frontend ---
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install

# ARG to bust cache on every build if passed, or just by modifying this line
ARG CACHE_BUST=7

COPY frontend/ ./
RUN npm run build

# --- Stage 2: Runtime Environment ---
FROM python:3.11-slim AS runtime

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Setup Backend
COPY backend/requirements.txt ./
# Force CPU-only PyTorch and install dependencies
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

# Set Python Path to include current directory
ENV PYTHONPATH=.

# Set explicit cache directories for models and ensure they are writable
ENV HF_HOME=/app/backend/data/models
ENV SENTENCE_TRANSFORMERS_HOME=/app/backend/data/models

# Pre-download the embedding model (baked into image)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy Backend Code
COPY backend/ ./backend

# Copy Frontend Build
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Ensure data directories exist and are writable by user 1000 (Hugging Face)
RUN mkdir -p backend/data/uploads backend/data/reports backend/data/vectors backend/data/models \
    && chown -R 1000:1000 /app

USER 1000

WORKDIR /app/backend

# Default port for Hugging Face
ENV PORT=7860

# Port for Hugging Face Spaces
EXPOSE 7860

# Start unified app (FastAPI serves both API and Static Frontend from /app/frontend/dist)
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
