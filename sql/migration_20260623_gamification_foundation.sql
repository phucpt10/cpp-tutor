-- Migration for gamification foundation

alter table if exists students
  add column if not exists level int not null default 1;

alter table if exists students
  add column if not exists streak_days int not null default 0;

alter table if exists students
  add column if not exists energy int not null default 100;

alter table if exists students
  add column if not exists last_login_date date;

alter table if exists students
  alter column student_code drop not null;

alter table if exists students
  alter column email drop not null;

alter table if exists students
  drop constraint if exists students_student_code_key;

alter table if exists students
  drop constraint if exists students_email_key;

drop index if exists idx_students_student_code;
drop index if exists idx_students_email;
create index if not exists idx_students_student_code on students(student_code);
create index if not exists idx_students_email on students(email);

create table if not exists achievements (
  id bigint generated always as identity primary key,
  name text not null unique,
  description text not null,
  badge_icon text not null
);

create table if not exists student_achievements (
  id bigint generated always as identity primary key,
  student_id uuid not null references students(id) on delete cascade,
  achievement_id bigint not null references achievements(id) on delete cascade,
  earned_at timestamptz not null default now(),
  unique (student_id, achievement_id)
);

create table if not exists daily_quests (
  id bigint generated always as identity primary key,
  student_id uuid not null references students(id) on delete cascade,
  title text not null,
  target int not null default 1,
  progress int not null default 0,
  reward_xp int not null default 30,
  completed boolean not null default false,
  quest_type text not null,
  quest_date date not null,
  unique (student_id, quest_type, quest_date)
);

create table if not exists boss_battles (
  id bigint generated always as identity primary key,
  topic_id bigint not null references topics(id) on delete cascade,
  title text not null,
  difficulty text not null,
  mcq_payload jsonb,
  coding_title text,
  coding_description text,
  coding_starter_code text,
  coding_expected_concepts text,
  provider_used text,
  created_at timestamptz not null default now()
);

create table if not exists boss_battle_attempts (
  id bigint generated always as identity primary key,
  student_id uuid not null references students(id) on delete cascade,
  topic_id bigint not null references topics(id) on delete cascade,
  boss_battle_id bigint not null references boss_battles(id) on delete cascade,
  mcq_score int not null default 0 check (mcq_score between 0 and 100),
  coding_score int not null default 0 check (coding_score between 0 and 100),
  overall_score int not null default 0 check (overall_score between 0 and 100),
  passed boolean not null default false,
  coding_feedback text not null default '',
  provider_used text,
  attempted_at timestamptz not null default now()
);

create table if not exists coding_exercises (
  id bigint generated always as identity primary key,
  topic_id bigint not null references topics(id) on delete cascade,
  title text not null,
  description text not null,
  starter_code text not null,
  expected_concepts text not null,
  difficulty text not null default 'Beginner',
  provider_used text,
  created_at timestamptz not null default now()
);

create table if not exists coding_submissions (
  id bigint generated always as identity primary key,
  student_id uuid not null references students(id) on delete cascade,
  topic_id bigint not null references topics(id) on delete cascade,
  exercise_id bigint not null references coding_exercises(id) on delete cascade,
  submitted_code text not null,
  score int not null default 0 check (score between 0 and 100),
  feedback text not null default '',
  passed boolean not null default false,
  provider_used text,
  submitted_at timestamptz not null default now()
);

create table if not exists leaderboard (
  id bigint generated always as identity primary key,
  student_id uuid not null unique references students(id) on delete cascade,
  xp int not null default 0,
  rank int not null default 0,
  updated_at timestamptz not null default now()
);

create table if not exists skill_tree_progress (
  id bigint generated always as identity primary key,
  student_id uuid not null unique references students(id) on delete cascade,
  syntax_score int not null default 0 check (syntax_score between 0 and 100),
  problem_solving_score int not null default 0 check (problem_solving_score between 0 and 100),
  debugging_score int not null default 0 check (debugging_score between 0 and 100),
  memory_management_score int not null default 0 check (memory_management_score between 0 and 100),
  oop_score int not null default 0 check (oop_score between 0 and 100)
);

