"""
ASCII Art Banner and UI Components for LFCS Practice Tool
Provides visually appealing banners and UI elements
"""

from .colors import Colors, dim, info, highlight, success, warning, error


# ASCII Art Banner
BANNER = f"""{Colors.BRIGHT_CYAN}
========================================================================
                                                                       
   ██╗     ███████╗ ██████╗███████╗                                   
   ██║     ██╔════╝██╔════╝██╔════╝                                   
   ██║     █████╗  ██║     ███████╗                                   
   ██║     ██╔══╝  ██║     ╚════██║                                   
   ███████╗██║     ╚██████╗███████║                                   
   ╚══════╝╚═╝      ╚═════╝╚══════╝                                   
                                                                       
        {Colors.BRIGHT_YELLOW}Linux System Administration Practice Tool{Colors.BRIGHT_CYAN}                
                                                                       
========================================================================
{Colors.RESET}"""

MINI_BANNER = f"""{Colors.BRIGHT_CYAN}
========================================================================
  {Colors.BOLD}LFCS Practice Tool{Colors.RESET}{Colors.BRIGHT_CYAN}  |  Linux System Administration Training      
========================================================================
{Colors.RESET}"""


def print_banner():
    """Print the main ASCII art banner"""
    print(BANNER)


def print_mini_banner():
    """Print a compact banner for subsequent screens"""
    print(MINI_BANNER)


def print_box(title: str, content: list, width: int = 70):
    """
    Print a boxed section with title and content (using simple underline)
    
    Args:
        title: Box title
        content: List of content lines
        width: Box width (default 70)
    """
    print(f"\n{Colors.BOLD}{Colors.WHITE}{title}{Colors.RESET}")
    print(f"{Colors.CYAN}{'-' * len(title)}{Colors.RESET}")
    
    # Content
    for line in content:
        print(f"  {line}")
    
    print()


def print_section_header(title: str, width: int = 70):
    """Print a major section header with decorative borders (top and bottom)"""
    print(f"\n{Colors.CYAN}{'=' * width}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{title.center(width)}{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * width}{Colors.RESET}\n")


def print_subheader(title: str):
    """Print a subheader with just an underline below"""
    print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{title}{Colors.RESET}")
    print(f"{Colors.CYAN}{'-' * len(title)}{Colors.RESET}\n")


def print_menu_item(number: int, label: str, description: str = None, badge: str = None):
    """
    Print a formatted menu item
    
    Args:
        number: Menu item number
        label: Main label
        description: Optional description
        badge: Optional badge (e.g., difficulty level)
    """
    num_str = f"{Colors.BRIGHT_CYAN}{number}.{Colors.RESET}"
    
    if badge:
        label_str = f"{badge} {highlight(label)}"
    else:
        label_str = highlight(label)
    
    if description:
        print(f"  {num_str} {label_str}")
        print(f"     {dim(description)}")
    else:
        print(f"  {num_str} {label_str}")


def print_info_table(data: dict, title: str = None):
    """
    Print information in a table format
    
    Args:
        data: Dictionary of key-value pairs
        title: Optional table title
    """
    if title:
        print_section_header(title)
    
    # Find longest key for alignment
    max_key_len = max(len(str(k)) for k in data.keys()) if data else 0
    
    for key, value in data.items():
        key_str = f"{highlight(str(key) + ':')}"
        padding = max_key_len - len(str(key))
        print(f"  {key_str}{' ' * padding} {info(str(value))}")


def print_progress_bar(current: int, total: int, width: int = 50, label: str = "Progress"):
    """
    Print a progress bar
    
    Args:
        current: Current progress value
        total: Total/max value
        width: Width of the progress bar
        label: Label for the progress bar
    """
    if total == 0:
        percentage = 0
    else:
        percentage = (current / total) * 100
    
    filled = int(width * current / total) if total > 0 else 0
    bar = '█' * filled + '░' * (width - filled)
    
    # Color based on percentage
    if percentage >= 80:
        color = Colors.BRIGHT_GREEN
    elif percentage >= 60:
        color = Colors.BRIGHT_YELLOW
    else:
        color = Colors.BRIGHT_RED
    
    print(f"{highlight(label + ':')} {color}{bar}{Colors.RESET} {percentage:.1f}% ({current}/{total})")


def print_divider(char: str = "-", width: int = 70):
    """Print a divider line"""
    print(f"{Colors.DIM}{char * width}{Colors.RESET}")


def print_important_notes(notes: list):
    """
    Print important notes with simple underline
    
    Args:
        notes: List of note strings
    """
    title = "Important Notes"
    print(f"\n{Colors.BOLD}{Colors.BRIGHT_YELLOW}{title}{Colors.RESET}")
    print(f"{Colors.YELLOW}{'-' * len(title)}{Colors.RESET}")
    
    for note in notes:
        print(f"  {Colors.BRIGHT_YELLOW}•{Colors.RESET} {note}")
    
    print()


def print_ascii_banner():
    """Print just the ASCII art without borders"""
    print(f"{Colors.BRIGHT_CYAN}   ██╗     ███████╗ ██████╗███████╗{Colors.RESET}")
    print(f"{Colors.BRIGHT_CYAN}   ██║     ██╔════╝██╔════╝██╔════╝{Colors.RESET}")
    print(f"{Colors.BRIGHT_CYAN}   ██║     █████╗  ██║     ███████╗{Colors.RESET}")
    print(f"{Colors.BRIGHT_CYAN}   ██║     ██╔══╝  ██║     ╚════██║{Colors.RESET}")
    print(f"{Colors.BRIGHT_CYAN}   ███████╗██║     ╚██████╗███████║{Colors.RESET}")
    print(f"{Colors.BRIGHT_CYAN}   ╚══════╝╚═╝      ╚═════╝╚══════╝{Colors.RESET}")


