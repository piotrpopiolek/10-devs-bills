#!/bin/bash
set -e

echo "Running database migrations..."

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL environment variable is not set"
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

# Convert DATABASE_URL format if needed (psycopg2 -> postgresql)
DB_URL="${DATABASE_URL//postgresql+psycopg2:/postgresql:}"

# IMPORTANT: Supabase CLI uses prepared statements which are not compatible
# with Connection Pooler (port 6543) in transaction mode.
# Also, Railway doesn't support IPv6, so we need to use direct connection with IPv4.
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
        # Use db.[PROJECT_REF].supabase.co which should resolve to IPv4
        DB_URL=$(echo "$DB_URL" | sed "s|@[^@]*pooler\.supabase\.com:6543|@db.$PROJECT_REF.supabase.co:5432|" | sed 's|:6543/|:5432/|')
        echo "Converted to direct connection using project ref: $PROJECT_REF"
    else
        # Fallback: just change port from 6543 to 5432
        DB_URL=$(echo "$DB_URL" | sed 's|:6543/|:5432/|')
        echo "Converted port from 6543 to 5432 (host unchanged)"
    fi
    echo ""
fi

echo "Using database URL for migrations: ${DB_URL//:[^@]*@/:***@}"
echo ""

# Change to supabase directory for proper context
cd /supabase || {
    echo "ERROR: Cannot access /supabase directory"
    exit 1
}

# Try Supabase CLI first, but fallback to psql if it fails with prepared statement errors
USE_PSQL=false

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo "WARNING: psql is not installed, will only try Supabase CLI"
fi

# Try Supabase CLI if available
if command -v supabase &> /dev/null; then
    echo "Attempting migrations with Supabase CLI..."
    echo ""
    
    # Force IPv4 by setting environment variables
    export GODEBUG=netdns=go
    
    if supabase db push --db-url "$DB_URL" 2>&1 | tee /tmp/migration_output.log; then
        echo ""
        echo "✓ Database migrations completed successfully with Supabase CLI!"
        exit 0
    else
        MIGRATION_ERROR=$(cat /tmp/migration_output.log)
        if [[ "$MIGRATION_ERROR" == *"prepared statement"* ]] || [[ "$MIGRATION_ERROR" == *"42P05"* ]]; then
            echo ""
            echo "WARNING: Supabase CLI failed due to prepared statement error"
            echo "Falling back to psql for migrations..."
            echo ""
            USE_PSQL=true
        else
            echo ""
            echo "✗ ERROR: Failed to apply database migrations with Supabase CLI"
            echo "  Check the error messages above for details"
            # If psql is available, try it as fallback
            if command -v psql &> /dev/null; then
                echo "Attempting fallback to psql..."
                USE_PSQL=true
            else
                exit 1
            fi
        fi
    fi
else
    echo "Supabase CLI not found, using psql for migrations..."
    USE_PSQL=true
fi

# Use psql to apply migrations directly
if [ "$USE_PSQL" = true ]; then
    if ! command -v psql &> /dev/null; then
        echo "✗ ERROR: psql is not installed and Supabase CLI failed"
        exit 1
    fi
    
    echo "Applying migrations using psql..."
    echo ""
    
    # psql supports postgresql:// URLs directly
    # Apply migrations in order (sorted by filename)
    MIGRATION_COUNT=0
    APPLIED_COUNT=0
    
    for migration_file in $(ls -1 migrations/*.sql 2>/dev/null | sort); do
        if [ -f "$migration_file" ]; then
            MIGRATION_COUNT=$((MIGRATION_COUNT + 1))
            migration_name=$(basename "$migration_file")
            migration_version=$(basename "$migration_file" .sql)
            
            echo "[$MIGRATION_COUNT] Applying: $migration_name"
            
            # Check if migration was already applied (if tracking table exists)
            # This is optional - if table doesn't exist, we'll just try to apply
            TRACKING_CHECK=$(psql "$DB_URL" -t -A -c "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'supabase_migrations' AND table_name = 'schema_migrations')" 2>/dev/null || echo "f")
            
            if [ "$TRACKING_CHECK" = "t" ]; then
                # Check if this migration was already applied
                ALREADY_APPLIED=$(psql "$DB_URL" -t -A -c "SELECT EXISTS (SELECT 1 FROM supabase_migrations.schema_migrations WHERE version = '$migration_version')" 2>/dev/null || echo "f")
                if [ "$ALREADY_APPLIED" = "t" ]; then
                    echo "  ⊘ Already applied, skipping"
                    APPLIED_COUNT=$((APPLIED_COUNT + 1))
                    continue
                fi
            fi
            
            # Apply migration
            if psql "$DB_URL" -f "$migration_file" -v ON_ERROR_STOP=1 > /tmp/migration_${migration_version}.log 2>&1; then
                echo "  ✓ Successfully applied"
                APPLIED_COUNT=$((APPLIED_COUNT + 1))
                
                # Try to update tracking table (if it exists)
                psql "$DB_URL" -c "INSERT INTO supabase_migrations.schema_migrations (version, statements, name) VALUES ('$migration_version', ARRAY[]::text[], '$migration_name') ON CONFLICT (version) DO NOTHING" 2>/dev/null || true
            else
                EXIT_CODE=$?
                echo "  ✗ Failed (exit code: $EXIT_CODE)"
                echo "  Error output:"
                cat /tmp/migration_${migration_version}.log | head -5
                echo ""
                echo "  Full error log saved to: /tmp/migration_${migration_version}.log"
                exit 1
            fi
            echo ""
        fi
    done
    
    echo "✓ Migrations completed: $APPLIED_COUNT/$MIGRATION_COUNT applied"
fi

