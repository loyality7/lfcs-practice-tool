"""
Database Manager and Scorer for Progress Tracking
Uses SQLite for local storage
"""

import sqlite3
import os
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging

from .error_handler import ErrorHandler, ErrorContext, handle_database_error


logger = logging.getLogger(__name__)


@dataclass
class Attempt:
    """Represents a single attempt at a scenario"""
    id: Optional[int]
    scenario_id: str
    category: str
    difficulty: str
    score: int
    max_score: int
    passed: bool
    duration: Optional[int]  # seconds
    timestamp: datetime


@dataclass
class Achievement:
    """Represents an achievement"""
    id: Optional[int]
    name: str
    description: str
    unlocked_at: Optional[datetime]


@dataclass
class Statistics:
    """User statistics"""
    total_attempts: int
    total_passed: int
    total_score: int
    average_score: float
    by_category: Dict[str, 'CategoryStats']
    current_streak: int
    best_streak: int
    achievements: List[Achievement]


@dataclass
class CategoryStats:
    """Statistics for a specific category"""
    category: str
    attempts: int
    passed: int
    total_score: int
    average_score: float
    by_difficulty: Dict[str, 'DifficultyStats']


@dataclass
class DifficultyStats:
    """Statistics for a specific difficulty level"""
    difficulty: str
    attempts: int
    passed: int
    total_score: int
    average_score: float


