#!/usr/bin/env python3
"""
Verify LFCS Practice Tool project structure
"""

import os
import sys
from pathlib import Path

def check_directory_structure():
    """Verify all required directories exist"""
    required_dirs = [
        'src/cli',
        'src/core',
        'src/docker_manager',
        'src/validation',
        'src/utils',
        'src/ai',
        'tests/unit',
        'tests/integration',
        'tests/fixtures',
        'tests/scenarios',
        'config',
        'database',
        'docker/base_images/ubuntu',
        'docker/base_images/centos',
        'docker/base_images/rocky',
        'docker/validation_scripts',
        'scenarios/networking/easy',
        'scenarios/networking/medium',
        'scenarios/networking/hard',
        'scenarios/storage/easy',
        'scenarios/storage/medium',
        'scenarios/storage/hard',
        'scenarios/users_groups/easy',
        'scenarios/users_groups/medium',
        'scenarios/users_groups/hard',
        'scenarios/operations_deployment/easy',
        'scenarios/operations_deployment/medium',
        'scenarios/operations_deployment/hard',
        'scenarios/essential_commands/easy',
        'scenarios/essential_commands/medium',
        'scenarios/essential_commands/hard',
        'docs/architecture',
        'docs/developer_guide',
        'docs/user_guide',
        'logs',
        'scripts',
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not os.path.isdir(dir_path):
            missing_dirs.append(dir_path)
    
    return missing_dirs

def check_required_files():
    """Verify all required files exist"""
    required_files = [
        'src/__init__.py',
        'src/cli/__init__.py',
        'src/core/__init__.py',
        'src/docker_manager/__init__.py',
        'src/validation/__init__.py',
        'src/utils/__init__.py',
        'src/ai/__init__.py',
        'src/main.py',
        'tests/__init__.py',
        'tests/unit/__init__.py',
        'tests/integration/__init__.py',
        'tests/fixtures/__init__.py',
        'tests/scenarios/__init__.py',
        'requirements.txt',
        'setup.py',
        'pytest.ini',
        'MANIFEST.in',
        'README.md',
        'config/config.yaml',
        'database/schema.sql',
        '.gitignore',
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.isfile(file_path):
            missing_files.append(file_path)
    
    return missing_files

def main():
    """Main verification function"""
    print("Verifying LFCS Practice Tool project structure...")
    print("=" * 60)
    
    # Check directories
    missing_dirs = check_directory_structure()
    if missing_dirs:
        print("\n❌ Missing directories:")
        for dir_path in missing_dirs:
            print(f"  - {dir_path}")
    else:
        print("\n✅ All required directories present")
    
    # Check files
    missing_files = check_required_files()
    if missing_files:
        print("\n❌ Missing files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
    else:
        print("\n✅ All required files present")
    
    # Summary
    print("\n" + "=" * 60)
    if missing_dirs or missing_files:
        print("❌ Project structure verification FAILED")
        return 1
    else:
        print("✅ Project structure verification PASSED")
        return 0

if __name__ == "__main__":
    sys.exit(main())