def print_center(text: str, width: int = 70):
    """Print centered text"""
    print(f"{Colors.BRIGHT_YELLOW}{text.center(width)}{Colors.RESET}")


def print_section(title: str):
    """Print a section header with underline"""
    print(f"\n{Colors.BOLD}{Colors.WHITE}{title}{Colors.RESET}")
    print(f"{Colors.CYAN}{'-' * len(title)}{Colors.RESET}")


def print_info(lines: list):
    """Print info lines"""
    for line in lines:
        print(f"  {line}")


def print_welcome_screen(version: str):
    """Display welcome screen with ASCII art banner"""
    from .colors import success, warning, dim, info, highlight
    
    # Check for updates
    update_available = None
    try:
        from .version_check import check_for_updates, get_update_command
        update_available = check_for_updates()
    except:
        pass
    
    print()
    print(f"{Colors.CYAN}{'=' * 70}{Colors.RESET}")
    print()
    print_ascii_banner()
    print_center("Linux System Administration Practice Tool")
    print()
    print(f"{Colors.CYAN}{'=' * 70}{Colors.RESET}")
    print()
    
    # Show version with update warning if available
    if update_available:
        print(f"{Colors.YELLOW}╭{'─' * 68}╮{Colors.RESET}")
        print(f"{Colors.YELLOW}│{Colors.RESET} {warning('⚠️  UPDATE AVAILABLE!')} " + " " * 45 + f"{Colors.YELLOW}│{Colors.RESET}")
        print(f"{Colors.YELLOW}│{Colors.RESET}" + " " * 70 + f"{Colors.YELLOW}│{Colors.RESET}")
        print(f"{Colors.YELLOW}│{Colors.RESET}  You are on version {dim(version)}, but {highlight(update_available)} is available!" + " " * (24 - len(version) - len(update_available)) + f"{Colors.YELLOW}│{Colors.RESET}")
        print(f"{Colors.YELLOW}│{Colors.RESET}  {warning('Missing latest features and bug fixes!')} " + " " * 24 + f"{Colors.YELLOW}│{Colors.RESET}")
        print(f"{Colors.YELLOW}│{Colors.RESET}" + " " * 70 + f"{Colors.YELLOW}│{Colors.RESET}")
        
        update_cmd = get_update_command() if update_available else "pip install --upgrade lfcs"
        print(f"{Colors.YELLOW}│{Colors.RESET}  Update now: {success(update_cmd)}" + " " * (56 - len(update_cmd)) + f"{Colors.YELLOW}│{Colors.RESET}")
        print(f"{Colors.YELLOW}╰{'─' * 68}╯{Colors.RESET}")
        print()
    
    print_section("System Information")
    
    # Show version status
    if update_available:
        version_status = f"{version} {warning('(Outdated!)')}"
    else:
        version_status = f"{version} {success('(Latest)')}"
    
    print_info([
        f"{highlight('Version:')} {version_status}",
        f"{highlight('Author:')} {info('C Sarath Babu')}",
        f"{highlight('License:')} {info('MIT')}"
    ])
    print()
    
    print_section("Important Notes")
    print_info([
        f"• Choose {success('start')} to begin a practice session",
        f"• Choose {info('list')} to browse available scenarios",
        f"• Choose {warning('stats')} to view your progress",
        f"• Choose {info('learn')} for interactive learning mode",
        f"• Use {highlight('--help')} for detailed command information"
    ])


def print_usage_help():
    """Print usage help in a styled format"""
    print_mini_banner()
    
    print(f"\n{highlight('Usage:')} {info('lfcs')} {dim('[options]')} {info('<command>')} {dim('[command-options]')}\n")
    
    print(f"{highlight('Available Commands:')}\n")
    
    commands = [
        ("start", "Start a new practice session", "Begin practicing with interactive scenario selection"),
        ("list", "List available scenarios", "Browse all scenarios with filters"),
        ("stats", "View your statistics", "See your progress and performance"),
        ("learn", "Interactive learning mode", "Learn Linux from basics to LFCS level"),
        ("reset", "Reset your progress", "Clear all statistics and start fresh")
    ]
    
    for cmd, short_desc, long_desc in commands:
        print(f"  {info(cmd.ljust(10))} {highlight(short_desc)}")
        print(f"  {' ' * 12} {dim(long_desc)}\n")
    
    print(f"\n{highlight('Examples:')}\n")
    examples = [
        ("lfcs start", "Interactive mode - select category, difficulty, and scenario"),
        ("lfcs start --category networking --difficulty easy", "Start with filters"),
        ("lfcs list", "Browse all available scenarios"),
        ("lfcs stats", "View your overall statistics"),
        ("lfcs learn", "Start interactive learning mode")
    ]
    
    for cmd, desc in examples:
        print(f"  {dim('$')} {info(cmd)}")
        print(f"     {dim(desc)}\n")
    
    print(f"{dim('For more information: lfcs <command> --help')}\n")
