#!/bin/bash
# Build script for LFCS Practice Tool package

set -e

echo "🔨 Building LFCS Practice Tool Package"
echo "======================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "setup.py" ]; then
    echo -e "${RED}Error: setup.py not found. Run this script from the project root.${NC}"
    exit 1
fi

# Clean previous builds
echo -e "\n${YELLOW}Cleaning previous builds...${NC}"
rm -rf build/ dist/ *.egg-info src/*.egg-info

# Check Python version
echo -e "\n${YELLOW}Checking Python version...${NC}"
python_version=$(python3 --version | cut -d' ' -f2)
echo "Python version: $python_version"

required_version="3.9"
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo -e "${RED}Error: Python 3.9 or higher is required${NC}"
    exit 1
fi

# Install build dependencies
echo -e "\n${YELLOW}Installing build dependencies...${NC}"
pip install --upgrade pip setuptools wheel build twine

# Check code style
echo -e "\n${YELLOW}Checking code style...${NC}"
if command -v black &> /dev/null; then
    black --check src/ tests/ || echo -e "${YELLOW}Warning: Code style issues found. Run 'black src/ tests/' to fix.${NC}"
fi

if command -v flake8 &> /dev/null; then
    flake8 src/ tests/ --max-line-length=100 || echo -e "${YELLOW}Warning: Linting issues found.${NC}"
fi

# Build source distribution
echo -e "\n${YELLOW}Building source distribution...${NC}"
python3 -m build --sdist

# Build wheel distribution
echo -e "\n${YELLOW}Building wheel distribution...${NC}"
python3 -m build --wheel

# Check the distribution
echo -e "\n${YELLOW}Checking distribution...${NC}"
twine check dist/*

# List built packages
echo -e "\n${GREEN}✓ Package built successfully!${NC}"
echo -e "\nBuilt packages:"
ls -lh dist/

# Instructions
echo -e "\n${GREEN}======================================"
echo "Package build complete!"
echo "======================================${NC}"
echo ""
echo "To install locally:"
echo "  pip install dist/lfcs_practice_tool-*.whl"
echo ""
echo "To upload to TestPyPI:"
echo "  twine upload --repository testpypi dist/*"
echo ""
echo "To upload to PyPI:"
echo "  twine upload dist/*"
echo ""
echo "To test the package:"
echo "  pip install dist/lfcs_practice_tool-*.whl"
echo "  lfcs-practice --help"
