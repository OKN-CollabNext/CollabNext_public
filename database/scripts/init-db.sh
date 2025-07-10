#!/bin/bash
set -e

# This script runs after the SQL dump is loaded
# Use this for additional database setup, user creation, permissions, etc.

echo "Starting additional database initialization..."

# Create additional users if needed
# psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
#     CREATE USER app_user WITH PASSWORD 'app_password';
#     GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
#     GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
# EOSQL

# Set up any indexes or optimizations
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Add any additional indexes for performance
    -- CREATE INDEX IF NOT EXISTS idx_authors_name ON authors(name);
    -- CREATE INDEX IF NOT EXISTS idx_institutions_name ON institutions(name);
    
    -- Update statistics
    ANALYZE;
EOSQL

echo "Additional database initialization completed." 