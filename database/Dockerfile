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
ENV POSTGRES_DB=collabnext
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=changeme123
ENV PGDATA=/var/lib/postgresql/data

# Create directory for initialization scripts
RUN mkdir -p /docker-entrypoint-initdb.d

# Copy SQL dump file and initialization scripts
# Replace 'path/to/your/dump.sql' with actual path to your SQL dump
COPY ./sql-dump/collabnext_dump.sql /docker-entrypoint-initdb.d/01-init-database.sql
COPY ./scripts/init-db.sh /docker-entrypoint-initdb.d/02-init-scripts.sh

# Copy custom SQL functions if needed
COPY ./sql-functions/mup_sql_functions.sql /docker-entrypoint-initdb.d/03-functions.sql

# Make scripts executable
RUN chmod +x /docker-entrypoint-initdb.d/*.sh

# Create custom postgresql.conf for optimizations (optional)
COPY ./config/postgresql.conf /etc/postgresql/postgresql.conf

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD pg_isready -U $POSTGRES_USER -d $POSTGRES_DB || exit 1

# Expose PostgreSQL port
EXPOSE 5432

# Use the default postgres entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"] 