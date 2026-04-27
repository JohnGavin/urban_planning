# Supabase Cloud Database — Setup & Access Guide

This guide explains how quiz progress is stored in the cloud so it works
across devices, and how to manage it.

## How It Works

When you take a quiz, your results are saved in two places:
1. **Locally** in your browser (IndexedDB) — works offline, instant
2. **Cloud** in Supabase (PostgreSQL database) — works across devices

Each student gets a random ID (like `stu_5d842f85-05c`) stored in their
browser's localStorage. This ID links their quiz results together.

## Current Supabase Project

| Detail | Value |
|--------|-------|
| Project name | raumplanung-progress |
| Project ID | `twodkhckmtweyxnsnftd` |
| Project URL | `https://twodkhckmtweyxnsnftd.supabase.co` |
| Region | (check dashboard) |
| Plan | Free tier (500MB database, 50K monthly active users) |
| Dashboard | https://supabase.com/dashboard/project/twodkhckmtweyxnsnftd |

## Login Details

| Detail | Value |
|--------|-------|
| Supabase login | https://supabase.com/dashboard |
| Account email | john.b.gavin@gmail.com |
| Password | (your Supabase account password — not stored here) |
| anon (public) key | `sb_publishable_MBLHzg2bxnYR2eccFL0D0w_QA89q6Lx` |

The **anon key** is embedded in the website JavaScript. It is public by design —
Supabase's Row Level Security (RLS) policies control what it can do (insert and
read quiz_attempts only).

## Database Structure

One table: `quiz_attempts`

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Auto-generated unique ID |
| student_id | TEXT | Random ID per student (from localStorage) |
| quiz_id | TEXT | Which quiz (e.g. "oerek-principles") |
| score | REAL | Raw score (sum of partial credits) |
| total | INTEGER | Number of questions |
| percentage | INTEGER | Score as percentage (0-100) |
| duration_sec | INTEGER | Time taken in seconds |
| created_at | TIMESTAMPTZ | When the quiz was submitted |

## How to View Data

1. Go to https://supabase.com/dashboard/project/twodkhckmtweyxnsnftd/editor
2. Click on `quiz_attempts` table
3. You can filter by student_id, quiz_id, or date
4. You can see all students' progress here

## How to Reset / Delete Data

### Delete one student's data
In the SQL editor (https://supabase.com/dashboard/project/twodkhckmtweyxnsnftd/sql/new):
```sql
DELETE FROM quiz_attempts WHERE student_id = 'stu_XXXX';
```

### Delete all data
```sql
TRUNCATE quiz_attempts;
```

### Delete the table entirely (to start over)
```sql
DROP TABLE IF EXISTS quiz_attempts;
```
Then re-run the setup SQL from `docs/supabase-setup.sql`.

## For Another Student Using Claude Cowork

If you are setting up your OWN Supabase project (not sharing the existing one):

### Step 1: Create a Supabase account
1. Go to https://supabase.com and sign up (free)
2. Click "New Project"
3. Name it anything (e.g. "my-raumplanung")
4. Choose a database password (save it somewhere safe)
5. Select region eu-central-1 (or closest to you)
6. Click "Create new project" and wait ~2 minutes

### Step 2: Get your credentials
1. Go to Settings → API (left sidebar)
2. Copy the **Project URL** (looks like `https://XXXXX.supabase.co`)
3. Copy the **anon public** key (starts with `eyJ...` or `sb_publishable_...`)

### Step 3: Create the database table
1. Go to SQL Editor (left sidebar)
2. Click "New query"
3. Paste this SQL and click "Run":

```sql
CREATE TABLE quiz_attempts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  student_id TEXT NOT NULL,
  quiz_id TEXT NOT NULL,
  score REAL NOT NULL,
  total INTEGER NOT NULL,
  percentage INTEGER NOT NULL,
  duration_sec INTEGER,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_quiz_attempts_student ON quiz_attempts(student_id);

ALTER TABLE quiz_attempts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can insert" ON quiz_attempts
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Anyone can read" ON quiz_attempts
  FOR SELECT USING (true);
```

### Step 4: Update the website code
Ask Claude Cowork to:
> "In site/js/supabase-sync.js, replace the SUPABASE_URL and SUPABASE_KEY
> values with my new project URL and anon key."

The two lines to change (near the top of the file):
```javascript
const SUPABASE_URL = 'https://YOUR-PROJECT-ID.supabase.co';
const SUPABASE_KEY = 'YOUR-ANON-KEY-HERE';
```

### Step 5: Test it
1. Open the website in your browser
2. Take a quiz
3. The status should say "Gespeichert (lokal + cloud)."
4. Check your Supabase dashboard → Table Editor → quiz_attempts

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Lokal gespeichert (cloud offline)" | Check internet connection. Check if Supabase project is running (dashboard). |
| No data in Supabase table | Check browser console (F12) for errors. Verify URL and key in supabase-sync.js. |
| "relation quiz_attempts does not exist" | Run the setup SQL again (Step 3 above). |
| Want to use a different Supabase project | Change URL and key in supabase-sync.js (Step 4 above). |
| Data from old browser not showing | Each browser gets a unique student_id. The old data is still in Supabase under the old ID. |

## Security Notes

- The **anon key** is public — it's designed to be in client-side code
- Row Level Security (RLS) is enabled — the key can only INSERT and SELECT
- It cannot DELETE, UPDATE, or access other tables
- The **service_role key** (in Settings → API) is SECRET — never share or embed it
- Student IDs are random — no personal data is stored
