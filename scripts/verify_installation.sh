#!/bin/bash
# Verification script for LFCS Practice Tool installation

set -e

echo "🔍 Verifying LFCS Practice Tool Installation"
echo "============================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

errors=0

# Check Python
echo -e "\n${YELLOW}Checking Python...${NC}"
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version)
    echo -e "${GREEN}✓${NC} $python_version"
else
    echo -e "${RED}✗ Python 3 not found${NC}"
    ((errors++))
fi

# Check pip
echo -e "\n${YELLOW}Checking pip...${NC}"
if command -v pip3 &> /dev/null; then
    pip_version=$(pip3 --version)
    echo -e "${GREEN}✓${NC} $pip_version"
else
    echo -e "${RED}✗ pip not found${NC}"
    ((errors++))
fi

# Check Docker
echo -e "\n${YELLOW}Checking Docker...${NC}"
if command -v docker &> /dev/null; then
    docker_version=$(docker --version)
    echo -e "${GREEN}✓${NC} $docker_version"
    
    # Check if Docker daemon is running
    if docker ps &> /dev/null; then
        echo -e "${GREEN}✓${NC} Docker daemon is running"
    else
        echo -e "${RED}✗ Docker daemon is not running${NC}"
        echo "  Start Docker with: sudo systemctl start docker (Linux) or Docker Desktop (Mac/Windows)"
        ((errors++))
    fi
else
    echo -e "${RED}✗ Docker not found${NC}"
    echo "  Install Docker from: https://docs.docker.com/get-docker/"
    ((errors++))
fi

# Check if package is installed
echo -e "\n${YELLOW}Checking LFCS Practice Tool installation...${NC}"
if command -v lfcs-practice &> /dev/null; then
    echo -e "${GREEN}✓${NC} lfcs-practice command found"
    
    # Try to run help
    if lfcs-practice --help &> /dev/null; then
        echo -e "${GREEN}✓${NC} lfcs-practice --help works"
    else
        echo -e "${RED}✗ lfcs-practice --help failed${NC}"
        ((errors++))
    fi
else
    echo -e "${RED}✗ lfcs-practice command not found${NC}"
    echo "  Install with: pip install lfcs-practice-tool"
    ((errors++))
fi

# Check Python package
echo -e "\n${YELLOW}Checking Python package...${NC}"
if python3 -c "import src" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Python package can be imported"
else
    echo -e "${YELLOW}⚠${NC} Python package import failed (may be OK if installed as package)"
fi

# Check required directories
echo -e "\n${YELLOW}Checking required directories...${NC}"
for dir in scenarios config database docker; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} $dir/ exists"
    else
        echo -e "${YELLOW}⚠${NC} $dir/ not found (may be OK if installed as package)"
    fi
done

# Check Docker images
echo -e "\n${YELLOW}Checking Docker images...${NC}"
if docker images | grep -q "lfcs-practice"; then
    echo -e "${GREEN}✓${NC} LFCS Practice Docker images found:"
    docker images | grep "lfcs-practice" | awk '{print "  - " $1 ":" $2}'
else
    echo -e "${YELLOW}⚠${NC} No LFCS Practice Docker images found"
    echo "  Build images with: cd docker/base_images && ./build_all.sh"
fi

# Check database
echo -e "\n${YELLOW}Checking database...${NC}"
if [ -f "database/progress.db" ]; then
    echo -e "${GREEN}✓${NC} Database file exists"
    db_size=$(du -h database/progress.db | cut -f1)
    echo "  Size: $db_size"
else
    echo -e "${YELLOW}⚠${NC} Database file not found (will be created on first run)"
fi

# Check logs directory
echo -e "\n${YELLOW}Checking logs directory...${NC}"
if [ -d "logs" ]; then
    echo -e "${GREEN}✓${NC} Logs directory exists"
    log_count=$(ls -1 logs/*.log 2>/dev/null | wc -l)
    if [ "$log_count" -gt 0 ]; then
        echo "  Found $log_count log file(s)"
    fi
else
    echo -e "${YELLOW}⚠${NC} Logs directory not found (will be created on first run)"
fi

# Summary
echo -e "\n============================================="
if [ $errors -eq 0 ]; then
    echo -e "${GREEN}✓ Installation verification complete!${NC}"
    echo -e "${GREEN}  All checks passed.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Build Docker images: cd docker/base_images && ./build_all.sh"
    echo "  2. Start practicing: lfcs-practice start"
    echo "  3. View help: lfcs-practice --help"
else
    echo -e "${RED}✗ Installation verification failed!${NC}"
    echo -e "${RED}  $errors error(s) found.${NC}"
    echo ""
    echo "Please fix the errors above and try again."
    exit 1
fi
