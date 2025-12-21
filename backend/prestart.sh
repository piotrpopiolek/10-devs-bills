#!/bin/bash
set -e

echo "Running database migrations with Supabase CLI..."

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL environment variable is not set"
    exit 1
fi

# Check if Supabase CLI is installed
if ! command -v supabase &> /dev/null; then
    echo "ERROR: Supabase CLI is not installed"
    exit 1
fi

# Check if migrations directory exists
MIGRATIONS_DIR="/supabase/migrations"
if [ ! -d "$MIGRATIONS_DIR" ]; then
    echo "WARNING: Migrations directory not found at $MIGRATIONS_DIR"
    echo "Skipping migrations..."
    exit 0
fi

# Check if there are any migration files
MIGRATION_FILES=$(ls -1 "$MIGRATIONS_DIR"/*.sql 2>/dev/null | wc -l)
if [ "$MIGRATION_FILES" -eq 0 ]; then
    echo "WARNING: No migration files found in $MIGRATIONS_DIR"
    echo "Skipping migrations..."
    exit 0
fi

echo "Found $MIGRATION_FILES migration file(s)"
echo ""

# Use Supabase CLI to push migrations
# This will apply all migrations in the migrations directory
# The --db-url flag allows us to use the DATABASE_URL directly
# Note: supabase db push applies migrations in order and tracks applied migrations
echo "Applying migrations using: supabase db push --db-url \$DATABASE_URL"
echo ""

# Convert DATABASE_URL format if needed (psycopg2 -> postgresql)
# Supabase CLI expects postgresql:// format
DB_URL="${DATABASE_URL//postgresql+psycopg2:/postgresql:}"

echo "Converted DATABASE_URL: $DB_URL"

# Change to supabase directory for proper context
cd /supabase || {
    echo "ERROR: Cannot access /supabase directory"
    exit 1
}

# Run supabase db push
# This command will:
# 1. Read migrations from ./migrations directory
# 2. Apply them in order
# 3. Track which migrations have been applied
# --db-url: Direct database connection URL (bypasses Supabase project linking)
# --password: Will prompt if needed (or use env var)
echo "Pushing migrations to database..."
if supabase db push --db-url "$DB_URL"; then
    echo ""
    echo "✓ Database migrations completed successfully!"
else
    echo ""
    echo "✗ ERROR: Failed to apply database migrations"
    echo "  Check the error messages above for details"
    exit 1
fi

