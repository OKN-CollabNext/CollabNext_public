# -------------------------------------------------------
#  PostgreSQL 17 Database Container with SQL Dump Initialization
# -------------------------------------------------------
FROM postgres:17-alpine

# Install additional tools for database operations
RUN apk add --no-cache \
    curl \
    gzip \
    && rm -rf /var/cache/apk/*

# Set environment variables for PostgreSQL
ENV POSTGRES_DB=openalex
ENV POSTGRES_USER=openalexreader
ENV POSTGRES_PASSWORD=collabnext2024reader!
ENV PGDATA=/var/lib/postgresql/data

# Create directory for initialization scripts
RUN mkdir -p /docker-entrypoint-initdb.d

# Copy initialization scripts if they exist
COPY ./scripts/ /docker-entrypoint-initdb.d/

# Copy custom SQL functions if they exist
COPY ./sql-functions/ /docker-entrypoint-initdb.d/

# Make scripts executable
RUN find /docker-entrypoint-initdb.d -name "*.sh" -exec chmod +x {} \;

# Copy custom postgresql.conf for optimizations
COPY ./config/postgresql.conf /etc/postgresql/postgresql.conf

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD pg_isready -U $POSTGRES_USER -d $POSTGRES_DB || exit 1

# Expose PostgreSQL port
EXPOSE 5432

# Use the default postgres entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"] 