"""
Unit and property-based tests for database manager and scorer
"""

import os
import tempfile
import sqlite3
from datetime import datetime
import pytest
from hypothesis import given, strategies as st, settings, assume

from src.utils.db_manager import (
    Scorer,
    Attempt,
    Achievement,
    Statistics,
    CategoryStats,
    DifficultyStats
)


# Hypothesis strategies
@st.composite
def scenario_id_strategy(draw):
    """Generate valid scenario IDs"""
    category = draw(st.sampled_from(['networking', 'storage', 'users_groups', 
                                     'operations_deployment', 'essential_commands']))
    num = draw(st.integers(min_value=1, max_value=999))
    return f"{category}_{num:03d}"


@st.composite
def attempt_data_strategy(draw):
    """Generate valid attempt data"""
    return {
        'scenario_id': draw(scenario_id_strategy()),
        'category': draw(st.sampled_from(['networking', 'storage', 'users_groups',
                                         'operations_deployment', 'essential_commands'])),
        'difficulty': draw(st.sampled_from(['easy', 'medium', 'hard'])),
        'score': draw(st.integers(min_value=0, max_value=100)),
        'max_score': draw(st.integers(min_value=1, max_value=100)),
        'passed': draw(st.booleans()),
        'duration': draw(st.one_of(st.none(), st.integers(min_value=1, max_value=3600)))
    }


class TestScorerBasics:
    """Basic unit tests for Scorer"""
    
    def test_scorer_initialization(self):
        """Test that scorer can be initialized"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            scorer = Scorer(db_path)
            
            assert os.path.exists(db_path)
            
            # Verify tables exist
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}
            conn.close()
            
            assert 'attempts' in tables
            assert 'achievements' in tables
    
    def test_calculate_score_basic(self):
        """Test basic score calculation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            scorer = Scorer(db_path)
            
            multipliers = {'easy': 1.0, 'medium': 1.5, 'hard': 2.0}
            
            # All checks passed, easy difficulty
            score = scorer.calculate_score(100, 10, 10, 'easy', multipliers)
            assert score == 100
            
            # Half checks passed, medium difficulty
            score = scorer.calculate_score(100, 5, 10, 'medium', multipliers)
            assert score == 75  # (5/10) * 100 * 1.5
            
            # All checks passed, hard difficulty
            score = scorer.calculate_score(100, 10, 10, 'hard', multipliers)
            assert score == 200
    
    def test_record_and_retrieve_attempt(self):
        """Test recording and retrieving attempts"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            scorer = Scorer(db_path)
            
            # Record an attempt
            attempt_id = scorer.record_attempt(
                scenario_id='test_001',
                category='networking',
                difficulty='easy',
                score=80,
                max_score=100,
                passed=True,
                duration=120
            )
            
            assert attempt_id > 0
            
            # Retrieve attempts
            attempts = scorer.get_all_attempts()
            assert len(attempts) == 1
            assert attempts[0].scenario_id == 'test_001'
            assert attempts[0].score == 80
            assert attempts[0].passed is True


class TestStatistics:
    """Tests for statistics calculation"""
    
    def test_empty_statistics(self):
        """Test statistics with no attempts"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            scorer = Scorer(db_path)
            
            stats = scorer.get_statistics()
            
            assert stats.total_attempts == 0
            assert stats.total_passed == 0
            assert stats.total_score == 0
            assert stats.average_score == 0.0
            assert len(stats.by_category) == 0
    
    def test_statistics_with_attempts(self):
        """Test statistics calculation with multiple attempts"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            scorer = Scorer(db_path)
            
            # Record multiple attempts
            scorer.record_attempt('net_001', 'networking', 'easy', 80, 100, True, 120)
            scorer.record_attempt('net_002', 'networking', 'medium', 60, 100, True, 180)
            scorer.record_attempt('stor_001', 'storage', 'easy', 40, 100, False, 90)
            
            stats = scorer.get_statistics()
            
            assert stats.total_attempts == 3
            assert stats.total_passed == 2
            assert stats.total_score == 180
            assert abs(stats.average_score - 60.0) < 0.01
            
            # Check category stats
            assert 'networking' in stats.by_category
            assert 'storage' in stats.by_category
            
            net_stats = stats.by_category['networking']
            assert net_stats.attempts == 2
            assert net_stats.passed == 2
            assert net_stats.total_score == 140
    
    def test_streak_calculation(self):
        """Test streak calculation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            scorer = Scorer(db_path)
            
            # Record a streak of 3 passes
            scorer.record_attempt('test_001', 'networking', 'easy', 80, 100, True)
            scorer.record_attempt('test_002', 'networking', 'easy', 90, 100, True)
            scorer.record_attempt('test_003', 'networking', 'easy', 85, 100, True)
            
            stats = scorer.get_statistics()
            assert stats.current_streak == 3
            assert stats.best_streak == 3
            
            # Break the streak
            scorer.record_attempt('test_004', 'networking', 'easy', 40, 100, False)
            
            stats = scorer.get_statistics()
            assert stats.current_streak == 0
            assert stats.best_streak == 3


