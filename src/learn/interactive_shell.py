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
        time_limit = getattr(exercise, 'time_limit', None) or 300  # Default 5 minutes
        
        import time
        import threading
        import sys
        
        start_time = time.time()
        timer_running = [True]
        
        def display_timer():
            """Display live countdown timer"""
            while timer_running[0]:
                elapsed = int(time.time() - start_time)
                remaining = max(0, time_limit - elapsed)
                
                mins = remaining // 60
                secs = remaining % 60
                
                # Color code based on time remaining
                if remaining > 120:  # > 2 minutes
                    timer_color = Colors.GREEN
                elif remaining > 60:  # > 1 minute
                    timer_color = Colors.YELLOW
                else:  # < 1 minute
                    timer_color = Colors.RED
                
                # Save cursor, move to top, print timer, restore cursor
                timer_str = f"{timer_color}⏱️  Time Remaining: {mins:02d}:{secs:02d}{Colors.RESET}"
                box_width = 50
                padding = box_width - 22  # Length of "⏱️  Time Remaining: MM:SS"
                
                # ANSI codes: save cursor, move to line 1, print, restore cursor
                sys.stdout.write(f"\033[s")  # Save cursor position
                sys.stdout.write(f"\033[1;1H")  # Move to line 1, column 1
                sys.stdout.write(f"{Colors.CYAN}┌{'─' * box_width}┐{Colors.RESET}\n")
                sys.stdout.write(f"{Colors.CYAN}│{Colors.RESET} {timer_str}{' ' * padding} {Colors.CYAN}│{Colors.RESET}\n")
                sys.stdout.write(f"{Colors.CYAN}└{'─' * box_width}┘{Colors.RESET}")
                sys.stdout.write(f"\033[u")  # Restore cursor position
                sys.stdout.flush()
                
                if remaining == 0:
                    timer_running[0] = False
                    break
                    
                time.sleep(1)
        
        # Start timer thread
        timer_thread = threading.Thread(target=display_timer, daemon=True)
        timer_thread.start()
        
        # Reserve space for timer at top
        print("\n\n\n")  # 3 lines for timer box
        
        try:
            for attempt in range(max_attempts):
                # Check if time expired
                if not timer_running[0]:
                    print(f"\n{error('⏰ Time expired!')} {dim('Moving to next exercise...')}\n")
                    return False
                
                # Show command prompt
                prompt_dir = "~" if self.cwd == "/root" else self.cwd.replace("/root", "~")
                user_input = input(f"{Colors.GREEN}student@lfcs{Colors.RESET}:{Colors.BLUE}{prompt_dir}{Colors.RESET}$ ").strip()
                
                if not user_input:
                    continue
                    
                # Handle special commands
                if user_input == 'hint':
                    self._show_hint(exercise)
                    continue
                elif user_input == 'skip':
                    timer_running[0] = False
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
                    timer_running[0] = False
                    print(f"{success('✓ Correct!')} {dim(f'+{exercise.points} points')}\n")
                    return True
                else:
                    remaining_attempts = max_attempts - attempt - 1
                    if remaining_attempts > 0:
                        print(f"{warning('✗ Not quite right.')} {dim(f'{remaining_attempts} attempts remaining')}")
                        print(dim("Type 'hint' for a hint, or 'skip' to skip this exercise.\n"))
            
            timer_running[0] = False
            print(f"{error('✗ Exercise failed.')} {dim('Moving to next exercise...')}\n")
            return False
            
        finally:
            timer_running[0] = False
            timer_thread.join(timeout=1)
    
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
            return self._validate_task(exercise)
            
        # If no specific validation is provided, check if the command matches the expected command
        # This prevents 'cd' from passing for 'ls' if no output/pattern/validation is specified
        if not exercise.expected_output and not exercise.expected_pattern:
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
