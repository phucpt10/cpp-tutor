-- RLS policies for identity mode (no Supabase password login)
-- Use only for trusted classroom/demo environment.

alter table if exists students enable row level security;
alter table if exists progress enable row level security;
alter table if exists xp_logs enable row level security;
alter table if exists daily_quests enable row level security;
alter table if exists leaderboard enable row level security;
alter table if exists skill_tree_progress enable row level security;
alter table if exists student_achievements enable row level security;
alter table if exists coding_exercises enable row level security;
alter table if exists coding_submissions enable row level security;
alter table if exists boss_battles enable row level security;
alter table if exists boss_battle_attempts enable row level security;

-- Students profile
drop policy if exists students_select_anon on students;
drop policy if exists students_insert_anon on students;
drop policy if exists students_update_anon on students;
create policy students_select_anon on students for select to anon using (true);
create policy students_insert_anon on students for insert to anon with check (true);
create policy students_update_anon on students for update to anon using (true) with check (true);

-- Learning progress and XP
drop policy if exists progress_select_anon on progress;
drop policy if exists progress_insert_anon on progress;
drop policy if exists progress_update_anon on progress;
create policy progress_select_anon on progress for select to anon using (true);
create policy progress_insert_anon on progress for insert to anon with check (true);
create policy progress_update_anon on progress for update to anon using (true) with check (true);

drop policy if exists xp_logs_select_anon on xp_logs;
drop policy if exists xp_logs_insert_anon on xp_logs;
create policy xp_logs_select_anon on xp_logs for select to anon using (true);
create policy xp_logs_insert_anon on xp_logs for insert to anon with check (true);

-- Gamification tables
drop policy if exists daily_quests_select_anon on daily_quests;
drop policy if exists daily_quests_insert_anon on daily_quests;
drop policy if exists daily_quests_update_anon on daily_quests;
create policy daily_quests_select_anon on daily_quests for select to anon using (true);
create policy daily_quests_insert_anon on daily_quests for insert to anon with check (true);
create policy daily_quests_update_anon on daily_quests for update to anon using (true) with check (true);

drop policy if exists leaderboard_select_anon on leaderboard;
drop policy if exists leaderboard_insert_anon on leaderboard;
drop policy if exists leaderboard_update_anon on leaderboard;
create policy leaderboard_select_anon on leaderboard for select to anon using (true);
create policy leaderboard_insert_anon on leaderboard for insert to anon with check (true);
create policy leaderboard_update_anon on leaderboard for update to anon using (true) with check (true);

drop policy if exists skill_tree_progress_select_anon on skill_tree_progress;
drop policy if exists skill_tree_progress_insert_anon on skill_tree_progress;
drop policy if exists skill_tree_progress_update_anon on skill_tree_progress;
create policy skill_tree_progress_select_anon on skill_tree_progress for select to anon using (true);
create policy skill_tree_progress_insert_anon on skill_tree_progress for insert to anon with check (true);
create policy skill_tree_progress_update_anon on skill_tree_progress for update to anon using (true) with check (true);

drop policy if exists student_achievements_select_anon on student_achievements;
drop policy if exists student_achievements_insert_anon on student_achievements;
create policy student_achievements_select_anon on student_achievements for select to anon using (true);
create policy student_achievements_insert_anon on student_achievements for insert to anon with check (true);

-- Practice/Boss tables
drop policy if exists coding_exercises_select_anon on coding_exercises;
drop policy if exists coding_exercises_insert_anon on coding_exercises;
drop policy if exists coding_exercises_update_anon on coding_exercises;
create policy coding_exercises_select_anon on coding_exercises for select to anon using (true);
create policy coding_exercises_insert_anon on coding_exercises for insert to anon with check (true);
create policy coding_exercises_update_anon on coding_exercises for update to anon using (true) with check (true);

drop policy if exists coding_submissions_select_anon on coding_submissions;
drop policy if exists coding_submissions_insert_anon on coding_submissions;
create policy coding_submissions_select_anon on coding_submissions for select to anon using (true);
create policy coding_submissions_insert_anon on coding_submissions for insert to anon with check (true);

drop policy if exists boss_battles_select_anon on boss_battles;
drop policy if exists boss_battles_insert_anon on boss_battles;
drop policy if exists boss_battles_update_anon on boss_battles;
create policy boss_battles_select_anon on boss_battles for select to anon using (true);
create policy boss_battles_insert_anon on boss_battles for insert to anon with check (true);
create policy boss_battles_update_anon on boss_battles for update to anon using (true) with check (true);

drop policy if exists boss_battle_attempts_select_anon on boss_battle_attempts;
drop policy if exists boss_battle_attempts_insert_anon on boss_battle_attempts;
create policy boss_battle_attempts_select_anon on boss_battle_attempts for select to anon using (true);
create policy boss_battle_attempts_insert_anon on boss_battle_attempts for insert to anon with check (true);