class Scorer:
    """
    Manages scoring, progress tracking, and statistics
    """
    
    def __init__(self, db_path: str = "database/progress.db"):
        self.db_path = db_path
        self.error_handler = ErrorHandler()
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Ensure database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
    
    def _init_database(self):
        """Initialize database schema with error handling"""
        # Read schema from file if it exists
        schema_path = "database/schema.sql"
        
        max_retries = 3
        retry_delay = 0.5  # seconds
        
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(self.db_path, timeout=10.0)
                cursor = conn.cursor()
                
                if os.path.exists(schema_path):
                    with open(schema_path, 'r') as f:
                        schema_sql = f.read()
                        cursor.executescript(schema_sql)
                else:
                    # Fallback to inline schema
                    cursor.executescript("""
                        CREATE TABLE IF NOT EXISTS attempts (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            scenario_id TEXT NOT NULL,
                            category TEXT NOT NULL,
                            difficulty TEXT NOT NULL,
                            score INTEGER NOT NULL,
                            max_score INTEGER NOT NULL,
                            passed BOOLEAN NOT NULL,
                            duration INTEGER,
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                        );
                        
                        CREATE TABLE IF NOT EXISTS achievements (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            description TEXT,
                            unlocked_at DATETIME
                        );
                        
                        CREATE INDEX IF NOT EXISTS idx_attempts_category ON attempts(category);
                        CREATE INDEX IF NOT EXISTS idx_attempts_timestamp ON attempts(timestamp);
                        CREATE INDEX IF NOT EXISTS idx_attempts_difficulty ON attempts(difficulty);
                        CREATE INDEX IF NOT EXISTS idx_attempts_scenario_id ON attempts(scenario_id);
                    """)
                
                conn.commit()
                conn.close()
                return  # Success
                
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower() and attempt < max_retries - 1:
                    logger.warning(f"Database locked, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    context = ErrorContext(user_action="initialize_database")
                    response = self.error_handler.handle_error(e, context)
                    print(self.error_handler.format_error_for_user(response))
                    raise
            except Exception as e:
                context = ErrorContext(user_action="initialize_database")
                response = self.error_handler.handle_error(e, context)
                print(self.error_handler.format_error_for_user(response))
                raise
    
    def calculate_score(self, max_score: int, checks_passed: int, 
                       checks_total: int, difficulty: str,
                       difficulty_multipliers: Dict[str, float]) -> int:
        """
        Calculate score based on validation results and difficulty
        
        Args:
            max_score: Maximum possible score for the scenario
            checks_passed: Number of validation checks passed
            checks_total: Total number of validation checks
            difficulty: Difficulty level (easy, medium, hard)
            difficulty_multipliers: Multipliers for each difficulty level
        
        Returns:
            Calculated score
        """
        if checks_total == 0:
            return 0
        
        # Calculate base score as percentage of checks passed
        base_score = (checks_passed / checks_total) * max_score
        
        # Apply difficulty multiplier
        multiplier = difficulty_multipliers.get(difficulty, 1.0)
        final_score = int(base_score * multiplier)
        
        return final_score
    
    def record_attempt(self, scenario_id: str, category: str, difficulty: str,
                      score: int, max_score: int, passed: bool,
                      duration: Optional[int] = None) -> int:
        """
        Record an attempt in the database with retry logic
        
        Args:
            scenario_id: ID of the scenario
            category: Category of the scenario
            difficulty: Difficulty level
            score: Score achieved
            max_score: Maximum possible score
            passed: Whether the attempt passed
            duration: Duration in seconds
        
        Returns:
            ID of the recorded attempt
        """
        max_retries = 3
        retry_delay = 0.5
        
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(self.db_path, timeout=10.0)
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO attempts (scenario_id, category, difficulty, score, 
                                        max_score, passed, duration, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (scenario_id, category, difficulty, score, max_score, 
                      passed, duration, datetime.now()))
                
                attempt_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                return attempt_id
                
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower() and attempt < max_retries - 1:
                    logger.warning(f"Database locked, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    context = ErrorContext(
                        scenario_id=scenario_id,
                        category=category,
                        difficulty=difficulty,
                        user_action="record_attempt"
                    )
                    response = self.error_handler.handle_error(e, context)
                    logger.error(f"Failed to record attempt: {response.message}")
                    raise
            except Exception as e:
                context = ErrorContext(
                    scenario_id=scenario_id,
                    category=category,
                    difficulty=difficulty,
                    user_action="record_attempt"
                )
                response = self.error_handler.handle_error(e, context)
                logger.error(f"Failed to record attempt: {response.message}")
                raise
    
    def get_statistics(self, category: Optional[str] = None) -> Statistics:
        """
        Get user statistics, optionally filtered by category
        
        Args:
            category: Optional category to filter by
        
        Returns:
            Statistics object with all relevant data
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build query based on category filter
        if category:
            query = "SELECT * FROM attempts WHERE category = ? ORDER BY timestamp"
            cursor.execute(query, (category,))
        else:
            query = "SELECT * FROM attempts ORDER BY timestamp"
            cursor.execute(query)
        
        attempts = cursor.fetchall()
        
        # Calculate overall statistics
        total_attempts = len(attempts)
        total_passed = sum(1 for a in attempts if a['passed'])
        total_score = sum(a['score'] for a in attempts)
        average_score = total_score / total_attempts if total_attempts > 0 else 0.0
        
        # Calculate statistics by category
        by_category = self._calculate_category_stats(attempts)
        
        # Calculate streaks
        current_streak, best_streak = self._calculate_streaks(attempts)
        
        # Get achievements
        cursor.execute("SELECT * FROM achievements WHERE unlocked_at IS NOT NULL")
        achievement_rows = cursor.fetchall()
        achievements = [
            Achievement(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                unlocked_at=datetime.fromisoformat(row['unlocked_at']) if row['unlocked_at'] else None
            )
            for row in achievement_rows
        ]
        
        conn.close()
        
        return Statistics(
            total_attempts=total_attempts,
            total_passed=total_passed,
            total_score=total_score,
            average_score=average_score,
            by_category=by_category,
            current_streak=current_streak,
            best_streak=best_streak,
            achievements=achievements
        )
    
    def _calculate_category_stats(self, attempts: List[sqlite3.Row]) -> Dict[str, CategoryStats]:
        """Calculate statistics grouped by category"""
        category_data = {}
        
        for attempt in attempts:
            cat = attempt['category']
            if cat not in category_data:
                category_data[cat] = []
            category_data[cat].append(attempt)
        
        result = {}
        for category, cat_attempts in category_data.items():
            total_attempts = len(cat_attempts)
            passed = sum(1 for a in cat_attempts if a['passed'])
            total_score = sum(a['score'] for a in cat_attempts)
            avg_score = total_score / total_attempts if total_attempts > 0 else 0.0
            
            # Calculate by difficulty
            by_difficulty = self._calculate_difficulty_stats(cat_attempts)
            
            result[category] = CategoryStats(
                category=category,
                attempts=total_attempts,
                passed=passed,
                total_score=total_score,
                average_score=avg_score,
                by_difficulty=by_difficulty
            )
        
        return result
    
    def _calculate_difficulty_stats(self, attempts: List[sqlite3.Row]) -> Dict[str, DifficultyStats]:
        """Calculate statistics grouped by difficulty"""
        difficulty_data = {}
        
        for attempt in attempts:
            diff = attempt['difficulty']
            if diff not in difficulty_data:
                difficulty_data[diff] = []
            difficulty_data[diff].append(attempt)
        
        result = {}
        for difficulty, diff_attempts in difficulty_data.items():
            total_attempts = len(diff_attempts)
            passed = sum(1 for a in diff_attempts if a['passed'])
            total_score = sum(a['score'] for a in diff_attempts)
            avg_score = total_score / total_attempts if total_attempts > 0 else 0.0
            
            result[difficulty] = DifficultyStats(
                difficulty=difficulty,
                attempts=total_attempts,
                passed=passed,
                total_score=total_score,
                average_score=avg_score
            )
        
        return result
    
    def _calculate_streaks(self, attempts: List[sqlite3.Row]) -> Tuple[int, int]:
        """Calculate current and best streaks"""
        if not attempts:
            return 0, 0
        
        current_streak = 0
        best_streak = 0
        temp_streak = 0
        
        # Calculate streaks from most recent to oldest
        for attempt in reversed(attempts):
            if attempt['passed']:
                temp_streak += 1
                best_streak = max(best_streak, temp_streak)
            else:
                temp_streak = 0
        
        # Current streak is the streak at the end (most recent)
        for attempt in reversed(attempts):
            if attempt['passed']:
                current_streak += 1
            else:
                break
        
        return current_streak, best_streak
    
    def get_recommendations(self, statistics: Statistics) -> List[str]:
        """
        Get personalized recommendations based on performance
        
        Args:
            statistics: User statistics
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        if statistics.total_attempts == 0:
            recommendations.append("Start with easy scenarios to build confidence")
            return recommendations
        
        # Check overall pass rate
        pass_rate = statistics.total_passed / statistics.total_attempts
        
        if pass_rate < 0.5:
            recommendations.append("Focus on easier scenarios to build fundamentals")
        elif pass_rate > 0.8:
            recommendations.append("Great job! Try harder scenarios to challenge yourself")
        
        # Check category performance and difficulty progression
        for category, cat_stats in statistics.by_category.items():
            # Calculate mastery for each difficulty level
            for difficulty, diff_stats in cat_stats.by_difficulty.items():
                mastery = self._calculate_mastery_percentage(diff_stats)
                
                # Recommend progression based on mastery
                if difficulty == 'easy' and mastery >= 80.0:
                    # Check if they've tried medium
                    if 'medium' not in cat_stats.by_difficulty or cat_stats.by_difficulty['medium'].attempts == 0:
                        recommendations.append(
                            f"You've mastered easy {category} scenarios ({mastery:.0f}% mastery)! "
                            f"Try medium difficulty to progress."
                        )
                elif difficulty == 'medium' and mastery >= 80.0:
                    # Check if they've tried hard
                    if 'hard' not in cat_stats.by_difficulty or cat_stats.by_difficulty['hard'].attempts == 0:
                        recommendations.append(
                            f"Excellent work on medium {category} scenarios ({mastery:.0f}% mastery)! "
                            f"Challenge yourself with hard difficulty."
                        )
                elif difficulty == 'hard' and mastery >= 80.0:
                    recommendations.append(
                        f"Outstanding! You've mastered hard {category} scenarios ({mastery:.0f}% mastery)!"
                    )
        
        # Check for weak categories
        if statistics.by_category:
            weakest_category = min(
                statistics.by_category.items(),
                key=lambda x: x[1].average_score
            )
            if weakest_category[1].average_score < 50:
                recommendations.append(
                    f"Practice more {weakest_category[0]} scenarios to improve"
                )
        
        # Check streak
        if statistics.current_streak >= 5:
            recommendations.append(f"Amazing {statistics.current_streak}-scenario streak! Keep it up!")
        elif statistics.current_streak == 0 and statistics.total_attempts > 0:
            recommendations.append("Don't give up! Review the feedback and try again")
        
        return recommendations
    
    def _calculate_mastery_percentage(self, diff_stats: DifficultyStats) -> float:
        """
        Calculate mastery percentage for a difficulty level
        
        Mastery is based on:
        - Pass rate (60% weight)
        - Average score relative to max (40% weight)
        
        Args:
            diff_stats: Difficulty statistics
        
        Returns:
            Mastery percentage (0-100)
        """
        if diff_stats.attempts == 0:
            return 0.0
        
        # Calculate pass rate
        pass_rate = (diff_stats.passed / diff_stats.attempts) * 100
        
        # Calculate average score percentage (assuming max score per scenario)
        # We use average_score as a percentage of typical max scores
        # For simplicity, we'll use the average_score directly as it's already normalized
        score_percentage = min(diff_stats.average_score, 100)
        
        # Weighted combination
        mastery = (pass_rate * 0.6) + (score_percentage * 0.4)
        
        return mastery
    
    def get_mastery_by_category_and_difficulty(self, category: Optional[str] = None) -> Dict[str, Dict[str, float]]:
        """
        Get mastery percentages organized by category and difficulty
        
        Args:
            category: Optional category filter
        
        Returns:
            Dictionary mapping category -> difficulty -> mastery percentage
        """
        statistics = self.get_statistics(category)
        mastery_data = {}
        
        for cat, cat_stats in statistics.by_category.items():
            mastery_data[cat] = {}
            for difficulty, diff_stats in cat_stats.by_difficulty.items():
                mastery_data[cat][difficulty] = self._calculate_mastery_percentage(diff_stats)
        
        return mastery_data
    
    def should_progress_to_next_difficulty(self, category: str, current_difficulty: str) -> bool:
        """
        Determine if user should progress to next difficulty level
        
        Args:
            category: Category to check
            current_difficulty: Current difficulty level
        
        Returns:
            True if user should progress to next difficulty
        """
        statistics = self.get_statistics(category)
        
        if category not in statistics.by_category:
            return False
        
        cat_stats = statistics.by_category[category]
        
        if current_difficulty not in cat_stats.by_difficulty:
            return False
        
        diff_stats = cat_stats.by_difficulty[current_difficulty]
        mastery = self._calculate_mastery_percentage(diff_stats)
        
        # Recommend progression if mastery >= 80%
        return mastery >= 80.0
    
    def unlock_achievement(self, name: str, description: str) -> int:
        """
        Unlock an achievement
        
        Args:
            name: Achievement name
            description: Achievement description
        
        Returns:
            ID of the achievement
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if achievement already exists
        cursor.execute("SELECT id FROM achievements WHERE name = ?", (name,))
        existing = cursor.fetchone()
        
        if existing:
            # Update unlock time
            cursor.execute(
                "UPDATE achievements SET unlocked_at = ? WHERE name = ?",
                (datetime.now(), name)
            )
            achievement_id = existing[0]
        else:
            # Create new achievement
            cursor.execute(
                "INSERT INTO achievements (name, description, unlocked_at) VALUES (?, ?, ?)",
                (name, description, datetime.now())
            )
            achievement_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return achievement_id
    
    def get_all_attempts(self, scenario_id: Optional[str] = None) -> List[Attempt]:
        """
        Get all attempts, optionally filtered by scenario
        
        Args:
            scenario_id: Optional scenario ID to filter by
        
        Returns:
            List of Attempt objects
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if scenario_id:
            cursor.execute("SELECT * FROM attempts WHERE scenario_id = ? ORDER BY timestamp", 
                         (scenario_id,))
        else:
            cursor.execute("SELECT * FROM attempts ORDER BY timestamp")
        
        rows = cursor.fetchall()
        conn.close()
        
        attempts = [
            Attempt(
                id=row['id'],
                scenario_id=row['scenario_id'],
                category=row['category'],
                difficulty=row['difficulty'],
                score=row['score'],
                max_score=row['max_score'],
                passed=bool(row['passed']),
                duration=row['duration'],
                timestamp=datetime.fromisoformat(row['timestamp'])
            )
            for row in rows
        ]
        
        return attempts
    
    def reset_progress(self) -> None:
        """
        Reset all progress and statistics
        Deletes all attempts and achievements from the database
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM attempts")
        cursor.execute("DELETE FROM achievements")
        
        conn.commit()
        conn.close()
