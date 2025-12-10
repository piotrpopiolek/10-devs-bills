-- ============================================================================
-- Migration: Add 'to_verify' status to processing_status enum
-- ============================================================================
-- Purpose: Adds the TO_VERIFY status value to the processing_status enum
--          to support bills that require manual verification
-- ============================================================================

-- Add 'to_verify' value to the processing_status enum
ALTER TYPE processing_status ADD VALUE IF NOT EXISTS 'to_verify';
