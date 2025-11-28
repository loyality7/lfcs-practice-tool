-- LFCS Practice Tool Database Schema

-- Table for storing user attempts
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_id TEXT NOT NULL,
    category TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    score INTEGER NOT NULL,
    max_score INTEGER NOT NULL,
    passed BOOLEAN NOT NULL,
    duration INTEGER,  -- seconds
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table for storing achievements
CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    unlocked_at DATETIME
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_attempts_category ON attempts(category);
CREATE INDEX IF NOT EXISTS idx_attempts_timestamp ON attempts(timestamp);
CREATE INDEX IF NOT EXISTS idx_attempts_difficulty ON attempts(difficulty);
CREATE INDEX IF NOT EXISTS idx_attempts_scenario_id ON attempts(scenario_id);

-- Table for learning progress
CREATE TABLE IF NOT EXISTS learning_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id TEXT NOT NULL,
    lesson_id TEXT NOT NULL,
    exercise_id TEXT,
    completed BOOLEAN DEFAULT 0,
    score INTEGER DEFAULT 0,
    completed_at DATETIME,
    UNIQUE(module_id, lesson_id, exercise_id)
);

-- Table for module unlocks
CREATE TABLE IF NOT EXISTS module_unlocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL UNIQUE,
    unlocked_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for learning tables
CREATE INDEX IF NOT EXISTS idx_learning_module ON learning_progress(module_id);
CREATE INDEX IF NOT EXISTS idx_learning_completed ON learning_progress(completed);
