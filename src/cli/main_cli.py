"""
Main CLI Interface for LFCS Practice Tool
Handles user interaction, command parsing, and output formatting
"""

import argparse
import sys
import logging
from typing import Optional, List
from datetime import datetime

from ..core.engine import Engine, SessionResult
from ..utils.config import load_config, Config
from ..utils.db_manager import Statistics
from ..utils.colors import Colors, success, error, warning, info, highlight, header, command, dim
from ..utils import banner
from ..utils.version_check import get_current_version
from ..learn import ModuleLoader, DifficultyLevel
from ..learn.interactive_shell import InteractiveShell
from ..docker_manager.environment import DockerEnvironment


logger = logging.getLogger(__name__)


class CLI:
    """
    Command-line interface for LFCS Practice Tool
    
    Responsibilities:
    - Parse command-line arguments
    - Route commands to appropriate handlers
    - Format and display output to users
    - Handle user input validation
    """
    
    def __init__(self, engine: Optional[Engine]):
        """
        Initialize CLI with core engine
        
        Args:
            engine: Initialized Engine instance (can be None for help commands)
        """
        self.engine = engine
        self.config = engine.config if engine else None
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Main entry point for CLI
        
        Args:
            args: Command-line arguments (defaults to sys.argv[1:])
        
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        parser = self._create_parser()
        
        # Parse arguments
        if args is None:
            args = sys.argv[1:]
        
        # Automatic update check (non-blocking)
        # Skip check ONLY for help, version, or update commands
        if not any(cmd in args for cmd in ['--help', '-h', '--version', 'update']):
            try:
                from ..utils.version_check import check_for_updates, print_update_notification
                
                # Check for updates (uses cache, max once per day)
                new_version = check_for_updates()
                if new_version:
                    print_update_notification(new_version)
            except Exception:
                # Silently fail - don't interrupt user experience
                pass
        
        # Show welcome screen if no arguments provided
        if not args:
            version = get_current_version()
            banner.print_welcome_screen(version)
            return 0
        
        # Handle help and version before parsing
        if '--help' in args or '-h' in args:
            self._print_help()
            return 0
        
        if '--version' in args:
            version = get_current_version()
            banner.print_mini_banner()
            print(f"\n{highlight('Version:')} {info(version)}\n")
            return 0
        
        try:
            parsed_args = parser.parse_args(args)
            
            # Route to appropriate command handler
            if parsed_args.command == 'start':
                return self.cmd_start(
                    category=parsed_args.category,
                    difficulty=parsed_args.difficulty,
                    distribution=parsed_args.distribution,
                    ai_mode=parsed_args.ai,
                    local_mode=parsed_args.local
                )
            elif parsed_args.command == 'stats':
                return self.cmd_stats(category=parsed_args.category)
            elif parsed_args.command == 'list':
                return self.cmd_list(
                    category=parsed_args.category,
                    difficulty=parsed_args.difficulty
                )
            elif parsed_args.command == 'reset':
                return self.cmd_reset(confirm=parsed_args.confirm)
            elif parsed_args.command == 'learn':
                return self.cmd_learn(
                    list_modules=parsed_args.list,
                    module_id=parsed_args.module,
                    continue_learning=parsed_args.continue_learn
                )
            elif parsed_args.command == 'update':
                return self.cmd_update(check_only=parsed_args.check)
            else:
                parser.print_help()
                return 1
        
        except SystemExit as e:
            # argparse calls sys.exit() on invalid arguments
            # Return the exit code (2 for argument errors, 0 for --help)
            return e.code if e.code is not None else 1
        except ValueError as e:
            print(f"Error: {e}")
            return 1
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            return 130
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            print(f"Error: {e}")
            return 1
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """
        Create argument parser with all commands and options
        
        Returns:
            Configured ArgumentParser
        """
        # Custom formatter to suppress default help and use our styled version
        class CustomHelpFormatter(argparse.RawDescriptionHelpFormatter):
            def format_help(self):
                # Return empty string - we'll handle help display ourselves
                return ""
        
        parser = argparse.ArgumentParser(
            prog='lfcs',
            description='LFCS Practice Tool - Interactive Linux System Administration Training',
            formatter_class=CustomHelpFormatter,
            add_help=False  # We'll add our own help
        )
        
        # Add help and version manually
        parser.add_argument(
            '-h', '--help',
            action='store_true',
            help='Show this help message and exit'
        )
        
        parser.add_argument(
            '--version',
            action='store_true',
            help='Show version number and exit'
        )
        
        # Subcommands
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Get categories and difficulties from config or use defaults
        categories = self.config.categories if self.config else [
            'operations_deployment', 'networking', 'storage', 
            'essential_commands', 'users_groups'
        ]
        difficulties = self.config.difficulties if self.config else ['easy', 'medium', 'hard']
        
        # Start command
        start_parser = subparsers.add_parser(
            'start',
            help='Start a new practice session',
            description='Start an interactive practice session. Select category, difficulty, and specific scenario.',
            add_help=False
        )
        start_parser.add_argument('-h', '--help', action='store_true', help='Show help for start command')
        start_parser.add_argument(
            '--category',
            choices=categories,
            help='Pre-filter by category (or select interactively)'
        )
        start_parser.add_argument(
            '--difficulty',
            choices=difficulties,
            help='Pre-filter by difficulty (or select interactively)'
        )
        start_parser.add_argument(
            '--distribution',
            choices=['ubuntu', 'centos', 'rocky'],
            help='Linux distribution for the practice container (default: ubuntu)'
        )
        start_parser.add_argument(
            '--ai',
            action='store_true',
            help='Enable AI-powered hints and validation (requires API key)'
        )
        start_parser.add_argument(
            '--local',
            action='store_true',
            help='Practice on local system without Docker (WARNING: modifies your actual system!)'
        )
        
        # Stats command
        stats_parser = subparsers.add_parser(
            'stats',
            help='View your statistics and progress',
            description='Display your performance statistics and progress'
        )
        stats_parser.add_argument(
            '--category',
            choices=categories,
            help='Show statistics for specific category only'
        )
        
        # List command
        list_parser = subparsers.add_parser(
            'list',
            help='List available scenarios',
            description='Browse all available scenarios interactively. Shows full task descriptions.'
        )
        list_parser.add_argument(
            '--category',
            choices=categories,
            help='Pre-filter by category (or select interactively)'
        )
        list_parser.add_argument(
            '--difficulty',
            choices=difficulties,
            help='Pre-filter by difficulty (or select interactively)'
        )
        
        # Reset command
        reset_parser = subparsers.add_parser(
            'reset',
            help='Reset your progress',
            description='Reset all progress and statistics (requires confirmation)'
        )
        reset_parser.add_argument(
            '--confirm',
            action='store_true',
            required=True,
            help='Confirm that you want to reset all progress'
        )
        
        # Learn command
        learn_parser = subparsers.add_parser(
            'learn',
            help='Interactive learning mode',
            description='Learn Linux from basics to LFCS level with interactive lessons and exercises'
        )
        learn_parser.add_argument(
            '--list',
            action='store_true',
            help='List all available learning modules'
        )
        learn_parser.add_argument(
            '--module',
            type=str,
            help='Start specific module by ID'
        )
        learn_parser.add_argument(
            '--continue',
            dest='continue_learn',
            action='store_true',
            help='Continue from last lesson'
        )
        
        # Update command
        update_parser = subparsers.add_parser(
            'update',
            help='Update lfcs to the latest version',
            description='Check for and install the latest version of lfcs from PyPI'
        )
        update_parser.add_argument(
            '--check',
            action='store_true',
            help='Only check for updates without installing'
        )
        
        return parser
    
    def cmd_start(self, category: Optional[str] = None,
                  difficulty: Optional[str] = None,
                  distribution: Optional[str] = None,
                  ai_mode: bool = False,
                  local_mode: bool = False) -> int:
        """
        Start a practice session with interactive scenario selection
        
        Args:
            category: Optional category filter
            difficulty: Optional difficulty filter
            distribution: Optional distribution selection
            ai_mode: Whether to enable AI features
            local_mode: Whether to practice on local system without Docker
        
        Returns:
            Exit code (0 for success)
        """
        # Handle local mode
        if local_mode or self.config.docker_config.local_mode:
            return self._start_local_session(category, difficulty, ai_mode)
        
        # Check if engine is available
        if self.engine is None:
            print(f"\n{error('Error:')} Engine not initialized. Docker is not accessible.")
            print(dim("Docker is running but you don't have permission to access it."))
            print(dim("Fix: sudo usermod -aG docker $USER"))
            print(dim("Then log out and log back in, or run: newgrp docker\n"))
            print(f"\n{info('Tip:')} You can use {highlight('--local')} flag to practice on your system without Docker")
            print(dim("Example: lfcs start --local\n"))
            return 1
        
        try:
            # Validate AI mode
            if ai_mode and not self.config.ai_enabled:
                print("Warning: AI mode requested but not configured. Continuing without AI features.")
                print("To enable AI, set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable.")
                ai_mode = False
            
            # Main practice loop
            while True:
                # Interactive selection if no filters provided
                scenario_id = None
                selected_category = category
                selected_difficulty = difficulty
                
                if selected_category is None:
                    selected_category = self._select_category()
                    if selected_category is None:
                        return 0  # User cancelled
                
                if selected_difficulty is None:
                    selected_difficulty = self._select_difficulty()
                    if selected_difficulty is None:
                        if category is None:
                            continue  # Go back to category selection
                        return 0  # User cancelled
                
                # Get scenarios matching the filters
                scenarios = self.engine.list_scenarios(selected_category, selected_difficulty)
                
                if not scenarios:
                    print(f"\n{error('No scenarios found matching your criteria.')}")
                    return 1
                
                # Let user select a specific scenario
                selected_scenario = self._select_scenario(scenarios, selected_category, selected_difficulty)
                if selected_scenario is None:
                    if category is None or difficulty is None:
                        continue  # Go back to start of wizard
                    return 0  # User cancelled
                
                scenario_id = selected_scenario.id
                
                # Display session start message
                banner.print_section_header("LFCS PRACTICE SESSION")
                
                filters = []
                filters.append(f"Category: {selected_category}")
                filters.append(f"Difficulty: {selected_difficulty}")
                filters.append(f"Scenario: {scenario_id}")
                if distribution:
                    filters.append(f"Distribution: {distribution}")
                
                print(dim("Selected: ") + info(" | ".join(filters)))
                print()
                
                # Start session with specific scenario
                result = self.engine.start_session(
                    category=selected_category,
                    difficulty=selected_difficulty,
                    distribution=distribution,
                    ai_mode=ai_mode,
                    scenario_id=scenario_id
                )
                
                # Display results
                self._display_session_result(result)
                
                # Ask if user wants to continue
                print(f"\n{highlight('What would you like to do?')}")
                print(f"  {info('1.')} Practice another scenario")
                print(f"  {info('2.')} Exit")
                print()
                
                while True:
                    try:
                        choice = input(f"{Colors.CYAN}Enter choice:{Colors.RESET} ").strip()
                        if choice == '1':
                            # Reset filters to allow new selection
                            category = None
                            difficulty = None
                            break
                        elif choice == '2':
                            print(f"\n{success('Good job! Keep practicing!')}\n")
                            return 0
                        else:
                            print(error("Invalid choice. Please enter 1 or 2."))
                    except KeyboardInterrupt:
                        print("\n")
                        return 0
            
        except ValueError as e:
            print(f"\nError: {e}")
            print("\nTry adjusting your filters or run 'lfcs list' to see available scenarios.")
            return 1
        except Exception as e:
            logger.error(f"Session failed: {e}", exc_info=True)
            print(f"\nError: Session failed - {e}")
            return 1
    
    def cmd_stats(self, category: Optional[str] = None) -> int:
        """
        Display user statistics
        
        Args:
            category: Optional category filter
        
        Returns:
            Exit code (0 for success)
        """
        # Check if engine is available
        if self.engine is None:
            print("\nError: Engine not initialized. Cannot retrieve statistics.")
            print("Please ensure Docker is installed and running.\n")
            return 1
        
        try:
            stats = self.engine.get_statistics(category)
            self._display_statistics(stats, category)
            return 0
        except Exception as e:
            logger.error(f"Failed to retrieve statistics: {e}", exc_info=True)
            print(f"Error: Could not retrieve statistics - {e}")
            return 1
    
    def cmd_list(self, category: Optional[str] = None,
                 difficulty: Optional[str] = None) -> int:
        """
        List available scenarios with interactive selection
        
        Args:
            category: Optional category filter
            difficulty: Optional difficulty filter
        
        Returns:
            Exit code (0 for success)
        """
        # Check if engine is available
        if self.engine is None:
            print("\nError: Engine not initialized. Cannot list scenarios.")
            print("Please ensure Docker is installed and running.\n")
            return 1
        
        try:
            # If no filters provided, make it interactive
            if category is None:
                category = self._select_category()
                if category is None:
                    return 0  # User cancelled
            
            if difficulty is None:
                difficulty = self._select_difficulty()
                if difficulty is None:
                    return 0  # User cancelled
            
            scenarios = self.engine.list_scenarios(category, difficulty)
            self._display_scenario_list(scenarios, category, difficulty)
            return 0
        except Exception as e:
            logger.error(f"Failed to list scenarios: {e}", exc_info=True)
            print(f"Error: Could not list scenarios - {e}")
            return 1
    
    def _select_category(self) -> Optional[str]:
        """
        Interactive category selection
        
        Returns:
            Selected category or None if cancelled
        """
        categories = self.config.categories if self.config else [
            'operations_deployment', 'networking', 'storage', 
            'essential_commands', 'users_groups'
        ]
        
        # Category icons and descriptions
        category_info = {
            'operations_deployment': ('⚙️', 'System operations, services, and deployment'),
            'networking': ('🌐', 'Network configuration and troubleshooting'),
            'storage': ('💾', 'Disk management, filesystems, and mounting'),
            'essential_commands': ('⌨️', 'Core Linux commands and text processing'),
            'users_groups': ('👥', 'User and group management, permissions')
        }
        
        banner.print_section_header("SELECT CATEGORY")
        
        for idx, cat in enumerate(categories, 1):
            icon, desc = category_info.get(cat, ('📁', 'Practice scenarios'))
            label = cat.replace('_', ' ').title()
            banner.print_menu_item(idx, f"{icon} {label}", desc)
        
        print(f"\n  {dim('0. Back')}")
        print()
        
        while True:
            try:
                choice = input(f"{Colors.CYAN}❯ Enter category number:{Colors.RESET} ").strip()
                
                if choice == '0':
                    return None
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(categories):
                    return categories[choice_num - 1]
                else:
                    print(error(f"Invalid choice. Please enter a number between 1 and {len(categories)}."))
            except ValueError:
                print(error("Invalid input. Please enter a number."))
            except KeyboardInterrupt:
                print("\n")
                return None
    
    def _select_difficulty(self) -> Optional[str]:
        """
        Interactive difficulty selection
        
        Returns:
            Selected difficulty or None if cancelled
        """
        difficulties = self.config.difficulties if self.config else ['easy', 'medium', 'hard']
        
        difficulty_info = {
            'easy': ('🟢', 'Perfect for beginners', success('[EASY]')),
            'medium': ('🟡', 'Intermediate level challenges', warning('[MEDIUM]')),
            'hard': ('🔴', 'Advanced scenarios for experts', error('[HARD]'))
        }
        
        banner.print_section_header("SELECT DIFFICULTY")
        
        for idx, diff in enumerate(difficulties, 1):
            icon, desc, badge = difficulty_info.get(diff, ('⚪', 'Practice scenarios', dim(f'[{diff.upper()}]')))
            banner.print_menu_item(idx, f"{icon} {diff.capitalize()}", desc, badge)
        
        print(f"\n  {dim('0. Back')}")
        print()
        
        while True:
            try:
                choice = input(f"{Colors.CYAN}❯ Enter difficulty number:{Colors.RESET} ").strip()
                
                if choice == '0':
                    return None
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(difficulties):
                    return difficulties[choice_num - 1]
                else:
                    print(error(f"Invalid choice. Please enter a number between 1 and {len(difficulties)}."))
            except ValueError:
                print(error("Invalid input. Please enter a number."))
            except KeyboardInterrupt:
                print("\n")
                return None
    
    def cmd_update(self, check_only: bool = False) -> int:
        """
        Check for and install updates
        
        Args:
            check_only: If True, only check for updates without installing
        
        Returns:
            Exit code (0 for success)
        """
        from ..utils.version_check import (
            check_for_updates,
            get_current_version, 
            print_update_notification,
            perform_update
        )
        
        current_version = get_current_version()
        banner.print_mini_banner()
        
        print(f"\n{info('Current version:')} {highlight(current_version)}")
        print(f"{info('Checking for updates...')}\n")
        
        try:
            latest_version = check_for_updates(force=True)
            
            if latest_version:
                print_update_notification(latest_version)
                
                if check_only:
                    return 0
                
                # Ask user if they want to update
                response = input(f"{Colors.CYAN}Do you want to update now? (y/n):{Colors.RESET} ").strip().lower()
                
                if response == 'y':
                    return perform_update()
                else:
                    print(f"\n{info('Update cancelled.')}\n")
                    return 0
            else:
                print(f"{success('✓ You are running the latest version!')}\n")
                return 0
                
        except Exception as e:
            logger.error(f"Update check failed: {e}", exc_info=True)
            print(f"{error('Update check failed.')} {dim('Please try again later.')}\n")
            return 1
    
    def cmd_reset(self, confirm: bool = False) -> int:
        """
        Reset user progress
        
        Args:
            confirm: Whether user confirmed the reset
        
        Returns:
            Exit code (0 for success)
        """
        # Check if engine is available
        if self.engine is None:
            print("\nError: Engine not initialized. Cannot reset progress.")
            print("Please ensure Docker is installed and running.\n")
            return 1
        
        if not confirm:
            print("Error: Reset requires --confirm flag")
            print("This will delete all your progress and statistics!")
            print("\nTo confirm, run: lfcs reset --confirm")
            return 1
        
        try:
            # Double-check with user
            print("\n" + "!" * 70)
            print("WARNING: This will permanently delete all your progress!")
            print("!" * 70)
            response = input("\nType 'DELETE' to confirm: ")
            
            if response != 'DELETE':
                print("Reset cancelled.")
                return 0
            
            # Perform reset
            self.engine.scorer.reset_progress()
            
            print("\n✓ All progress has been reset.")
            print("You can start fresh with 'lfcs start'\n")
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to reset progress: {e}", exc_info=True)
            print(f"Error: Could not reset progress - {e}")
            return 1
    
    def _display_session_result(self, result: SessionResult) -> None:
        """Display the results of a practice session"""
        banner.print_section_header("SESSION RESULTS")
        
        # Status with big visual indicator
        if result.passed:
            print(f"\n  {success('✓ PASSED')} {success('🎉')}\n")
        else:
            print(f"\n  {error('✗ FAILED')} {error('❌')}\n")
        
        # Summary info
        summary = [
            f"{highlight('Score:')} {success(str(result.score))} / {info(str(result.scenario.points))}",
            f"{highlight('Checks Passed:')} {success(str(result.validation_result.checks_passed))} / {info(str(result.validation_result.checks_total))}",
            f"{highlight('Duration:')} {info(str(result.duration))} seconds"
        ]
        
        banner.print_box("Summary", summary)
        
        # Detailed feedback
        if result.validation_result.check_results:
            print(f"{highlight('Detailed Results:')}\n")
            for check_result in result.validation_result.check_results:
                if check_result.passed:
                    print(f"  {success('✓')} {check_result.check_name}")
                else:
                    print(f"  {error('✗')} {check_result.check_name}")
                    if check_result.message:
                        print(f"    {dim(check_result.message)}")
            print()
        
        banner.print_divider()
    
    def _display_statistics(self, stats: Statistics, category: Optional[str]) -> None:
        """Display user statistics"""
        if category:
            banner.print_section_header(f"STATISTICS - {category.upper()}")
        else:
            banner.print_section_header("OVERALL STATISTICS")
        
        # Overall stats
        print(f"\n{highlight('Total Attempts:')} {info(str(stats.total_attempts))}")
        print(f"{highlight('Total Passed:')} {success(str(stats.total_passed))}")
        
        if stats.total_attempts > 0:
            pass_rate = (stats.total_passed / stats.total_attempts) * 100
            rate_color = success if pass_rate >= 70 else warning if pass_rate >= 50 else error
            print(f"{highlight('Pass Rate:')} {rate_color(f'{pass_rate:.1f}%')}")
            print(f"{highlight('Average Score:')} {info(f'{stats.average_score:.1f}')}")
        
        print(f"\n{highlight('Current Streak:')} {info(str(stats.current_streak))}")
        print(f"{highlight('Best Streak:')} {success(str(stats.best_streak))}")
        
        # Category breakdown with mastery percentages
        if stats.by_category:
            print(f"\n{highlight('Performance by Category and Difficulty:')}")
            print(Colors.DIM + "-" * 70 + Colors.RESET)
            
            for cat_name, cat_stats in sorted(stats.by_category.items()):
                if cat_stats.attempts > 0:
                    cat_pass_rate = (cat_stats.passed / cat_stats.attempts) * 100
                    rate_color = success if cat_pass_rate >= 70 else warning if cat_pass_rate >= 50 else error
                    print(f"\n{info(cat_name.upper())}:")
                    print(f"  Overall: {cat_stats.attempts} attempts | {cat_stats.passed} passed | {rate_color(f'{cat_pass_rate:.1f}%')} pass rate")
                    
                    # Show mastery by difficulty
                    if cat_stats.by_difficulty:
                        print(f"  {dim('Mastery by Difficulty:')}")
                        for diff in ['easy', 'medium', 'hard']:
                            if diff in cat_stats.by_difficulty:
                                diff_stats = cat_stats.by_difficulty[diff]
                                mastery = self.engine.scorer._calculate_mastery_percentage(diff_stats)
                                
                                # Color-code mastery
                                if mastery >= 80:
                                    mastery_color = success
                                    mastery_icon = "★"
                                elif mastery >= 60:
                                    mastery_color = warning
                                    mastery_icon = "◐"
                                else:
                                    mastery_color = error
                                    mastery_icon = "○"
                                
                                diff_label = diff.capitalize().ljust(6)
                                print(f"    {mastery_icon} {diff_label}: {mastery_color(f'{mastery:.1f}%')} mastery "
                                      f"({diff_stats.attempts} attempts, {diff_stats.passed} passed)")
        
        # Recommendations
        recommendations = self.engine.get_recommendations()
        if recommendations:
            print(f"\n{highlight('Recommendations:')}")
            for rec in recommendations:
                print(f"  💡 {info(rec)}")
        
        # Achievements
        if stats.achievements:
            print(f"\n{highlight('Achievements:')}")
            for achievement in stats.achievements:
                print(f"  🏆 {success(achievement.name)} - {dim(achievement.description)}")
        
        banner.print_divider("=")
    
    def _display_scenario_list(self, scenarios: List, category: Optional[str],
                               difficulty: Optional[str]) -> None:
        """Display list of scenarios with full descriptions"""
        filters = []
        if category:
            filters.append(f"Category: {category.replace('_', ' ').title()}")
        if difficulty:
            filters.append(f"Difficulty: {difficulty.capitalize()}")
        
        if filters:
            banner.print_section_header(f"SCENARIOS - {' | '.join(filters)}")
        else:
            banner.print_section_header("ALL SCENARIOS")
        
        if not scenarios:
            print(f"\n{warning('No scenarios found matching your criteria.')}")
            print(dim("Try adjusting your filters.\n"))
            return
        
        print(f"\n{highlight('Found')} {info(str(len(scenarios)))} {highlight('scenario(s):')}\n")
        
        # Sort scenarios by ID for consistent ordering
        sorted_scenarios = sorted(scenarios, key=lambda s: s.id)
        
        # Display scenarios with full task descriptions
        for idx, scenario in enumerate(sorted_scenarios, 1):
            # Color-code difficulty badges
            if scenario.difficulty == 'easy':
                difficulty_badge = success('[EASY]')
            elif scenario.difficulty == 'medium':
                difficulty_badge = warning('[MEDIUM]')
            elif scenario.difficulty == 'hard':
                difficulty_badge = error('[HARD]')
            else:
                difficulty_badge = dim(f'[{scenario.difficulty.upper()}]')
            
            # Display scenario number and ID
            print(f"{info(f'{idx}.')} {difficulty_badge} {highlight(scenario.id)}")
            
            # Display full task description with proper wrapping
            task_lines = self._wrap_text(scenario.task, width=66, indent=4)
            for line in task_lines:
                print(line)
            
            # Display points
            print(f"    {dim('Points:')} {info(str(scenario.points))}")
            
            # Add spacing between scenarios
            if idx < len(sorted_scenarios):
                print()
        
        banner.print_divider("=")
    
    def _select_scenario(self, scenarios: List, category: str, difficulty: str):
        """
        Interactive scenario selection from a list
        
        Args:
            scenarios: List of scenarios to choose from
            category: Category name for display
            difficulty: Difficulty level for display
        
        Returns:
            Selected scenario or None if cancelled
        """
        banner.print_section_header(f"SELECT SCENARIO - {category.replace('_', ' ').title()} | {difficulty.capitalize()}")
        
        # Sort scenarios by ID
        sorted_scenarios = sorted(scenarios, key=lambda s: s.id)
        
        # Display scenarios with numbers
        for idx, scenario in enumerate(sorted_scenarios, 1):
            # Color-code difficulty badges
            if scenario.difficulty == 'easy':
                difficulty_badge = success('[EASY]')
            elif scenario.difficulty == 'medium':
                difficulty_badge = warning('[MEDIUM]')
            elif scenario.difficulty == 'hard':
                difficulty_badge = error('[HARD]')
            else:
                difficulty_badge = dim(f'[{scenario.difficulty.upper()}]')
            
            print(f"  {info(str(idx))}. {difficulty_badge} {highlight(scenario.id)}")
            
            # Display task description (wrapped)
            task_lines = self._wrap_text(scenario.task, width=66, indent=6)
            for line in task_lines:
                print(line)
            
            print(f"      {dim('Points:')} {info(str(scenario.points))}")
            print()
        
        print(f"  {dim('0. Back')}")
        print()
        
        while True:
            try:
                choice = input(f"{Colors.CYAN}Enter scenario number:{Colors.RESET} ").strip()
                
                if choice == '0':
                    return None
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(sorted_scenarios):
                    return sorted_scenarios[choice_num - 1]
                else:
                    print(error(f"Invalid choice. Please enter a number between 1 and {len(sorted_scenarios)}."))
            except ValueError:
                print(error("Invalid input. Please enter a number."))
            except KeyboardInterrupt:
                print("\n")
                return None
    
    def _start_local_session(self, category: Optional[str], difficulty: Optional[str], ai_mode: bool) -> int:
        """
        Start a practice session on the local system without Docker
        
        Args:
            category: Optional category filter
            difficulty: Optional difficulty filter
            ai_mode: Whether to enable AI features
        
        Returns:
            Exit code (0 for success)
        """
        print("\n" + Colors.YELLOW + "!" * 70 + Colors.RESET)
        print(warning("⚠ LOCAL MODE WARNING"))
        print(Colors.YELLOW + "!" * 70 + Colors.RESET)
        print(f"\n{warning('You are about to practice on your LOCAL SYSTEM.')}")
        print(f"{warning('This will MODIFY files and settings on your actual machine!')}\n")
        print(f"{dim('Recommended: Use Docker mode for safe, isolated practice.')}")
        print(f"{dim('Only use local mode if you understand the risks.')}\n")
        
        response = input(f"{Colors.CYAN}Type 'YES' to continue with local mode:{Colors.RESET} ").strip()
        
        if response != 'YES':
            print(f"\n{info('Cancelled. Use')} {highlight('lfcs start')} {info('for Docker mode.')}\n")
            return 0
        
        # Interactive selection
        if category is None:
            category = self._select_category()
            if category is None:
                return 0
        
        if difficulty is None:
            difficulty = self._select_difficulty()
            if difficulty is None:
                return 0
        
        # Get scenarios
        scenarios = self.engine.scenario_loader.list_scenarios(category, difficulty)
        
        if not scenarios:
            print(f"\n{error('No scenarios found matching your criteria.')}")
            return 1
        
        # Select scenario
        selected_scenario = self._select_scenario(scenarios, category, difficulty)
        if selected_scenario is None:
            return 0
        
        # Display scenario
        banner.print_section_header(f"LOCAL MODE - SCENARIO: {selected_scenario.id}")
        
        print(f"\n{highlight('Category:')} {info(selected_scenario.category)}")
        print(f"{highlight('Difficulty:')} {info(selected_scenario.difficulty.capitalize())}")
        print(f"{highlight('Points:')} {info(str(selected_scenario.points))}")
        
        print(f"\n{highlight('TASK:')}")
        print(f"{selected_scenario.task}\n")
        
        if selected_scenario.hints:
            print(f"{highlight('HINTS:')}")
            for i, hint in enumerate(selected_scenario.hints, 1):
                print(f"  {dim(f'{i}.')} {hint}")
            print()
        
        if selected_scenario.time_limit:
            print(f"{highlight('TIME LIMIT:')} {warning(f'{selected_scenario.time_limit} seconds')}\n")
        
        banner.print_divider("=")
        print(f"\n{warning('⚠ Working on YOUR LOCAL SYSTEM')}")
        print(f"{dim('Complete the task above on your actual machine.')}\n")
        
        input(f"{Colors.CYAN}Press Enter when ready to validate...{Colors.RESET}")
        
        # Validation (local mode - run checks on host)
        print(f"\n{info('Running validation on local system...')}\n")
        
        # Note: Validation in local mode would need special handling
        # For now, show a message
        print(f"{warning('⚠ Local mode validation not fully implemented yet.')}")
        print(f"{dim('You can manually verify your work against the task requirements.')}\n")
        
        return 0
    
    def _print_help(self) -> None:
        """Display styled help message"""
        banner.print_mini_banner()
        
        # Usage
        print(f"\n{highlight('Usage:')} {info('lfcs')} {dim('[options]')} {info('<command>')} {dim('[command-options]')}")
        
        # Commands section
        banner.print_subheader("Available Commands")
        
        commands = [
            ("start", "🚀", "Start a new practice session", 
             "Begin practicing with interactive scenario selection"),
            ("list", "📋", "List available scenarios", 
             "Browse all scenarios with category and difficulty filters"),
            ("stats", "📊", "View your statistics", 
             "See your progress, performance, and achievements"),
            ("learn", "📚", "Interactive learning mode", 
             "Learn Linux from basics to LFCS level with guided lessons"),
            ("update", "📦", "Update to latest version",
             "Check for and install the latest version from PyPI"),
            ("reset", "🔄", "Reset your progress", 
             "Clear all statistics and start fresh (requires confirmation)")
        ]
        
        for cmd, icon, short_desc, long_desc in commands:
            print(f"  {icon} {info(cmd.ljust(8))} {highlight(short_desc)}")
            print(f"     {dim(long_desc)}\n")
        
        # Options section
        banner.print_subheader("Global Options")
        print(f"  {info('-h, --help')}     Show this help message and exit")
        print(f"  {info('--version')}      Show version number and exit")
        
        # Examples section
        banner.print_subheader("Examples")
        
        examples = [
            ("Interactive mode", "lfcs start", 
             "Select category, difficulty, and scenario interactively"),
            ("Filtered start", "lfcs start --category networking --difficulty easy", 
             "Start with pre-selected filters"),
            ("Browse scenarios", "lfcs list", 
             "Interactively browse all available scenarios"),
            ("View progress", "lfcs stats", 
             "See your overall statistics and achievements"),
            ("Category stats", "lfcs stats --category essential_commands", 
             "View statistics for a specific category"),
            ("Learning mode", "lfcs learn", 
             "Start interactive learning from basics"),
            ("Local practice", "lfcs start --local", 
             "Practice on your system without Docker (⚠️  not recommended)")
        ]
        
        for title, cmd, desc in examples:
            print(f"  {dim('•')} {highlight(title)}")
            print(f"    {dim('$')} {info(cmd)}")
            print(f"    {dim(desc)}\n")
        
        # Command-specific help
        banner.print_divider()
        print(f"\n{dim('For command-specific help, use:')} {info('lfcs <command> --help')}")
        print(f"{dim('Example:')} {info('lfcs start --help')}\n")
        
        # Footer
        notes = [
            "Docker is required for safe, isolated practice environments",
            "All progress is automatically saved to your local database",
            "Press Ctrl+C at any time to exit safely"
        ]
        banner.print_important_notes(notes)
    
    def _wrap_text(self, text: str, width: int = 70, indent: int = 0) -> List[str]:
        """
        Wrap text to specified width with indentation
        
        Args:
            text: Text to wrap
            width: Maximum line width
            indent: Number of spaces to indent
        
        Returns:
            List of wrapped lines
        """
        import textwrap
        
        indent_str = ' ' * indent
        wrapped = textwrap.fill(
            text,
            width=width,
            initial_indent=indent_str,
            subsequent_indent=indent_str,
            break_long_words=False,
            break_on_hyphens=False
        )
        return wrapped.split('\n')



    
    def cmd_learn(self, list_modules: bool = False, module_id: Optional[str] = None,
                  continue_learning: bool = False) -> int:
        """
        Start interactive learning mode
        
        Args:
            list_modules: List all available modules
            module_id: Start specific module by ID
            continue_learning: Continue from last lesson
        
        Returns:
            Exit code (0 for success)
        """
        # Load modules
        loader = ModuleLoader()
        loader.load_all()
        
        # List modules if requested
        if list_modules:
            return self._list_learning_modules(loader)
        
        # TODO: Implement continue from last lesson
        if continue_learning:
            print(warning("Continue feature not yet implemented. Starting fresh..."))
        
        # Start specific module or show selection
        if module_id:
            module = loader.get_module(module_id)
            if not module:
                print(f"{error('Module not found:')} {module_id}")
                return 1
            return self._start_learning_module(module)
        else:
            return self._select_and_start_module(loader)
    
    def _list_learning_modules(self, loader: ModuleLoader) -> int:
        """List all available learning modules"""
        print(f"\\n{header('AVAILABLE LEARNING MODULES')}\\n")
        
        for level in DifficultyLevel:
            modules = loader.get_modules_by_level(level)
            if not modules:
                continue
                
            level_name = level.value.replace('_', ' ').title()
            icon = {'beginner': '🌱', 'intermediate': '📚', 'advanced': '🚀', 
                   'expert': '💎', 'lfcs_prep': '🎓'}.get(level.value, '📖')
            
            print(f"{icon} {highlight(level_name)} ({len(modules)} modules)")
            banner.print_divider("-")
            
            for module in modules:
                print(f"  {info(module.id)}")
                print(f"    {dim(module.title)}")
                print(f"    {dim(f'⏱ {module.estimated_time} min | {len(module.lessons)} lessons')}\\n")
        
        return 0
    
    def _select_and_start_module(self, loader: ModuleLoader) -> int:
        """Interactive module selection"""
        banner.print_section_header("LFCS LEARN MODE - Choose Your Path")
        
        # Show levels
        levels = [
            (DifficultyLevel.BEGINNER, '🌱', 'Start here if new to Linux'),
            (DifficultyLevel.INTERMEDIATE, '📚', 'Text processing, processes, packages'),
            (DifficultyLevel.ADVANCED, '🚀', 'Networking, storage, users'),
            (DifficultyLevel.EXPERT, '💎', 'Security, automation, troubleshooting'),
        ]
        
        for idx, (level, icon, desc) in enumerate(levels, 1):
            modules = loader.get_modules_by_level(level)
            count = len(modules)
            level_name = level.value.replace('_', ' ').title()
            
            if count > 0:
                print(f"  {info(f'{idx}.')} {icon} {highlight(level_name)} ({count} modules)")
                print(f"      {dim(desc)}")
            else:
                print(f"  {dim(f'{idx}. {icon} {level_name} (0 modules) - Coming soon')}")
            print()
        
        # Get user choice
        try:
            choice = input(f"{Colors.CYAN}Enter choice (1-{len(levels)}):{Colors.RESET} ").strip()
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(levels):
                selected_level = levels[choice_num - 1][0]
                modules = loader.get_modules_by_level(selected_level)
                
                if not modules:
                    print(f"\\n{warning('No modules available for this level yet.')}\\n")
                    return 0
                
                # Show modules for selected level
                return self._select_module_from_level(modules)
            else:
                print(error(f"Please enter a number between 1 and {len(levels)}"))
                return 1
        except (ValueError, KeyboardInterrupt):
            print("\\n")
            return 0
    
    def _select_module_from_level(self, modules: list) -> int:
        """Select specific module from a level"""
        banner.print_section_header(f"{modules[0].level.value.replace('_', ' ').title()} Modules")
        
        for idx, module in enumerate(modules, 1):
            print(f"  {info(f'{idx}.')} {highlight(module.title)}")
            print(f"      {dim(module.description)}")
            print(f"      {dim(f'⏱ {module.estimated_time} min | {len(module.lessons)} lessons | {module.get_total_exercises()} exercises')}\\n")
        
        try:
            choice = input(f"{Colors.CYAN}Enter module (1-{len(modules)}):{Colors.RESET} ").strip()
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(modules):
                selected_module = modules[choice_num - 1]
                return self._start_learning_module(selected_module)
            else:
                print(error(f"Please enter a number between 1 and {len(modules)}"))
                return 1
        except (ValueError, KeyboardInterrupt):
            print("\\n")
            return 0
    
    def _start_learning_module(self, module) -> int:
        """Start a learning module with Docker environment"""
        banner.print_section_header(f"MODULE: {module.title}")
        
        print(f"{dim(module.description)}\\n")
        print(f"  {info('Lessons:')} {len(module.lessons)}")
        print(f"  {info('Exercises:')} {module.get_total_exercises()}")
        print(f"  {info('Estimated Time:')} {module.estimated_time} minutes\\n")
        
        input(f"{Colors.CYAN}Press Enter to start...{Colors.RESET}")
        
        # Start Docker container for learning
        if not self.engine:
            print(f"\\n{error('Error:')} Engine not initialized.")
            return 1
            
        container = None
        try:
            # Create container
            print(f"\\n{info('Starting learning environment...')}\\n")
            
            # Create a minimal scenario object for learning mode
            from src.core.models import Scenario, ValidationRules
            
            dummy_scenario = Scenario(
                id=f"learn_{module.id}",
                category="learning",
                difficulty="beginner",
                task=module.description,  # Use description as task
                validation=ValidationRules(checks=[]),
                hints=[],
                points=0,
                time_limit=None,
                setup_commands=[]
            )
            
            container = self.engine.docker_manager.create_container(
                distribution='ubuntu',
                scenario=dummy_scenario
            )
            
            # Create Docker environment
            env = DockerEnvironment(container)
            
            # Create interactive shell
            shell = InteractiveShell(env)
            
            # Run each lesson
            total_completed = 0
            total_points = 0
            
            for lesson_idx, lesson in enumerate(module.lessons, 1):
                banner.print_section_header(f"Lesson {lesson_idx}/{len(module.lessons)}")
                
                completed, points = shell.run_lesson(lesson)
                total_completed += completed
                total_points += points
                
                # Ask to continue
                if lesson_idx < len(module.lessons):
                    try:
                        cont = input(f"\\n{Colors.CYAN}Continue to next lesson? (y/n):{Colors.RESET} ").strip().lower()
                        if cont != 'y':
                            break
                    except KeyboardInterrupt:
                        print("\\n")
                        break
            
            # Show results
            banner.print_section_header("MODULE COMPLETE!")
            
            print(f"  {success('Exercises Completed:')} {total_completed}/{module.get_total_exercises()}")
            print(f"  {success('Points Earned:')} {total_points}/{module.get_total_points()}\\n")
            
            # TODO: Save progress to database
            
            return 0
            
        except Exception as e:
            logger.error(f"Learning session failed: {e}", exc_info=True)
            print(f"\\n{error('Error:')} {e}\\n")
            return 1
            
        finally:
            # Ensure container is cleaned up
            if container:
                print(f"\\n{info('Cleaning up environment...')}")
                try:
                    self.engine.docker_manager.destroy_container(container)
                except Exception as e:
                    logger.error(f"Error cleaning up container: {e}")
