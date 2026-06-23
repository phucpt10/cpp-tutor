# AI C/C++ Tutor Adventure (Phase 1 MVP)

Production-quality Streamlit application for C/C++ learning with:

- Mandatory student identity authentication (student code, email, full name)
- Theory generation
- Quiz generation and evaluation
- Coding practice generation and evaluation
- Boss Battle generation and evaluation
- Progress tracking with topic unlock rules
- XP and level gamification
- Gamification foundation: streak, energy, quests, achievements, leaderboard, skill tree, world map
- Topic score tracking and cumulative total score tracking
- Supabase authentication and PostgreSQL persistence
- LLM router with fallback chain: Gemini -> OpenRouter -> Groq

## 1. Clean Architecture Overview

The project uses separated layers:

- Presentation layer: Streamlit pages (`cpp_tutor/pages`)
- Application layer: use-case services (`cpp_tutor/services`)
- Domain layer: entities/models (`cpp_tutor/models`)
- Infrastructure layer: Supabase adapters + external LLM providers (`cpp_tutor/database`, provider services)

SOLID highlights:

- Single Responsibility: each service has one concern (auth, progress, theory, quiz)
- Open/Closed: add new LLM providers without changing page logic
- Liskov Substitution: providers implement same `LLMProvider` contract
- Interface Segregation: UI depends on high-level service behavior
- Dependency Inversion: core flows depend on abstractions (`LLMProvider`), not concrete SDKs

## 2. Folder Structure

```
cpp_tutor/
├── app.py
├── config.py
├── pages/
│   ├── dashboard.py
│   ├── boss_battle.py
│   ├── practice.py
│   ├── theory.py
│   ├── quiz.py
│   └── profile.py
├── services/
│   ├── llm_provider.py
│   ├── llm_router.py
│   ├── gemini_provider.py
│   ├── openrouter_provider.py
│   ├── groq_provider.py
│   ├── auth_service.py
│   ├── boss_battle_service.py
│   ├── practice_service.py
│   ├── progress_service.py
│   ├── theory_service.py
│   └── quiz_service.py
├── database/
│   └── supabase_client.py
├── models/
│   ├── boss_battle.py
│   ├── student.py
│   ├── practice.py
│   ├── topic.py
│   ├── progress.py
│   └── quiz.py
├── utils/
│   ├── auth_guard.py
│   └── xp_calculator.py
└── prompts/
    ├── boss_battle_evaluation_prompt.txt
    ├── boss_battle_prompt.txt
    ├── practice_evaluation_prompt.txt
    ├── practice_prompt.txt
    ├── theory_prompt.txt
    └── quiz_prompt.txt

sql/
└── schema.sql

.env
requirements.txt
README.md
```

## 3. Setup

### 3.1 Install dependencies

```bash
pip install -r requirements.txt
```

### 3.2 Configure environment variables

Update `.env`:

```env
APP_ENV=development
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY

GEMINI_API_KEY=YOUR_GEMINI_KEY
OPENROUTER_API_KEY=YOUR_OPENROUTER_KEY
GROQ_API_KEY=YOUR_GROQ_KEY

GEMINI_MODEL=gemini-1.5-flash
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free
GROQ_MODEL=llama-3.1-8b-instant
REQUEST_TIMEOUT_SECONDS=10
```

### 3.3 Create database schema

Run SQL in Supabase SQL Editor:

- `sql/schema.sql`

If you already have an existing database, run the migration instead of recreating the schema:

- `sql/migration_20260623_gamification_foundation.sql`

### 3.4 Run app

```bash
streamlit run cpp_tutor/app.py
```

## 4. Functional Mapping

- FR-01 Authentication: `app.py` + `services/auth_service.py`
- FR-02 Dashboard: `pages/dashboard.py`
- FR-03 Course/Unlock Rule: `services/progress_service.py`
- FR-04 Theory Module: `pages/theory.py` + `services/theory_service.py`
- FR-05 Quiz Generator: `pages/quiz.py` + `services/quiz_service.py`
- FR-06 Quiz Evaluation: `services/quiz_service.py`
- Practice MVP: `pages/practice.py` + `services/practice_service.py`
- Boss Battle MVP: `pages/boss_battle.py` + `services/boss_battle_service.py`
- FR-07 XP System: `services/progress_service.py` + `utils/xp_calculator.py`
- FR-08 Progress Tracking: `progress` table + dashboard visualization

## 5. Authentication Policy (Audit Standard)

Before students can access learning features, they must provide all required fields:

- Student Code
- Email
- Full Name
- Password

Login succeeds only when these identity fields match the registered student profile in Supabase.

## 6. Score Persistence

- Per-topic score is stored in `progress.score`
- Total score is stored in `students.total_score`
- `students.total_score` is synchronized after each quiz submission

## 7. Gamification Foundation

The current foundation phase includes:

- 5-level progression with titles: Novice, Explorer, Apprentice, Developer, Master
- Daily login reward (`+5 XP`)
- 7-day streak bonus (`+100 XP`)
- Daily energy reset to `100`
- Daily quests for login, reading one lesson, and passing one quiz
- Achievement foundation with seeded badges
- Global leaderboard by XP
- Skill tree progress for Syntax, Problem Solving, Debugging, Memory Management, and OOP
- Static adventure world map for UI progression
- Practice stage after quiz pass with `+100 XP` reward per topic
- Boss Battle stage after practice pass with `+200 XP` reward per topic

Current foundation schema additions:

