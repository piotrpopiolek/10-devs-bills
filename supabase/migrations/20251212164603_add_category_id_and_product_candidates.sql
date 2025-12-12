-- ============================================================================
-- Migration: Add category_id to bill_items and create product_candidates table
-- ============================================================================
-- Purpose: 
--   1. Adds category_id column to bill_items table with foreign key to categories
--   2. Creates product_candidates table for managing product candidate groups
--      before they become approved product indexes
--
-- Affected objects:
--   - Table: bill_items (add column category_id)
--   - Table: product_candidates (new table)
--   - Indexes: GIN index for fuzzy search on product_candidates.representative_name
--              Partial index on product_candidates.status
--
-- Special considerations:
--   - Uses pg_trgm extension (already enabled) for fuzzy text search
--   - product_candidates.category_id allows NULL (can be set later by LLM or user)
--   - bill_items.category_id allows NULL (can be set later by LLM or user)
-- ============================================================================

-- ============================================================================
-- Step 1: Add category_id column to bill_items
-- ============================================================================

-- Add category_id column as nullable with foreign key constraint
alter table bill_items
    add column category_id integer,
    add constraint bill_items_category_id_fkey 
        foreign key (category_id) 
        references categories(id) 
        on delete restrict;

-- Add index for performance
create index idx_bill_items_category_id on bill_items(category_id);

-- ============================================================================
-- Step 2: Create product_candidates table
-- ============================================================================

create table product_candidates (
    id serial primary key,
    
    -- Nazwa reprezentatywna dla grupy (np. pierwszy original_text z grupy, lub najbardziej popularny wczesny)
    representative_name text not null,
    
    -- Liczba potwierdzeń, BillItem pasujący do tej grupy
    user_confirmations integer not null default 0,
    
    -- Kategoria dopasowana przez model LLM lub wybrana przez użytkownika z listy dostępnych kategorii
    category_id integer references categories(id) on delete set null,
    
    -- ID utworzonego ProductIndex po osiągnięciu progu (jeśli kandydat został zaakceptowany)
    product_index_id integer references product_indexes(id) on delete set null,
    
    -- Status kandydata: 'pending', 'approved', 'rejected'
    status varchar(50) not null default 'pending',
    
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- Add comment to table
comment on table product_candidates is 'Product candidates awaiting approval before becoming product indexes';

-- ============================================================================
-- Step 3: Create indexes for product_candidates
-- ============================================================================

-- Indeks na nazwie reprezentatywnej dla szybkiego fuzzy search
-- Uses GIN index with trigram operator class for efficient text similarity searches
create index idx_product_candidates_name_trgm 
    on product_candidates 
    using gin(lower(representative_name) gin_trgm_ops);

-- Indeks na statusie (partial index for pending candidates)
create index idx_product_candidates_status 
    on product_candidates(status) 
    where status = 'pending';

-- Additional indexes for foreign keys (for join performance)
create index idx_product_candidates_category_id 
    on product_candidates(category_id);

create index idx_product_candidates_product_index_id 
    on product_candidates(product_index_id);