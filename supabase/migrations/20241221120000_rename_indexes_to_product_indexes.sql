-- migration: rename indexes tables to product_indexes
-- purpose: align table names with db-plan.md specification
-- affected tables: indexes → product_indexes, index_aliases → product_index_aliases
-- special considerations: requires renaming foreign key constraints and updating all references
-- date: 2025-11-21

-- Step 1: Rename indexes table to product_indexes
ALTER TABLE indexes RENAME TO product_indexes;

-- Step 2: Rename all indexes on product_indexes table
ALTER INDEX idx_indexes_name RENAME TO idx_product_indexes_name;
ALTER INDEX idx_indexes_category_id RENAME TO idx_product_indexes_category_id;
ALTER INDEX idx_indexes_synonyms RENAME TO idx_product_indexes_synonyms;

-- Step 3: Rename index_aliases table to product_index_aliases
ALTER TABLE index_aliases RENAME TO product_index_aliases;

-- Step 4: Rename the unique index (PostgreSQL doesn't support expressions in UNIQUE CONSTRAINT)
-- Note: PostgreSQL automatically updates foreign key references when renaming tables
-- We use UNIQUE INDEX instead of CONSTRAINT because we need LOWER() function
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'idx_index_aliases_unique_raw_name_index'
    ) THEN
        ALTER INDEX idx_index_aliases_unique_raw_name_index 
            RENAME TO idx_product_index_aliases_unique_raw_name_index;
    END IF;
END $$;

-- Step 5: Rename remaining indexes on product_index_aliases table
ALTER INDEX idx_index_aliases_index_id RENAME TO idx_product_index_aliases_index_id;
ALTER INDEX idx_index_aliases_shop_id RENAME TO idx_product_index_aliases_shop_id;
ALTER INDEX idx_index_aliases_user_id RENAME TO idx_product_index_aliases_user_id;
ALTER INDEX idx_index_aliases_raw_name RENAME TO idx_product_index_aliases_raw_name;

-- Step 6: Update foreign key constraint in bill_items table
-- PostgreSQL should have automatically updated the reference, but we'll verify and fix if needed
-- First, check and drop the old constraint if it exists with old name
DO $$
DECLARE
    constraint_name text;
BEGIN
    -- Find the foreign key constraint name
    SELECT conname INTO constraint_name
    FROM pg_constraint
    WHERE conrelid = 'bill_items'::regclass
    AND confrelid = 'product_indexes'::regclass
    AND contype = 'f';
    
    -- If constraint exists but has old name, rename it
    IF constraint_name IS NOT NULL AND constraint_name LIKE '%indexes%' THEN
        EXECUTE format('ALTER TABLE bill_items RENAME CONSTRAINT %I TO bill_items_index_id_fkey', constraint_name);
    END IF;
END $$;

-- Step 7: Update foreign key constraint in product_index_aliases table
-- Similar check for product_index_aliases
DO $$
DECLARE
    constraint_name text;
BEGIN
    -- Find the foreign key constraint name
    SELECT conname INTO constraint_name
    FROM pg_constraint
    WHERE conrelid = 'product_index_aliases'::regclass
    AND confrelid = 'product_indexes'::regclass
    AND contype = 'f';
    
    -- If constraint exists but has old name, rename it
    IF constraint_name IS NOT NULL AND (constraint_name LIKE '%index_aliases%' OR constraint_name LIKE '%indexes%') THEN
        EXECUTE format('ALTER TABLE product_index_aliases RENAME CONSTRAINT %I TO product_index_aliases_index_id_fkey', constraint_name);
    END IF;
END $$;

-- Step 8: Update table comments to match documentation
COMMENT ON TABLE product_indexes IS 'normalized product dictionary with synonyms and category associations';
COMMENT ON TABLE product_index_aliases IS 'ocr text variants linked to normalized products with confirmation tracking';

-- Verification queries (commented out - uncomment to verify after migration)
-- SELECT table_name FROM information_schema.tables 
-- WHERE table_schema = 'public' 
-- AND table_name IN ('product_indexes', 'product_index_aliases');
-- 
-- SELECT indexname FROM pg_indexes 
-- WHERE tablename IN ('product_indexes', 'product_index_aliases')
-- ORDER BY tablename, indexname;