class TestAchievements:
    """Tests for achievement system"""
    
    def test_unlock_achievement(self):
        """Test unlocking achievements"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            scorer = Scorer(db_path)
            
            achievement_id = scorer.unlock_achievement(
                "First Steps",
                "Complete your first scenario"
            )
            
            assert achievement_id > 0
            
            stats = scorer.get_statistics()
            assert len(stats.achievements) == 1
            assert stats.achievements[0].name == "First Steps"
    
    def test_duplicate_achievement(self):
        """Test that unlocking same achievement twice updates it"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            scorer = Scorer(db_path)
            
            id1 = scorer.unlock_achievement("Test", "Test achievement")
            id2 = scorer.unlock_achievement("Test", "Test achievement")
            
            # Should be same ID
            assert id1 == id2
            
            stats = scorer.get_statistics()
            assert len(stats.achievements) == 1


class TestRecommendations:
    """Tests for recommendation system"""
    
    def test_recommendations_no_attempts(self):
        """Test recommendations with no attempts"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            scorer = Scorer(db_path)
            
            stats = scorer.get_statistics()
            recommendations = scorer.get_recommendations(stats)
            
            assert len(recommendations) > 0
            assert any("easy" in r.lower() for r in recommendations)
    
    def test_recommendations_high_performance(self):
        """Test recommendations for high performers"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            scorer = Scorer(db_path)
            
            # Record many successful attempts
            for i in range(10):
                scorer.record_attempt(f'test_{i}', 'networking', 'easy', 90, 100, True)
            
            stats = scorer.get_statistics()
            recommendations = scorer.get_recommendations(stats)
            
            assert any("harder" in r.lower() or "challenge" in r.lower() 
                      for r in recommendations)


