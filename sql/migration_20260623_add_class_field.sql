-- Migration: Add class information to students table
-- Date: 2026-06-23
-- Purpose: Track which class each student belongs to

alter table students
add column if not exists class text;

-- Create index for class queries
create index if not exists idx_students_class on students(class);

-- Update comments
comment on column students.class is 'Class/section identifier (e.g., "CS101", "Math-A1")';