insert into achievements (name, description, badge_icon)
values
  ('First Steps', 'Complete your first lesson and start the adventure.', '🥾'),
  ('Quiz Hero', 'Score 100% in 5 quizzes.', '🏆'),
  ('Pointer Master', 'Complete the Pointer Dungeon world.', '🗡️'),
  ('Coding Warrior', 'Complete 20 coding exercises.', '⚔️'),
  ('Boss Conqueror', 'Defeat your first boss battle.', '👑'),
  ('7-Day Streak', 'Log in for 7 consecutive days.', '🔥')
on conflict (name) do nothing;

-- Boss Battle Seeding: 14 bosses across curriculum
insert into boss_battles (topic_id, title, difficulty)
select id, 'Variable Goblin', 'Beginner'
from topics
where title = 'Data Types, Variables & Constants'
on conflict do nothing;

insert into boss_battles (topic_id, title, difficulty)
select id, 'Operator Oracle', 'Beginner'
from topics
where title = 'C/C++ Operators'
on conflict do nothing;

insert into boss_battles (topic_id, title, difficulty)
select id, 'If Elemental', 'Beginner'
from topics
where title = 'Decision Making (if-else, switch-case)'
on conflict do nothing;

insert into boss_battles (topic_id, title, difficulty)
select id, 'Loop Lich', 'Beginner'
from topics
where title = 'Repetition Statements (for, while, do-while)'
on conflict do nothing;

insert into boss_battles (topic_id, title, difficulty)
select id, 'Array Dragon', 'Intermediate'
from topics
where title = 'Arrays & Strings'
on conflict do nothing;

insert into boss_battles (topic_id, title, difficulty)
select id, 'Struct Sentinel', 'Intermediate'
from topics
where title = 'Structures (struct)'
on conflict do nothing;

insert into boss_battles (topic_id, title, difficulty)
select id, 'Function Fiend', 'Intermediate'
from topics
where title = 'Introducing Functions'
on conflict do nothing;

insert into boss_battles (topic_id, title, difficulty)
select id, 'Reference Revenant', 'Advanced'
from topics
where title = 'Pass by Reference'
on conflict do nothing;

insert into boss_battles (topic_id, title, difficulty)
select id, 'Memory Phantom', 'Advanced'
from topics
where title = 'Pointers & Pointers - Arrays'
on conflict do nothing;

insert into boss_battles (topic_id, title, difficulty)
select id, 'Class Constructor', 'Advanced'
from topics
where title = 'Introducing Objects & Classes'
on conflict do nothing;

insert into boss_battles (topic_id, title, difficulty)
select id, 'Inheritance Imp', 'Advanced'
from topics
where title = 'Inheritance'
on conflict do nothing;

insert into boss_battles (topic_id, title, difficulty)
select id, 'Polymorphic Phoenix', 'Hard'
from topics
where title = 'Polymorphism'
on conflict do nothing;

insert into boss_battles (topic_id, title, difficulty)
select id, 'Exception Eater', 'Hard'
from topics
where title = 'Exceptions'
on conflict do nothing;

insert into boss_battles (topic_id, title, difficulty)
select id, 'STL Savant', 'Hard'
from topics
where title = 'Data Structures and STL'
on conflict do nothing;

update students
set level = case
  when xp >= 1000 then 5
  when xp >= 600 then 4
  when xp >= 300 then 3
  when xp >= 100 then 2
  else 1
end;

insert into leaderboard (student_id, xp, rank)
select id, xp, 0
from students
on conflict (student_id) do update set xp = excluded.xp;

insert into skill_tree_progress (student_id)
select id
from students
on conflict (student_id) do nothing;