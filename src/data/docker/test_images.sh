#!/bin/bash
# Test LFCS practice base images

set -e

echo "=========================================="
echo "Testing LFCS Practice Base Images"
echo "=========================================="
echo

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

test_image() {
    local image=$1
    local distro=$2
    
    echo "Testing $distro image: $image"
    echo "----------------------------------------"
    
    # Test 1: Image exists
    if docker image inspect "$image" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Image exists"
    else
        echo -e "${RED}✗${NC} Image not found"
        return 1
    fi
    
    # Test 2: Essential commands available
    echo -n "Testing essential commands... "
    if docker run --rm "$image" /bin/bash -c "
        which sudo vim systemctl ip useradd groupadd > /dev/null 2>&1
    "; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
    
    # Test 3: Student user exists
    echo -n "Testing student user... "
    if docker run --rm "$image" /bin/bash -c "
        id student > /dev/null 2>&1
    "; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
    
    # Test 4: Sudo access works
    echo -n "Testing sudo access... "
    if docker run --rm "$image" /bin/bash -c "
        sudo -u student sudo whoami | grep -q root
    "; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
    
    # Test 5: Practice directories exist
    echo -n "Testing practice directories... "
    if docker run --rm "$image" /bin/bash -c "
        test -d /practice && test -d /opt/data && test -d /mnt/test
    "; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
    
    # Test 6: Networking tools
    echo -n "Testing networking tools... "
    if docker run --rm "$image" /bin/bash -c "
        which ip ping ssh > /dev/null 2>&1
    "; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
    
    # Test 7: Storage tools
    echo -n "Testing storage tools... "
    if docker run --rm "$image" /bin/bash -c "
        which lvm parted mkfs.ext4 > /dev/null 2>&1
    "; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
    
    echo -e "${GREEN}All tests passed for $distro!${NC}"
    echo
}

# Test all images
failed=0

if ! test_image "lfcs-practice-ubuntu:latest" "Ubuntu"; then
    failed=$((failed + 1))
fi

if ! test_image "lfcs-practice-centos:latest" "CentOS"; then
    failed=$((failed + 1))
fi

if ! test_image "lfcs-practice-rocky:latest" "Rocky Linux"; then
    failed=$((failed + 1))
fi

echo "=========================================="
if [ $failed -eq 0 ]; then
    echo -e "${GREEN}All images passed testing!${NC}"
    exit 0
else
    echo -e "${RED}$failed image(s) failed testing${NC}"
    exit 1
fi
