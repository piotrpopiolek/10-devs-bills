-- ============================================================================
-- Migration: Initial database schema for Bills MVP
-- ============================================================================
-- Purpose: Creates the complete database schema for the Bills application
--          including all tables, types, indexes, and constraints.
--
-- Affected objects:
--   - Extension: pg_trgm (for fuzzy search)
--   - ENUM types: processing_status, verification_source, 
--                 telegram_message_status, telegram_message_type
--   - Tables: users, shops, categories, product_indexes, 
--            product_index_aliases, bills, bill_items, telegram_messages
--   - Indexes: Multiple indexes for performance optimization
--   - Constraints: Foreign keys, unique constraints, check constraints
--
-- Special considerations:
--   - Uses pg_trgm extension for fuzzy search on product names
--   - Case-insensitive unique constraints using LOWER() function
--   - GIN indexes for JSONB and text search
--   - Partial indexes for filtered queries
-- ============================================================================

-- Enable pg_trgm extension for fuzzy text search
-- This extension is required for trigram-based similarity searches
create extension if not exists pg_trgm;

-- ============================================================================
-- ENUM Types
-- ============================================================================

-- Processing status for bills (tracking OCR and AI processing pipeline)
create type processing_status as enum ('pending', 'processing', 'completed', 'error');

-- Source of verification for bill items (who/what verified the item)
create type verification_source as enum ('auto', 'user', 'admin');

-- Status of telegram messages (delivery tracking)
create type telegram_message_status as enum ('sent', 'delivered', 'read', 'failed');

-- Type of telegram message content
create type telegram_message_type as enum ('text', 'photo', 'document', 'audio', 'video', 'voice', 'sticker');

-- ============================================================================
-- Table: users
-- ============================================================================
-- Stores user information linked to Telegram external_id
-- Note: No personal data stored per PRD requirements
create table users (
    id serial primary key,
    external_id bigint not null unique,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    is_active boolean not null default true
);

-- Index for fast lookup by Telegram external_id (unique constraint already exists)
create unique index idx_users_external_id on users(external_id);

-- ============================================================================
-- Table: shops
-- ============================================================================
-- Stores shop/store information
-- Unique constraint on (name, address) is case-sensitive
-- Application should normalize data before insert
create table shops (
    id serial primary key,
    name varchar(255) not null,
    address varchar(255),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint uq_shops_name_address unique (name, address)
);

-- Index for shop name searches
create index idx_shops_name on shops(name);

