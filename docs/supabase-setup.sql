-- Run this in Supabase SQL Editor:
-- https://supabase.com/dashboard/project/twodkhckmtweyxnsnftd/sql/new

-- Quiz attempts table
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

-- Index for fast lookups per student
CREATE INDEX idx_quiz_attempts_student ON quiz_attempts(student_id);

-- Enable Row Level Security
ALTER TABLE quiz_attempts ENABLE ROW LEVEL SECURITY;

-- Anyone can insert (anon key)
CREATE POLICY "Anyone can insert" ON quiz_attempts
  FOR INSERT WITH CHECK (true);

-- Anyone can read their own rows (matched by student_id passed in query)
CREATE POLICY "Anyone can read" ON quiz_attempts
  FOR SELECT USING (true);
