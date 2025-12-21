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

# IMPORTANT: Supabase CLI uses prepared statements which are not compatible
# with Connection Pooler (port 6543) in transaction mode.
# Convert pooler URL to direct database connection (port 5432) for migrations.
if [[ "$DB_URL" == *":6543/"* ]] || [[ "$DB_URL" == *"pooler.supabase.com"* ]]; then
    echo "WARNING: DATABASE_URL uses Connection Pooler (port 6543)"
    echo "Converting to direct database connection (port 5432) for migrations..."
    echo ""
    
    # Extract project reference from pooler URL
    # Format: postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
    # Convert to: postgresql://postgres.[PROJECT_REF]:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
    
    # Extract project ref from user part (postgres.[PROJECT_REF])
    if [[ "$DB_URL" =~ postgres\.([^:]+): ]]; then
        PROJECT_REF="${BASH_REMATCH[1]}"
        # Replace pooler hostname and port with direct connection
        DB_URL=$(echo "$DB_URL" | sed "s|@[^@]*pooler\.supabase\.com:6543|@db.$PROJECT_REF.supabase.co:5432|" | sed 's|:6543/|:5432/|')
        echo "Converted to direct connection using project ref: $PROJECT_REF"
    else
        # Fallback: just change port from 6543 to 5432
        DB_URL=$(echo "$DB_URL" | sed 's|:6543/|:5432/|')
        echo "Converted port from 6543 to 5432 (host unchanged)"
    fi
    echo ""
fi

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