-- ============================================================================
-- Table: categories
-- ============================================================================
-- Hierarchical category structure for product classification
-- parent_id allows tree structure (self-referencing)
create table categories (
    id serial primary key,
    name varchar(255) not null unique,
    parent_id integer references categories(id) on delete restrict,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- Indexes for category lookups and hierarchy navigation
create index idx_categories_name on categories(name);
create index idx_categories_parent_id on categories(parent_id);

-- ============================================================================
-- Table: product_indexes
-- ============================================================================
-- Dictionary of normalized products (the "golden list")
-- This is the canonical product reference table
create table product_indexes (
    id serial primary key,
    name varchar(255) not null,
    synonyms jsonb,
    category_id integer references categories(id) on delete restrict,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- GIN trigram index for fuzzy search on product names (requires pg_trgm)
create index idx_product_indexes_name_trgm on product_indexes using gin(name gin_trgm_ops);

-- Case-insensitive unique constraint on product name
create unique index uq_product_indexes_name_lower on product_indexes(lower(name));

-- Index for category-based product queries
create index idx_product_indexes_category_id on product_indexes(category_id);

-- GIN index for JSONB synonyms field (efficient JSON queries)
create index idx_product_indexes_synonyms on product_indexes using gin(synonyms);

-- ============================================================================
-- Table: product_index_aliases
-- ============================================================================
-- Stores OCR variants/aliases for products
-- Tracks how often each alias is confirmed (confirmations_count)
-- Links to shops and users for context
create table product_index_aliases (
    id serial primary key,
    raw_name text not null,
    index_id integer not null references product_indexes(id) on delete cascade,
    confirmations_count integer not null default 0,
    first_seen_at timestamptz default now(),
    last_seen_at timestamptz,
    locale varchar(10) default 'pl_PL',
    shop_id integer references shops(id) on delete set null,
    user_id integer references users(id) on delete set null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- Indexes for alias lookups
create index idx_product_index_aliases_index_id on product_index_aliases(index_id);
create index idx_product_index_aliases_shop_id on product_index_aliases(shop_id);
create index idx_product_index_aliases_user_id on product_index_aliases(user_id);
create unique index uq_alias_raw_name_index on product_index_aliases(lower(raw_name), index_id);

-- ============================================================================
-- Table: bills
-- ============================================================================
-- Main table for storing receipt/bill information
-- Tracks processing status and image lifecycle
create table bills (
    id serial primary key,
    bill_date timestamptz not null,
    total_amount numeric(12,2),
    image_url text,
    image_hash varchar(64),
    image_expires_at timestamptz,
    image_status varchar(50) default 'active',
    status processing_status not null default 'pending',
    error_message text,
    user_id integer not null references users(id) on delete cascade,
    shop_id integer references shops(id) on delete set null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint check_total_amount_positive check (total_amount >= 0)
);

-- Composite index for user expense reports (ordered by date descending)
create index idx_bills_user_id_bill_date on bills(user_id, bill_date desc);

-- Index for filtering bills by processing status
create index idx_bills_status on bills(status);

-- Index for shop-based queries
create index idx_bills_shop_id on bills(shop_id);

-- Partial index for image expiration cleanup job (only indexes non-null values)
create index idx_bills_image_expires_at on bills(image_expires_at) where image_expires_at is not null;

-- ============================================================================
-- Table: bill_items
-- ============================================================================
-- Individual items/products from a bill/receipt
-- Links to product_indexes for normalized product data
create table bill_items (
    id serial primary key,
    quantity numeric(10,4) not null,
    unit_price numeric(12,2) not null,
    total_price numeric(12,2) not null,
    original_text text,
    confidence_score numeric(3,2), -- OCR confidence score (0.00-1.00)
    is_verified boolean not null default false,
    verification_source verification_source not null default 'auto',
    bill_id integer not null references bills(id) on delete cascade,
    index_id integer references product_indexes(id) on delete set null,
    created_at timestamptz not null default now(),
    constraint check_quantity_positive check (quantity > 0),
    constraint check_unit_price_non_negative check (unit_price >= 0)
);

-- Index for bill-to-items relationship
create index idx_bill_items_bill_id on bill_items(bill_id);

-- Index for product-based queries
create index idx_bill_items_index_id on bill_items(index_id);

-- Partial index for unverified items (workflow optimization)
-- Only indexes items that need verification (is_verified = false)
create index idx_bill_items_unverified on bill_items(is_verified) where is_verified = false;

-- ============================================================================
-- Table: telegram_messages
-- ============================================================================
-- Stores Telegram messages sent to/from the bot
-- Links messages to bills and users
create table telegram_messages (
    id serial primary key,
    telegram_message_id bigint not null unique,
    chat_id bigint not null,
    message_type telegram_message_type not null,
    content text not null, -- Message text or caption
    file_id varchar(255),
    file_path text,
    status telegram_message_status not null default 'sent',
    error_message text,
    user_id integer not null references users(id) on delete cascade,
    bill_id integer references bills(id) on delete set null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- Composite index for chat message history (ordered by creation time)
create index idx_telegram_messages_chat_id_created_at on telegram_messages(chat_id, created_at);

-- Index for user-based message queries
create index idx_telegram_messages_user_id on telegram_messages(user_id);

-- Index for bill-to-message relationship
create index idx_telegram_messages_bill_id on telegram_messages(bill_id);

