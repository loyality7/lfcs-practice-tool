"""
Setup configuration for LFCS Practice Tool
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="lfcs",
    version="1.0.6",
    packages=find_packages(exclude=["tests", "tests.*", "docs", ".kiro"]),
    include_package_data=True,
    
    # Dependencies
    install_requires=[
        "pyyaml>=6.0",
        "docker>=6.0.0",
        "python-dotenv>=1.0.0",
        "tabulate>=0.9.0",
        "colorama>=0.4.6",
        "jinja2>=3.1.0",
    ],
    
    extras_require={
        "ai": [
            "openai>=1.0.0",
            "anthropic>=0.3.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "hypothesis>=6.0.0",
            "pytest-cov>=4.1.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "hypothesis>=6.0.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    
    # Entry points for CLI commands
    entry_points={
        "console_scripts": [
            "lfcs-practice=src.main:main",
            "lfcs=src.main:main",  # Shorter alias
        ],
    },
    
    # Package metadata
    author="LFCS Practice Team",
    author_email="",
    description="CLI-based LFCS Practice Environment with Docker containers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/loyality7/lfcs-practice-tool",
    project_urls={
        "Bug Reports": "https://github.com/loyality7/lfcs-practice-tool/issues",
        "Source": "https://github.com/loyality7/lfcs-practice-tool",
        "Documentation": "https://github.com/loyality7/lfcs-practice-tool/blob/main/README.md",
    },
    
    # Classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Education :: Testing",
        "Topic :: System :: Systems Administration",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Environment :: Console",
    ],
    
    keywords="lfcs linux certification practice docker training sysadmin",
    python_requires=">=3.9",
    
    # Package data
    package_data={
        "": [
            "*.yaml",
            "*.yml",
            "*.sql",
            "*.sh",
            "*.md",
        ],
        "src": [
            "data/scenarios/*.yaml",
            "data/scenarios/*/*.yaml",
            "data/scenarios/*/*/*.yaml",
            "data/learn_modules/*.yaml",
            "data/learn_modules/*/*.yaml",
            "data/schema.sql",
            "agent/lfcs-check",
            "data/docker/*",
            "data/docker/*/*",
        ],
    },
    
    # Zip safe
    zip_safe=False,
)
