"""
Color utilities for CLI output
Provides ANSI color codes for terminal output
"""

import sys
import os


class Colors:
    """ANSI color codes for terminal output"""
    
    # Always enable colors by default (user can disable with NO_COLOR=1)
    ENABLED = os.environ.get('NO_COLOR') is None
    
    # Basic colors - always set them
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    
    # Reset
    RESET = '\033[0m'
    
    @classmethod
    def disable(cls):
        """Disable all colors"""
        cls.ENABLED = False
        for attr in dir(cls):
            if attr.isupper() and not attr.startswith('_'):
                setattr(cls, attr, '')
    
    @classmethod
    def enable(cls):
        """Enable colors (if terminal supports it)"""
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            cls.ENABLED = True
            # Re-initialize colors
            cls.__init__()


# Convenience functions for common use cases
def success(text: str) -> str:
    """Format text as success (green)"""
    return f"{Colors.BRIGHT_GREEN}{text}{Colors.RESET}"


def error(text: str) -> str:
    """Format text as error (red)"""
    return f"{Colors.BRIGHT_RED}{text}{Colors.RESET}"


def warning(text: str) -> str:
    """Format text as warning (yellow)"""
    return f"{Colors.BRIGHT_YELLOW}{text}{Colors.RESET}"


def info(text: str) -> str:
    """Format text as info (cyan)"""
    return f"{Colors.BRIGHT_CYAN}{text}{Colors.RESET}"


def highlight(text: str) -> str:
    """Format text as highlighted (bold white)"""
    return f"{Colors.BOLD}{Colors.WHITE}{text}{Colors.RESET}"


def dim(text: str) -> str:
    """Format text as dimmed (gray)"""
    return f"{Colors.DIM}{text}{Colors.RESET}"


def header(text: str) -> str:
    """Format text as header (bold cyan)"""
    return f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{text}{Colors.RESET}"


def command(text: str) -> str:
    """Format text as command (bright blue)"""
    return f"{Colors.BRIGHT_BLUE}{text}{Colors.RESET}"


def value(text: str) -> str:
    """Format text as value (magenta)"""
    return f"{Colors.BRIGHT_MAGENTA}{text}{Colors.RESET}"
