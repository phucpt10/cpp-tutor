-- Migration: Fix students table UUID generation
-- Date: 2026-06-23
-- Purpose: Ensure id column auto-generates UUID for new records

-- For existing Supabase setup, add default UUID generation to id column if not exists
-- Note: In PostgreSQL, use ALTER TABLE for this
ALTER TABLE students
ALTER COLUMN id SET DEFAULT gen_random_uuid();

-- If table already exists and has records without default, this ensures future inserts work
-- Supabase: This migration should be run in the SQL Editor if schema.sql was already applied
