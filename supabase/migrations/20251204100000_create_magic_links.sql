-- ============================================================================
-- Migration: Create magic_links table
-- ============================================================================
-- Purpose: Creates the magic_links table for passwordless authentication.
--          This table stores tokens used to authenticate users via email links.
--
-- Affected objects:
--   - Table: magic_links
--   - Indexes: idx_magic_links_token, idx_magic_links_user_id, idx_magic_links_expires_at
--
-- Special considerations:
--   - Table has Row Level Security (RLS) enabled.
--   - No RLS policies are added for 'anon' or 'authenticated' roles, meaning
--     access is restricted to the service role (backend) only by default.
--     This is intended as magic links are sensitive and verified by the API.
-- ============================================================================

-- Create the magic_links table
create table magic_links (
    id serial primary key,
    token varchar(255) not null,
    user_id integer not null references users(id) on delete cascade,
    expires_at timestamptz not null,
    used boolean not null default false,
    used_at timestamptz,
    redirect_url varchar(512),
    created_at timestamptz not null default now()
);

-- Comments for the table and columns
comment on table magic_links is 'Magic link tokens for passwordless authentication';
comment on column magic_links.token is 'Unique token for the magic link';
comment on column magic_links.user_id is 'Foreign key to the user associated with the link';
comment on column magic_links.expires_at is 'Timestamp when the token expires';
comment on column magic_links.used is 'Flag indicating if the token has been used';
comment on column magic_links.used_at is 'Timestamp when the token was used';
comment on column magic_links.redirect_url is 'URL to redirect the user to after successful authentication';

-- Create indexes
-- Unique index on token allows fast lookups and ensures uniqueness
create unique index idx_magic_links_token on magic_links(token);

-- Index on user_id for filtering links by user
create index idx_magic_links_user_id on magic_links(user_id);

-- Index on expires_at for cleaning up expired tokens
create index idx_magic_links_expires_at on magic_links(expires_at);

-- Enable Row Level Security
alter table magic_links enable row level security;

-- ============================================================================
-- RLS Policies
-- ============================================================================
-- Note: We are strictly restricting access to the service role (backend).
-- No policies for 'anon' or 'authenticated' are created, which implicitly denies access
-- to these roles via the Supabase Client.
-- This ensures that magic links can only be managed by the secure server-side logic.

