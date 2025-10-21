-- migration: initial database schema for bills mvp
-- purpose: create all tables, indexes, constraints, and enums for the bills application
-- affected tables: users, shops, categories, indexes, index_aliases, bills, bill_items, telegram_messages
-- special considerations: includes custom enums, comprehensive indexing, and data validation constraints

-- enable required extensions for full-text search and trigram matching
create extension if not exists "pg_trgm";

-- create custom enum types
-- processing status for bills workflow
create type processing_status as enum ('pending', 'processing', 'completed', 'error');

-- verification source for bill items
create type verification_source as enum ('auto', 'user', 'admin');

-- telegram message status tracking
create type telegram_message_status as enum ('sent', 'delivered', 'read', 'failed');

-- telegram message types for different content
create type telegram_message_type as enum ('text', 'photo', 'document', 'audio', 'video', 'voice', 'sticker');

-- table: users
-- managed by supabase auth, stores external telegram user references
create table users (
    id serial primary key,
    external_id bigint not null unique,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    is_active boolean not null default true
);

-- unique index for fast telegram user lookup
create unique index idx_users_external_id on users(external_id);

-- table: shops
-- stores shop information with unique name+address constraint
create table shops (
    id serial primary key,
    name varchar(255) not null,
    address text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- unique index for shop name+address combination (handles null addresses)
create unique index idx_shops_unique_name_address on shops(lower(name), lower(coalesce(address, '')));

-- index for shop name searches
create index idx_shops_name on shops(lower(name));

-- table: categories
-- hierarchical category structure for product organization
create table categories (
    id serial primary key,
    name varchar(255) not null unique,
    parent_id integer references categories(id) on delete restrict,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- indexes for category navigation
create index idx_categories_name on categories(name);
create index idx_categories_parent_id on categories(parent_id);

-- table: indexes (product dictionary)
-- normalized product names with synonyms and category associations
create table indexes (
    id serial primary key,
    name varchar(255) not null unique,
    synonyms jsonb,
    category_id integer references categories(id) on delete restrict,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- indexes for product lookups
create index idx_indexes_name on indexes(name);
create index idx_indexes_category_id on indexes(category_id);
create index idx_indexes_synonyms on indexes using gin(synonyms);

-- table: index_aliases (ocr variants)
-- stores raw ocr text variants linked to normalized products
create table index_aliases (
    id serial primary key,
    raw_name text not null,
    index_id integer not null references indexes(id) on delete cascade,
    confirmations_count integer not null default 0,
    first_seen_at timestamptz,
    last_seen_at timestamptz,
    locale varchar(10),
    shop_id integer references shops(id) on delete set null,
    user_id integer references users(id) on delete set null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- unique index for raw_name + index_id combination (case-insensitive)
create unique index idx_index_aliases_unique_raw_name_index on index_aliases(lower(raw_name), index_id);

-- indexes for alias management and search
create index idx_index_aliases_index_id on index_aliases(index_id);
create index idx_index_aliases_shop_id on index_aliases(shop_id);
create index idx_index_aliases_user_id on index_aliases(user_id);
create index idx_index_aliases_raw_name on index_aliases using gin(lower(raw_name) gin_trgm_ops);

-- table: bills
-- main bills table with processing status and image management
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

-- indexes for bill queries and reporting
create index idx_bills_user_id_bill_date on bills(user_id, bill_date desc);
create index idx_bills_status on bills(status);
create index idx_bills_shop_id on bills(shop_id);
create index idx_bills_image_expires_at on bills(image_expires_at) where image_expires_at is not null;

-- table: bill_items
-- individual items from bills with verification tracking
create table bill_items (
    id serial primary key,
    quantity numeric(10,4) not null,
    unit_price numeric(12,2) not null,
    total_price numeric(12,2) not null,
    original_text text,
    confidence_score decimal(3,2),
    is_verified boolean not null default false,
    verification_source verification_source not null default 'auto',
    bill_id integer not null references bills(id) on delete cascade,
    index_id integer references indexes(id) on delete set null,
    created_at timestamptz not null default now(),
    constraint check_quantity_positive check (quantity > 0),
    constraint check_unit_price_non_negative check (unit_price >= 0),
    constraint check_total_price_calculation check (total_price = round(quantity * unit_price, 2))
);

-- indexes for bill item operations
create index idx_bill_items_bill_id on bill_items(bill_id);
create index idx_bill_items_index_id on bill_items(index_id);
create index idx_bill_items_unverified on bill_items(bill_id) where is_verified = false;

-- table: telegram_messages
-- telegram message tracking and content storage
create table telegram_messages (
    id serial primary key,
    telegram_message_id bigint not null unique,
    chat_id bigint not null,
    message_type telegram_message_type not null,
    content text not null,
    file_id varchar(255),
    file_path text,
    status telegram_message_status not null default 'sent',
    error_message text,
    user_id integer not null references users(id) on delete cascade,
    bill_id integer references bills(id) on delete set null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- indexes for telegram message queries
create unique index idx_telegram_messages_telegram_id on telegram_messages(telegram_message_id);
create index idx_telegram_messages_chat_id_created_at on telegram_messages(chat_id, created_at desc);
create index idx_telegram_messages_user_id on telegram_messages(user_id);
create index idx_telegram_messages_bill_id on telegram_messages(bill_id);

-- add comments for documentation
comment on table users is 'user accounts managed by supabase auth with telegram external references';
comment on table shops is 'shop information with unique name+address constraints';
comment on table categories is 'hierarchical category structure for product organization';
comment on table indexes is 'normalized product dictionary with synonyms and category associations';
comment on table index_aliases is 'ocr text variants linked to normalized products with confirmation tracking';
comment on table bills is 'main bills table with processing status and image lifecycle management';
comment on table bill_items is 'individual bill items with verification and confidence tracking';
comment on table telegram_messages is 'telegram message tracking and content storage for bill processing';

-- add column comments for key fields
comment on column users.external_id is 'telegram user id for external authentication';
comment on column bills.status is 'processing status: pending, processing, completed, error';
comment on column bills.image_expires_at is 'image expiration date for automatic cleanup (6 months retention)';
comment on column bill_items.confidence_score is 'ocr confidence score (0.00-1.00)';
comment on column bill_items.is_verified is 'manual verification status for quality control';
comment on column index_aliases.confirmations_count is 'number of times this alias was confirmed as correct';
