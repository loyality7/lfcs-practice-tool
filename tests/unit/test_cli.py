"""
Unit and Property-Based Tests for CLI Interface
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from unittest.mock import Mock, MagicMock, patch
import sys
from io import StringIO

from src.cli.main_cli import CLI
from src.core.engine import Engine
from src.utils.config import Config


# Test fixtures
@pytest.fixture
def mock_engine():
    """Create a mock engine for testing"""
    engine = Mock(spec=Engine)
    engine.config = Config()
    engine.start_session = Mock()
    engine.get_statistics = Mock()
    engine.list_scenarios = Mock(return_value=[])
    engine.scorer = Mock()
    engine.scorer.reset_progress = Mock()
    engine.shutdown = Mock()
    return engine


@pytest.fixture
def cli(mock_engine):
    """Create CLI instance with mock engine"""
    return CLI(mock_engine)


# Unit Tests
class TestCLIBasics:
    """Basic unit tests for CLI functionality"""
    
    def test_cli_initialization(self, mock_engine):
        """Test CLI initializes correctly"""
        cli = CLI(mock_engine)
        assert cli.engine == mock_engine
        assert cli.config == mock_engine.config
    
    def test_no_arguments_shows_help(self, cli):
        """Test that running with no arguments shows help"""
        exit_code = cli.run([])
        assert exit_code == 0
    
    def test_invalid_command_returns_error(self, cli):
        """Test that invalid commands return non-zero exit code"""
        with patch('sys.stderr', new=StringIO()):
            exit_code = cli.run(['invalid_command'])
            assert exit_code != 0
    
    def test_start_command_basic(self, cli, mock_engine):
        """Test basic start command"""
        mock_engine.start_session.return_value = Mock(
            passed=True,
            score=100,
            scenario=Mock(points=100),
            validation_result=Mock(
                checks_passed=5,
                checks_total=5,
                check_results=[]
            ),
            duration=60
        )
        
        exit_code = cli.run(['start'])
        assert exit_code == 0
        mock_engine.start_session.assert_called_once()
    
    def test_stats_command_basic(self, cli, mock_engine):
        """Test basic stats command"""
        from src.utils.db_manager import Statistics
        
        mock_engine.get_statistics.return_value = Statistics(
            total_attempts=10,
            total_passed=8,
            total_score=800,
            average_score=80.0,
            by_category={},
            current_streak=3,
            best_streak=5,
            achievements=[]
        )
        
        # Mock get_recommendations to return a list
        mock_engine.get_recommendations.return_value = [
            "Great job! Try harder scenarios to challenge yourself"
        ]
        
        exit_code = cli.run(['stats'])
        assert exit_code == 0
        mock_engine.get_statistics.assert_called_once()
    
    def test_list_command_basic(self, cli, mock_engine):
        """Test basic list command"""
        exit_code = cli.run(['list'])
        assert exit_code == 0
        mock_engine.list_scenarios.assert_called_once()
    
    def test_reset_requires_confirm(self, cli):
        """Test that reset without --confirm flag fails"""
        with patch('sys.stderr', new=StringIO()):
            exit_code = cli.run(['reset'])
        # argparse returns 2 for missing required arguments
        assert exit_code == 2


# Helper function to create CLI instance
def create_test_cli():
    """Create a CLI instance with mock engine for testing"""
    engine = Mock(spec=Engine)
    engine.config = Config()
    engine.start_session = Mock()
    engine.get_statistics = Mock()
    engine.list_scenarios = Mock(return_value=[])
    engine.scorer = Mock()
    engine.scorer.reset_progress = Mock()
    engine.shutdown = Mock()
    return CLI(engine), engine


# Property-Based Tests
class TestCLICommandValidation:
    """Property-based tests for CLI command validation"""
    
    # Feature: lfcs-practice-environment, Property 9: CLI command validation
    # Validates: Requirements 5.5
    @settings(max_examples=100)
    @given(
        invalid_category=st.text(min_size=1).filter(
            lambda x: x not in ['operations_deployment', 'networking', 'storage', 
                               'essential_commands', 'users_groups']
        ),
    )
    def test_property_invalid_category_rejected(self, invalid_category):
        """
        Property: For any invalid category, the CLI should reject it with an error
        
        This tests that the CLI properly validates category arguments and rejects
        invalid values without proceeding with execution.
        """
        # Avoid categories that might be interpreted as other arguments
        assume(not invalid_category.startswith('-'))
        assume(len(invalid_category) < 100)  # Reasonable length
        
        cli, _ = create_test_cli()
        
        with patch('sys.stderr', new=StringIO()):
            exit_code = cli.run(['start', '--category', invalid_category])
        
        # Should return non-zero exit code for invalid input
        assert exit_code != 0, f"CLI should reject invalid category '{invalid_category}'"
    
    # Feature: lfcs-practice-environment, Property 9: CLI command validation
    # Validates: Requirements 5.5
    @settings(max_examples=100)
    @given(
        invalid_difficulty=st.text(min_size=1).filter(
            lambda x: x not in ['easy', 'medium', 'hard']
        ),
    )
    def test_property_invalid_difficulty_rejected(self, invalid_difficulty):
        """
        Property: For any invalid difficulty, the CLI should reject it with an error
        
        This tests that the CLI properly validates difficulty arguments and rejects
        invalid values without proceeding with execution.
        """
        # Avoid difficulties that might be interpreted as other arguments
        assume(not invalid_difficulty.startswith('-'))
        assume(len(invalid_difficulty) < 100)  # Reasonable length
        
        cli, _ = create_test_cli()
        
        with patch('sys.stderr', new=StringIO()):
            exit_code = cli.run(['start', '--difficulty', invalid_difficulty])
        
        # Should return non-zero exit code for invalid input
        assert exit_code != 0, f"CLI should reject invalid difficulty '{invalid_difficulty}'"
    
    # Feature: lfcs-practice-environment, Property 9: CLI command validation
    # Validates: Requirements 5.5
    @settings(max_examples=100)
    @given(
        invalid_distribution=st.text(min_size=1).filter(
            lambda x: x not in ['ubuntu', 'centos', 'rocky']
        ),
    )
    def test_property_invalid_distribution_rejected(self, invalid_distribution):
        """
        Property: For any invalid distribution, the CLI should reject it with an error
        
        This tests that the CLI properly validates distribution arguments and rejects
        invalid values without proceeding with execution.
        """
        # Avoid distributions that might be interpreted as other arguments
        assume(not invalid_distribution.startswith('-'))
        assume(len(invalid_distribution) < 100)  # Reasonable length
        
        cli, _ = create_test_cli()
        
        with patch('sys.stderr', new=StringIO()):
            exit_code = cli.run(['start', '--distribution', invalid_distribution])
        
        # Should return non-zero exit code for invalid input
        assert exit_code != 0, f"CLI should reject invalid distribution '{invalid_distribution}'"
    
    # Feature: lfcs-practice-environment, Property 9: CLI command validation
    # Validates: Requirements 5.5
    @settings(max_examples=100)
    @given(
        invalid_command=st.text(min_size=1).filter(
            lambda x: x not in ['start', 'stats', 'list', 'reset']
        ),
    )
    def test_property_invalid_command_rejected(self, invalid_command):
        """
        Property: For any invalid command, the CLI should reject it with an error
        
        This tests that the CLI properly validates top-level commands and rejects
        invalid values without proceeding with execution.
        """
        # Avoid commands that might be interpreted as flags
        assume(not invalid_command.startswith('-'))
        assume(len(invalid_command) < 100)  # Reasonable length
        assume(invalid_command not in ['help', '--help', '-h'])  # Help is valid
        
        cli, _ = create_test_cli()
        
        with patch('sys.stderr', new=StringIO()):
            exit_code = cli.run([invalid_command])
        
        # Should return non-zero exit code for invalid input
        assert exit_code != 0, f"CLI should reject invalid command '{invalid_command}'"
    
    # Feature: lfcs-practice-environment, Property 9: CLI command validation
    # Validates: Requirements 5.5
    @settings(max_examples=100)
    @given(
        valid_category=st.sampled_from(['operations_deployment', 'networking', 
                                       'storage', 'essential_commands', 'users_groups']),
        valid_difficulty=st.sampled_from(['easy', 'medium', 'hard']),
        valid_distribution=st.sampled_from(['ubuntu', 'centos', 'rocky'])
    )
    def test_property_valid_arguments_accepted(self, valid_category, valid_difficulty, 
                                               valid_distribution):
        """
        Property: For any valid argument combination, the CLI should accept it
        
        This tests that the CLI properly accepts all valid combinations of arguments
        and proceeds with execution (calls the engine).
        """
        cli, mock_engine = create_test_cli()
        
        # Mock successful session
        mock_engine.start_session.return_value = Mock(
            passed=True,
            score=100,
            scenario=Mock(points=100),
            validation_result=Mock(
                checks_passed=5,
                checks_total=5,
                check_results=[]
            ),
            duration=60
        )
        
        exit_code = cli.run([
            'start',
            '--category', valid_category,
            '--difficulty', valid_difficulty,
            '--distribution', valid_distribution
        ])
        
        # Should succeed with valid arguments
        assert exit_code == 0, (
            f"CLI should accept valid arguments: "
            f"category={valid_category}, difficulty={valid_difficulty}, "
            f"distribution={valid_distribution}"
        )
        
        # Should have called the engine
        mock_engine.start_session.assert_called_once()
        
        # Verify correct arguments were passed
        call_args = mock_engine.start_session.call_args
        assert call_args.kwargs['category'] == valid_category
        assert call_args.kwargs['difficulty'] == valid_difficulty
        assert call_args.kwargs['distribution'] == valid_distribution
    
    # Feature: lfcs-practice-environment, Property 9: CLI command validation
    # Validates: Requirements 5.5
    @settings(max_examples=100)
    @given(
        flag_name=st.text(
            alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'), min_codepoint=ord('a')),
            min_size=1,
            max_size=15
        ).filter(
            lambda x: x not in [
                'category', 'difficulty', 'distribution', 'ai',
                'confirm', 'help', 'version', 'h', 'v'
            ]
        )
    )
    def test_property_unknown_flags_rejected(self, flag_name):
        """
        Property: For any unknown flag, the CLI should reject it with an error
        
        This tests that the CLI properly validates flags and rejects unknown ones
        without proceeding with execution.
        """
        cli, _ = create_test_cli()
        
        unknown_flag = f'--{flag_name}'
        
        with patch('sys.stderr', new=StringIO()):
            exit_code = cli.run(['start', unknown_flag])
        
        # Should return non-zero exit code for unknown flag
        assert exit_code != 0, f"CLI should reject unknown flag '{unknown_flag}'"


class TestCLIErrorHandling:
    """Test CLI error handling"""
    
    def test_engine_error_handled_gracefully(self, cli, mock_engine):
        """Test that engine errors are handled gracefully"""
        mock_engine.start_session.side_effect = Exception("Engine error")
        
        exit_code = cli.run(['start'])
        assert exit_code == 1
    
    def test_keyboard_interrupt_handled(self, cli, mock_engine):
        """Test that keyboard interrupt is handled"""
        mock_engine.start_session.side_effect = KeyboardInterrupt()
        
        exit_code = cli.run(['start'])
        assert exit_code == 130
    
    def test_value_error_handled(self, cli, mock_engine):
        """Test that ValueError is handled with appropriate message"""
        mock_engine.start_session.side_effect = ValueError("No scenarios found")
        
        exit_code = cli.run(['start', '--category', 'networking'])
        assert exit_code == 1