class TestPropertyBasedScorer:
    """Property-based tests for scorer"""
    
    # Feature: lfcs-practice-environment, Property 6: Score calculation consistency
    @given(
        max_score=st.integers(min_value=1, max_value=1000),
        checks_passed=st.integers(min_value=0, max_value=100),
        checks_total=st.integers(min_value=1, max_value=100),
        difficulty=st.sampled_from(['easy', 'medium', 'hard'])
    )
    @settings(max_examples=100, deadline=None)
    def test_score_calculation_consistency(self, max_score, checks_passed, checks_total, difficulty):
        """
        Property: For any validation result with the same number of passed checks and 
        scenario difficulty, the calculated score should be identical across multiple calculations.
        
        Validates: Requirements 4.1
        """
        # Ensure checks_passed <= checks_total
        assume(checks_passed <= checks_total)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            scorer = Scorer(db_path)
            
            # Define difficulty multipliers
            multipliers = {'easy': 1.0, 'medium': 1.5, 'hard': 2.0}
            
            # Calculate score multiple times
            score1 = scorer.calculate_score(max_score, checks_passed, checks_total, 
                                           difficulty, multipliers)
            score2 = scorer.calculate_score(max_score, checks_passed, checks_total, 
                                           difficulty, multipliers)
            score3 = scorer.calculate_score(max_score, checks_passed, checks_total, 
                                           difficulty, multipliers)
            
            # All calculations should produce identical results
            assert score1 == score2, \
                f"Score calculation should be consistent: {score1} != {score2}"
            assert score2 == score3, \
                f"Score calculation should be consistent: {score2} != {score3}"
            assert score1 == score3, \
                f"Score calculation should be consistent: {score1} != {score3}"
            
            # Verify score is non-negative
            assert score1 >= 0, "Score should be non-negative"
            
            # Verify score respects the formula
            if checks_total > 0:
                expected_base = (checks_passed / checks_total) * max_score
                expected_final = int(expected_base * multipliers[difficulty])
                assert score1 == expected_final, \
                    f"Score should match formula: expected {expected_final}, got {score1}"
    
    # Feature: lfcs-practice-environment, Property 7: Progress persistence
    @given(attempt_data=attempt_data_strategy())
    @settings(max_examples=100, deadline=None)
    def test_progress_persistence(self, attempt_data):
        """
        Property: For any completed scenario, when the result is persisted to the database,
        querying the database immediately afterward should return that attempt with all correct details.
        
        Validates: Requirements 4.2, 4.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            scorer = Scorer(db_path)
            
            # Ensure max_score >= score
            if attempt_data['max_score'] < attempt_data['score']:
                attempt_data['max_score'] = attempt_data['score']
            
            # Record attempt
            attempt_id = scorer.record_attempt(
                scenario_id=attempt_data['scenario_id'],
                category=attempt_data['category'],
                difficulty=attempt_data['difficulty'],
                score=attempt_data['score'],
                max_score=attempt_data['max_score'],
                passed=attempt_data['passed'],
                duration=attempt_data['duration']
            )
            
            # Retrieve attempt
            attempts = scorer.get_all_attempts(scenario_id=attempt_data['scenario_id'])
            
            # Verify persistence
            assert len(attempts) > 0, "Attempt should be persisted"
            
            retrieved = attempts[-1]  # Get most recent
            assert retrieved.scenario_id == attempt_data['scenario_id'], \
                "Scenario ID should match"
            assert retrieved.category == attempt_data['category'], \
                "Category should match"
            assert retrieved.difficulty == attempt_data['difficulty'], \
                "Difficulty should match"
            assert retrieved.score == attempt_data['score'], \
                "Score should match"
            assert retrieved.max_score == attempt_data['max_score'], \
                "Max score should match"
            assert retrieved.passed == attempt_data['passed'], \
                "Passed status should match"
            assert retrieved.duration == attempt_data['duration'], \
                "Duration should match"
    
    # Feature: lfcs-practice-environment, Property 8: Statistics accuracy
    @given(attempts_list=st.lists(attempt_data_strategy(), min_size=1, max_size=20))
    @settings(max_examples=100, deadline=None)
    def test_statistics_accuracy(self, attempts_list):
        """
        Property: For any set of recorded attempts, the calculated statistics 
        (completion rate, average score, performance by category) should accurately 
        reflect the sum and averages of those attempts.
        
        Validates: Requirements 4.3
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            scorer = Scorer(db_path)
            
            # Record all attempts
            for attempt_data in attempts_list:
                # Ensure max_score >= score
                if attempt_data['max_score'] < attempt_data['score']:
                    attempt_data['max_score'] = attempt_data['score']
                
                scorer.record_attempt(
                    scenario_id=attempt_data['scenario_id'],
                    category=attempt_data['category'],
                    difficulty=attempt_data['difficulty'],
                    score=attempt_data['score'],
                    max_score=attempt_data['max_score'],
                    passed=attempt_data['passed'],
                    duration=attempt_data['duration']
                )
            
            # Get statistics
            stats = scorer.get_statistics()
            
            # Verify total attempts
            assert stats.total_attempts == len(attempts_list), \
                "Total attempts should match number of recorded attempts"
            
            # Verify total passed
            expected_passed = sum(1 for a in attempts_list if a['passed'])
            assert stats.total_passed == expected_passed, \
                "Total passed should match number of passed attempts"
            
            # Verify total score
            expected_total_score = sum(a['score'] for a in attempts_list)
            assert stats.total_score == expected_total_score, \
                "Total score should be sum of all scores"
            
            # Verify average score
            expected_avg = expected_total_score / len(attempts_list)
            assert abs(stats.average_score - expected_avg) < 0.01, \
                f"Average score should be {expected_avg}, got {stats.average_score}"
            
            # Verify category statistics
            categories = set(a['category'] for a in attempts_list)
            for category in categories:
                assert category in stats.by_category, \
                    f"Category {category} should be in statistics"
                
                cat_attempts = [a for a in attempts_list if a['category'] == category]
                cat_stats = stats.by_category[category]
                
                assert cat_stats.attempts == len(cat_attempts), \
                    f"Category {category} attempt count should match"
                
                expected_cat_score = sum(a['score'] for a in cat_attempts)
                assert cat_stats.total_score == expected_cat_score, \
                    f"Category {category} total score should match"
    
    # Feature: lfcs-practice-environment, Property 14: Difficulty multiplier consistency
    @given(
        max_score=st.integers(min_value=1, max_value=1000),
        checks_passed=st.integers(min_value=1, max_value=100),
        checks_total=st.integers(min_value=1, max_value=100)
    )
    @settings(max_examples=100, deadline=None)
    def test_difficulty_multiplier_consistency(self, max_score, checks_passed, checks_total):
        """
        Property: For any two scenarios with different difficulty levels but identical 
        validation results, the harder scenario should always award more points than the easier one.
        
        Validates: Requirements 12.3
        """
        # Ensure checks_passed <= checks_total
        assume(checks_passed <= checks_total)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            scorer = Scorer(db_path)
            
            # Define difficulty multipliers (must be strictly increasing)
            multipliers = {'easy': 1.0, 'medium': 1.5, 'hard': 2.0}
            
            # Calculate scores for each difficulty level
            easy_score = scorer.calculate_score(max_score, checks_passed, checks_total, 
                                               'easy', multipliers)
            medium_score = scorer.calculate_score(max_score, checks_passed, checks_total, 
                                                 'medium', multipliers)
            hard_score = scorer.calculate_score(max_score, checks_passed, checks_total, 
                                               'hard', multipliers)
            
            # Verify difficulty ordering: easy <= medium <= hard
            assert easy_score <= medium_score, \
                f"Medium difficulty should award >= easy: easy={easy_score}, medium={medium_score}"
            assert medium_score <= hard_score, \
                f"Hard difficulty should award >= medium: medium={medium_score}, hard={hard_score}"
            assert easy_score <= hard_score, \
                f"Hard difficulty should award >= easy: easy={easy_score}, hard={hard_score}"
            
            # If checks_passed > 0, verify strict inequality (harder should give MORE points)
            if checks_passed > 0 and checks_total > 0:
                # Due to integer truncation, we might have equality in edge cases
                # But the relationship should hold based on multipliers
                assert easy_score * multipliers['medium'] / multipliers['easy'] <= medium_score + 1, \
                    "Medium score should reflect multiplier relationship"
                assert easy_score * multipliers['hard'] / multipliers['easy'] <= hard_score + 1, \
                    "Hard score should reflect multiplier relationship"


