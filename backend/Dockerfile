# -------------------------------------------------------
#  Step 1 (Builder Image): Build Python wheel dependencies
# -------------------------------------------------------
FROM python:3.12-slim AS builder

# Install build tools and PostgreSQL development headers, then clean up
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt requirements.txt

# Build wheels for all dependencies
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# -------------------------------------------------------
#  Step 2 (Final Image): Copy only what we need
# -------------------------------------------------------
FROM python:3.12-slim

# Install runtime dependencies for PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install the wheels from the builder stage
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels

# Copy over the actual application code and data files
COPY . .

# Create logs directory
RUN mkdir -p logs

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV PYTHONPATH=/app

# Environment variables for database (will be overridden by Kubernetes)
ENV DB_HOST=localhost
ENV DB_PORT=5432
ENV DB_NAME=collabnext
ENV DB_USER=postgres
ENV DB_PASSWORD=

# Expose port 5000 for Gunicorn
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Use Gunicorn as recommended for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:app"] 