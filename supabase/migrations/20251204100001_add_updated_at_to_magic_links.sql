-- ============================================================================
-- Migration: Add updated_at column to magic_links table
-- ============================================================================
-- Purpose: Adds the updated_at timestamp column to the magic_links table.
--          This column automatically tracks when a record is modified.
--
-- Affected objects:
--   - Table: magic_links
--   - Column: updated_at
--
-- Special considerations:
--   - Column is not nullable and has a default value of now()
--   - SQLAlchemy ORM handles automatic updates via onupdate=func.now()
--   - This is a non-destructive operation (adds column with default value)
-- ============================================================================

-- Add updated_at column to magic_links table
-- Column is not nullable with default value of current timestamp
-- SQLAlchemy ORM will automatically update this value on row modification
alter table magic_links
add column updated_at timestamptz not null default now();

-- Add comment explaining the column's purpose
comment on column magic_links.updated_at is 
    'Timestamp when the record was last updated (automatically managed by SQLAlchemy ORM)';
