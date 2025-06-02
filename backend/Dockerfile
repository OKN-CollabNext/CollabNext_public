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

# Create a non-root user and group
# We use a fixed UID/GID for better reproducibility and to avoid issues with file permissions
# if volumes are mounted from the host.
RUN groupadd -r appgroup --gid=1001 && \
    useradd -r -s /bin/false -g appgroup --uid=1001 appuser

# Set the working directory
WORKDIR /app

# Install the wheels from the builder stage
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels

# Copy over the actual application code and data files
COPY . .

# Create logs directory
RUN mkdir -p logs
# Change ownership of the /app directory to the new user
# This ensures the user can write to this directory if needed (e.g., for logs or temp files, though ideally logs go to stdout)
RUN chown -R appuser:appgroup /app

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV PYTHONPATH=/app

# Environment variables for database (will be overridden by Kubernetes)
ENV DB_HOST=localhost
ENV DB_PORT=5432
ENV DB_NAME=collabnext
ENV DB_USER=postgres
ENV DB_PASSWORD=""
# Recommended: Set PYTHONUNBUFFERED so Python output (like print statements and logs)
# goes directly to the terminal without being buffered. This is good for Docker logging.
ENV PYTHONUNBUFFERED=1


# Expose port 5000 for Gunicorn
EXPOSE 5000

# Switch to the non-root user
USER appuser

# Use Gunicorn as recommended for production
# The appuser will execute this command.
# Gunicorn will bind to port 5000, which is allowed for non-root users.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]