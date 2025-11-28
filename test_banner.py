#!/usr/bin/env python3
"""
Test script to preview the new banner and UI
"""

from src.utils import banner
from src.utils.colors import success, error, warning, info, highlight, dim

# Test 1: Welcome screen
print("\n" + "="*80)
print("TEST 1: Welcome Screen")
print("="*80)
banner.print_welcome_screen("1.0.0")

# Test 2: Section headers
print("\n" + "="*80)
print("TEST 2: Section Headers")
print("="*80)
banner.print_section_header("SELECT CATEGORY")

# Test 3: Menu items
print("\n" + "="*80)
print("TEST 3: Menu Items")
print("="*80)
banner.print_menu_item(1, "🌐 Networking", "Network configuration and troubleshooting")
banner.print_menu_item(2, "💾 Storage", "Disk management, filesystems, and mounting", success("[EASY]"))
banner.print_menu_item(3, "⚙️ Operations", "System operations and services", warning("[MEDIUM]"))

# Test 4: Info table
print("\n" + "="*80)
print("TEST 4: Info Table")
print("="*80)
data = {
    "Total Attempts": "42",
    "Passed": "35",
    "Pass Rate": "83.3%",
    "Current Streak": "5"
}
banner.print_info_table(data, "Your Statistics")

# Test 5: Progress bar
print("\n" + "="*80)
print("TEST 5: Progress Bars")
print("="*80)
banner.print_progress_bar(85, 100, label="Easy Mastery")
banner.print_progress_bar(60, 100, label="Medium Mastery")
banner.print_progress_bar(30, 100, label="Hard Mastery")

# Test 6: Box
print("\n" + "="*80)
print("TEST 6: Box")
print("="*80)
content = [
    f"{highlight('Category:')} {info('Networking')}",
    f"{highlight('Difficulty:')} {warning('[MEDIUM]')}",
    f"{highlight('Scenario:')} {info('static_ip_01')}",
    f"{highlight('Points:')} {success('10')}"
]
banner.print_box("Session Details", content)

# Test 7: Important notes
print("\n" + "="*80)
print("TEST 7: Important Notes")
print("="*80)
notes = [
    "Docker is required for safe, isolated practice environments",
    "Use --local flag to practice on your system (not recommended)",
    "All progress is saved automatically to your local database",
    "Press Ctrl+C at any time to exit safely"
]
banner.print_important_notes(notes)

# Test 8: Usage help
print("\n" + "="*80)
print("TEST 8: Usage Help")
print("="*80)
banner.print_usage_help()

print("\n" + "="*80)
print("All tests complete!")
print("="*80 + "\n")