- `students.level`
- `students.streak_days`
- `students.energy`
- `students.last_login_date`
- `achievements`
- `student_achievements`
- `daily_quests`
- `boss_battles`
- `leaderboard`
- `skill_tree_progress`
- `coding_exercises`
- `coding_submissions`
- `boss_battle_attempts`

## 8. Practice MVP Flow

The minimal learning flow is now:

- Theory
- Quiz
- Practice
- Reward
- Unlock Next Topic

Practice rules:

- Practice opens only when the selected topic quiz score is `>= 80`
- The student submits C/C++ code in the Practice page
- AI evaluates the submission and returns structured feedback
- Passing practice awards `+100 XP` once per topic
- Submission data is stored in `coding_submissions`
- Generated exercises are stored in `coding_exercises`

## 9. Boss Battle MVP Flow

The minimal adventure extension now continues after Practice:

- Practice pass unlocks Boss Battle for supported topics
- Boss Battle contains 10 MCQ and 1 coding challenge
- MCQ is scored locally, coding is evaluated by AI
- Overall boss score is the average of MCQ score and coding score
- Passing boss battle awards `+200 XP` once per topic
- Winning a first boss battle grants the `Boss Conqueror` badge
- Boss attempt data is stored in `boss_battle_attempts`

## 10. Boss Battle Seeding & Curriculum Coverage

Boss Battle expansion now covers 14 core topics across the C/C++ curriculum:

**Beginner Bosses (Difficulty: Beginner)**
- 🧌 **Variable Goblin** - Data Types, Variables & Constants
- 🔮 **Operator Oracle** - C/C++ Operators  
- ⚡ **If Elemental** - Decision Making (if-else, switch-case)
- 🔁 **Loop Lich** - Repetition Statements (for, while, do-while)

**Intermediate Bosses (Difficulty: Intermediate)**
- 🐉 **Array Dragon** - Arrays & Strings
- 🛡️ **Struct Sentinel** - Structures (struct)
- 👿 **Function Fiend** - Introducing Functions

**Advanced Bosses (Difficulty: Advanced)**
- 👻 **Reference Revenant** - Pass by Reference
- 💀 **Memory Phantom** - Pointers & Pointers - Arrays
- 👨‍💼 **Class Constructor** - Introducing Objects & Classes
- 👹 **Inheritance Imp** - Inheritance

**Hard Bosses (Difficulty: Hard)**
- 🔥 **Polymorphic Phoenix** - Polymorphism
- 👹 **Exception Eater** - Exceptions
- 🧙 **STL Savant** - Data Structures and STL

Dynamic boss generation: Each boss battle contains:
- 10 auto-generated MCQ questions (verified JSON format)
- 1 coding challenge with starter code and concepts
- MCQ scoring: exact answer match (0-100%)
- Coding scoring: AI evaluation (0-100%)
- Overall score: average of MCQ + coding scores
- Pass threshold: overall score >= 80%
- Reward: +200 XP per topic + "Boss Conqueror" badge on first win

## 11. Admin Dashboard

New `pages/admin.py` provides classroom analytics and progress tracking:

**Admin Access Control:**
- Enable via `ADMIN_MODE=true` environment variable
- Conditional admin link in main navigation (shown only to authorized users)
- Protected endpoint with access verification

**Dashboard Features:**

1. **Class Overview** - 4-metric summary:
   - Total Students
   - Average XP
   - Average Level
   - Average Total Score
   - Most completed topic
   - Bottleneck topic (most struggles)

2. **Student Progress Details** - Interactive table showing:
   - Student Code, Full Name, Email
   - XP, Level, Streak Days, Total Score
   - Quiz Completed (count)
   - Practice Passed (count)
   - Boss Defeated (count)
   - Achievements Earned (count)
   - Sorted by XP descending (leaderboard order)

3. **Topic Completion & Performance** - Per-topic statistics:
   - Topic Title
   - Completed / In Progress / Locked counts
   - Completion Rate (% of class)
   - Average Score for completed students
   - Sorted by completion rate descending

4. **Leaderboard Top 10** - Highest XP earners:
   - Rank, Student Code, Full Name, Email, Total XP

5. **Quick Export** - Download CSV reports:
   - Student Progress CSV (all metrics per student)
   - Topic Stats CSV (completion and performance data)

**Service Layer (`services/admin_service.py`)**:
- `get_all_students_progress()` → List[StudentProgressStat]
- `get_topic_completion_stats()` → List[TopicCompletionStat]
- `get_class_overview()` → ClassOverviewStat
- `get_leaderboard_top_n(n)` → List[Dict] with rank/student info/XP

All queries optimized with indexed joins on `(student_id, topic_id)`.

## 12. LLM Fallback Strategy

Order is fixed in `services/llm_router.py`:

1. Gemini (primary)
2. OpenRouter (fallback 1)
3. Groq (fallback 2)

If provider `n` fails due to timeout/rate limit/key issue, router automatically tries provider `n+1`.

## 13. Deployment (Streamlit Community Cloud)

1. Push this repository to GitHub
2. Create Streamlit app and set main file: `cpp_tutor/app.py`
3. Add all environment variables in Streamlit Secrets
4. Ensure Supabase project allows your deployment origin
5. For admin access: Set `ADMIN_MODE=true` in secrets for instructor account

## 14. Notes

- Keep API keys in `.env` or deployment secrets, never hardcode.
- Free-tier models can be rate-limited; fallback router helps maintain uptime.
- Boss Battle MVP now covers 14 seeded bosses across curriculum with difficulty progression.
- Admin Dashboard requires `ADMIN_MODE=true` to enable (instructor/admin only).
- Weekly challenge, adaptive difficulty, and mentor persona are not fully implemented yet.
