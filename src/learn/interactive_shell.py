"""Interactive learning shell"""

import re
import logging
from typing import Optional, List
from ..core.interfaces import Environment, ExecutionResult
from ..utils.colors import Colors, success, error, warning, info, highlight, dim
from .models import Exercise, Lesson, ExerciseType

logger = logging.getLogger(__name__)

class InteractiveShell:
    """Interactive shell for learning exercises"""
    
    def __init__(self, environment: Environment):
        self.environment = environment
        self.hint_level = 0
        self.command_history: List[str] = []
        self.cwd = "/root"  # Default working directory
        
    def run_lesson(self, lesson: Lesson) -> tuple[int, int]:
        """
        Run a lesson interactively
        Returns: (exercises_completed, total_points_earned)
        """
        print(f"\n{Colors.CYAN}{'=' * 70}{Colors.RESET}")
        print(highlight(f"📖 {lesson.title}"))
        print(f"{Colors.CYAN}{'=' * 70}{Colors.RESET}\n")
        
        # Display notes
        print(lesson.notes)
        print()
        
        if not lesson.exercises:
            input(dim("Press Enter to continue..."))
            return (0, 0)
            
        # Run exercises
        completed = 0
        points_earned = 0
        
        for idx, exercise in enumerate(lesson.exercises, 1):
            print(f"\n{Colors.CYAN}{'─' * 70}{Colors.RESET}")
            print(info(f"Exercise {idx}/{len(lesson.exercises)}"))
            print(f"{Colors.CYAN}{'─' * 70}{Colors.RESET}\n")
            
            if self.run_exercise(exercise):
                completed += 1
                points_earned += exercise.points
                
        return (completed, points_earned)
    
    def run_exercise(self, exercise: Exercise) -> bool:
        """Run a single exercise, returns True if completed successfully"""
        print(f"{highlight('Task:')} {exercise.description}\n")
        
        if exercise.exercise_type == ExerciseType.COMMAND:
            return self._run_command_exercise(exercise)
        elif exercise.exercise_type == ExerciseType.QUESTION:
            return self._run_question_exercise(exercise)
        else:
            return self._run_task_exercise(exercise)
    
    def _run_command_exercise(self, exercise: Exercise) -> bool:
        """Run a command-based exercise"""
        self.hint_level = 0
        max_attempts = 3
        
        for attempt in range(max_attempts):
            # Show command prompt
            # Show current directory in prompt like a real shell
            prompt_dir = "~" if self.cwd == "/root" else self.cwd
            user_input = input(f"{Colors.GREEN}{prompt_dir} $ {Colors.RESET}").strip()
            
            if not user_input:
                continue
                
            # Handle special commands
            if user_input == 'hint':
                self._show_hint(exercise)
                continue
            elif user_input == 'skip':
                print(warning("Skipping exercise..."))
                return False
                
            # Execute command with state tracking
            self.command_history.append(user_input)
            result = self._execute_with_state(user_input)
            
            # Show output
            if result.output:
                print(result.output)
            if result.error:
                print(error(result.error))
                
            # Validate
            if self._validate_command(exercise, user_input, result):
                print(f"\n{success('✓ Correct!')} {dim(f'+{exercise.points} points')}\n")
                return True
            else:
                remaining = max_attempts - attempt - 1
                if remaining > 0:
                    print(f"{warning('✗ Not quite right.')} {dim(f'{remaining} attempts remaining')}")
                    print(dim("Type 'hint' for a hint, or 'skip' to skip this exercise.\n"))
                    
        print(f"\n{error('✗ Exercise failed.')} {dim('Moving to next exercise...')}\n")
        return False
    
    def _run_question_exercise(self, exercise: Exercise) -> bool:
        """Run a multiple-choice question exercise"""
        print(f"{exercise.question}\n")
        
        for idx, option in enumerate(exercise.options, 1):
            print(f"  {idx}. {option}")
            
        print()
        
        while True:
            try:
                choice = input(f"{Colors.CYAN}Your answer (1-{len(exercise.options)}):{Colors.RESET} ").strip()
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(exercise.options):
                    selected = exercise.options[choice_num - 1]
                    if selected == exercise.correct_answer:
                        print(f"\n{success('✓ Correct!')}\n")
                        return True
                    else:
                        print(f"\n{error('✗ Incorrect.')} {dim(f'The correct answer is: {exercise.correct_answer}')}\n")
                        return False
                else:
                    print(error(f"Please enter a number between 1 and {len(exercise.options)}"))
            except ValueError:
                print(error("Please enter a valid number"))
            except KeyboardInterrupt:
                print("\n")
                return False
    
    def _run_task_exercise(self, exercise: Exercise) -> bool:
        """Run a task-based exercise (free-form)"""
        print(dim("Complete the task described above, then press Enter when done.\n"))
        input()
        
        # Validate if validation rules provided
        if exercise.validation:
            result = self._validate_task(exercise)
            if result:
                print(f"\n{success('✓ Task completed!')}\n")
                return True
            else:
                print(f"\n{error('✗ Task validation failed.')}\n")
                return False
        else:
            # No validation, assume completed
            print(f"\n{success('✓ Task marked as complete!')}\n")
            return True
            
    def _execute_with_state(self, command: str) -> ExecutionResult:
        """Execute command maintaining current working directory state"""
        # Marker to separate command output from PWD
        marker = "___CWD___"
        
        # Construct command: cd <cwd> && <command>; echo marker; pwd
        # We use ; before echo to ensure PWD is printed even if command fails
        wrapped_cmd = f"cd {self.cwd} && {command}; echo '{marker}'; pwd"
        
        result = self.environment.execute_command(wrapped_cmd)
        
        # Parse output to extract new CWD and real output
        if result.output:
            parts = result.output.split(f"{marker}\n")
            if len(parts) >= 2:
                real_output = parts[0]
                new_cwd = parts[1].strip()
                
                # Update state
                if new_cwd:
                    self.cwd = new_cwd
                    
                # Update result
                result.output = real_output
                
        return result
    
    def _validate_command(self, exercise: Exercise, command: str, result: ExecutionResult) -> bool:
        """Validate command execution"""
        # Check exit code
        if result.exit_code != 0:
            return False
            
        # Check expected output
        if exercise.expected_output:
            norm_actual = ' '.join(result.output.strip().split())
            norm_expected = ' '.join(exercise.expected_output.strip().split())
            if norm_actual != norm_expected:
                return False
                
        # Check pattern match
        if exercise.expected_pattern:
            if not re.search(exercise.expected_pattern, result.output):
                return False
                
        # Check custom validation
        if exercise.validation:
            # TODO: Implement custom validation logic
            pass
            
        # If no specific validation is provided, check if the command matches the expected command
        # This prevents 'cd' from passing for 'ls' if no output/pattern/validation is specified
        if not exercise.expected_output and not exercise.expected_pattern and not exercise.validation:
            if exercise.command:
                # Simple check: does the command start with the expected command?
                # This allows arguments but prevents completely different commands
                expected_cmd = exercise.command.split()[0]
                actual_cmd = command.strip().split()[0]
                if actual_cmd != expected_cmd:
                    return False
            
        return True
    
    def _validate_task(self, exercise: Exercise) -> bool:
        """Validate task completion"""
        if not exercise.validation:
            return True
            
        # Execute validation command
        val_type = exercise.validation.get('type')
        if val_type == 'command':
            cmd = exercise.validation.get('command')
            # Run validation in current CWD context
            result = self._execute_with_state(cmd)
            return result.exit_code == 0
        elif val_type == 'file':
            path = exercise.validation.get('path')
            # Check file existence relative to CWD if relative path
            if not path.startswith('/'):
                path = f"{self.cwd}/{path}"
            return self.environment.file_exists(path)
            
        return True
    
    def _show_hint(self, exercise: Exercise):
        """Show progressive hints"""
        if not exercise.hints:
            print(dim("No hints available for this exercise."))
            return
            
        if self.hint_level >= len(exercise.hints):
            print(dim("No more hints available."))
            return
            
        print(f"\n{info('💡 Hint:')} {exercise.hints[self.hint_level]}\n")
        self.hint_level += 1