class TestProgressiveDifficulty:
    """Tests for progressive difficulty system (Task 16)"""
    
    def test_mastery_percentage_calculation(self):
        """Test mastery percentage calculation for a difficulty level"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            scorer = Scorer(db_path)
            
            # Record some attempts for easy difficulty
            scorer.record_attempt("test_01", "networking", "easy", 80, 100, True, 60)
            scorer.record_attempt("test_02", "networking", "easy", 90, 100, True, 45)
            scorer.record_attempt("test_03", "networking", "easy", 70, 100, True, 50)
            scorer.record_attempt("test_04", "networking", "easy", 60, 100, False, 55)
            
            # Get statistics
            stats = scorer.get_statistics("networking")
            
            # Get difficulty stats for easy
            diff_stats = stats.by_category["networking"].by_difficulty["easy"]
            
            # Calculate mastery
            mastery = scorer._calculate_mastery_percentage(diff_stats)
            
            # Verify mastery is calculated correctly
            # Pass rate: 3/4 = 75%
            # Average score: (80+90+70+60)/4 = 75
            # Mastery: 75 * 0.6 + 75 * 0.4 = 45 + 30 = 75
            assert abs(mastery - 75.0) < 0.1, f"Expected mastery ~75%, got {mastery}%"
    
    def test_mastery_by_category_and_difficulty(self):
        """Test getting mastery percentages organized by category and difficulty"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            scorer = Scorer(db_path)
            
            # Record attempts across multiple categories and difficulties
            scorer.record_attempt("net_easy_01", "networking", "easy", 90, 100, True, 60)
            scorer.record_attempt("net_easy_02", "networking", "easy", 85, 100, True, 55)
            scorer.record_attempt("net_medium_01", "networking", "medium", 70, 100, True, 70)
            scorer.record_attempt("storage_easy_01", "storage", "easy", 95, 100, True, 50)
            
            # Get mastery data
            mastery_data = scorer.get_mastery_by_category_and_difficulty()
            
            # Verify structure
            assert "networking" in mastery_data
            assert "storage" in mastery_data
            assert "easy" in mastery_data["networking"]
            assert "medium" in mastery_data["networking"]
            assert "easy" in mastery_data["storage"]
            
            # Verify mastery values are percentages
            for category, difficulties in mastery_data.items():
                for difficulty, mastery in difficulties.items():
                    assert 0 <= mastery <= 100, \
                        f"Mastery for {category}/{difficulty} should be 0-100%, got {mastery}%"
    
    def test_should_progress_to_next_difficulty(self):
        """Test recommendation logic for difficulty progression"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            scorer = Scorer(db_path)
            
            # Record high-mastery attempts for easy difficulty
            for i in range(10):
                scorer.record_attempt(f"test_{i}", "networking", "easy", 90, 100, True, 60)
            
            # Should recommend progression
            should_progress = scorer.should_progress_to_next_difficulty("networking", "easy")
            assert should_progress, "Should recommend progression with high mastery"
            
            # Record low-mastery attempts for medium difficulty
            for i in range(10):
                scorer.record_attempt(f"test_med_{i}", "storage", "medium", 40, 100, False, 60)
            
            # Should not recommend progression
            should_progress = scorer.should_progress_to_next_difficulty("storage", "medium")
            assert not should_progress, "Should not recommend progression with low mastery"
    
    def test_recommendations_include_progression(self):
        """Test that recommendations include difficulty progression suggestions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            scorer = Scorer(db_path)
            
            # Record high-mastery attempts for easy difficulty
            for i in range(10):
                scorer.record_attempt(f"test_{i}", "networking", "easy", 95, 100, True, 60)
            
            # Get recommendations
            stats = scorer.get_statistics()
            recommendations = scorer.get_recommendations(stats)
            
            # Should include progression recommendation
            progression_found = any("medium" in rec.lower() and "networking" in rec.lower() 
                                   for rec in recommendations)
            assert progression_found, \
                f"Recommendations should suggest progressing to medium difficulty. Got: {recommendations}"
    
    def test_mastery_with_no_attempts(self):
        """Test mastery calculation with no attempts"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            scorer = Scorer(db_path)
            
            # Create a DifficultyStats with no attempts
            from src.utils.db_manager import DifficultyStats
            diff_stats = DifficultyStats(
                difficulty="easy",
                attempts=0,
                passed=0,
                total_score=0,
                average_score=0.0
            )
            
            mastery = scorer._calculate_mastery_percentage(diff_stats)
            assert mastery == 0.0, "Mastery should be 0% with no attempts"
    
    def test_mastery_perfect_performance(self):
        """Test mastery calculation with perfect performance"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            scorer = Scorer(db_path)
            
            # Record perfect attempts
            for i in range(5):
                scorer.record_attempt(f"test_{i}", "networking", "hard", 100, 100, True, 60)
            
            stats = scorer.get_statistics("networking")
            diff_stats = stats.by_category["networking"].by_difficulty["hard"]
            
            mastery = scorer._calculate_mastery_percentage(diff_stats)
            
            # Perfect performance: 100% pass rate, 100 average score
            # Mastery: 100 * 0.6 + 100 * 0.4 = 100
            assert abs(mastery - 100.0) < 0.1, f"Expected 100% mastery, got {mastery}%"
