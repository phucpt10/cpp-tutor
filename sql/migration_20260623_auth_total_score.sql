-- Migration for mandatory student identity fields and total score tracking

alter table if exists students
  add column if not exists student_code text;

alter table if exists students
  add column if not exists total_score int not null default 0;

-- Backfill student_code for existing rows (temporary deterministic value).
update students
set student_code = coalesce(student_code, 'TEMP-' || replace(id::text, '-', ''))
where student_code is null;

alter table if exists students
  alter column student_code set not null;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'students_student_code_key'
  ) then
    alter table students
      add constraint students_student_code_key unique (student_code);
  end if;
end $$;

-- Keep total_score synchronized for old data.
with score_by_student as (
  select student_id, coalesce(sum(score), 0) as total_score
  from progress
  group by student_id
)
update students s
set total_score = ss.total_score
from score_by_student ss
where s.id = ss.student_id;
