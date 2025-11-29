# LFCS Practice Base Images

This directory contains Dockerfiles and build scripts for creating base images used in the LFCS Practice Tool. Each image is configured with essential tools and packages needed for Linux Foundation Certified System Administrator (LFCS) exam preparation.

## Available Images

### Ubuntu 22.04
- **Image Name**: `lfcs-practice-ubuntu:22.04` (also tagged as `latest`)
- **Base**: Ubuntu 22.04 LTS
- **Use Case**: Debian-based system administration practice

### CentOS Stream 9
- **Image Name**: `lfcs-practice-centos:stream9` (also tagged as `latest`)
- **Base**: CentOS Stream 9
- **Use Case**: RHEL-based system administration practice

### Rocky Linux 9
- **Image Name**: `lfcs-practice-rocky:9` (also tagged as `latest`)
- **Base**: Rocky Linux 9
- **Use Case**: RHEL-compatible system administration practice

## Installed Tools and Packages

All images include the following categories of tools:

### System Utilities
- sudo, vim, nano, less, man-db, bash-completion

### Networking Tools
- net-tools, iproute2/iproute, iputils, traceroute
- DNS utilities (dnsutils/bind-utils)
- SSH server and client
- netcat/nmap-ncat

### System Management
- systemd
- cron/cronie
- at (job scheduling)

### Storage and Filesystem
- LVM2 (Logical Volume Manager)
- parted, gdisk (partitioning tools)
- xfsprogs, e2fsprogs, btrfs-progs (filesystem tools)
- NFS utilities

### User Management
- passwd, shadow-utils
- User and group management tools

### Process Management
- psmisc, procps/procps-ng
- htop (process viewer)

### File Management
- rsync, tar, gzip, bzip2, xz

### Text Processing
- grep, sed, awk/gawk

### Development Tools
- git, make, gcc

### Monitoring
- sysstat (system statistics)

### Security
- iptables
- firewalld (CentOS/Rocky)
- ufw (Ubuntu)
- SELinux tools (CentOS/Rocky)
- AppArmor (Ubuntu)

## User Accounts

Each image comes with two pre-configured accounts:

### Student User
- **Username**: `student`
- **Password**: `student`
- **Home**: `/home/student`
- **Shell**: `/bin/bash`
- **Privileges**: Full sudo access (NOPASSWD)
- **Groups**: sudo/wheel

### Root User
- **Username**: `root`
- **Password**: `root`
- **Full system access**

## Practice Directories

The following directories are pre-created for practice scenarios:
- `/practice` - Main practice directory (owned by student)
- `/opt/data` - Data directory for storage scenarios
- `/mnt/test` - Mount point for filesystem scenarios

## Building Images

### Build All Images
```bash
./build_all.sh
```

### Build Individual Images
```bash
# Ubuntu
cd ubuntu && ./build.sh

# CentOS
cd centos && ./build.sh

# Rocky Linux
cd rocky && ./build.sh
```

## Running Containers

### Basic Container
```bash
docker run --rm -it lfcs-practice-ubuntu:latest /bin/bash
```

### Container with Systemd (Required for Service Management)
```bash
docker run --rm -it --privileged \
  -v /sys/fs/cgroup:/sys/fs/cgroup:ro \
  lfcs-practice-ubuntu:latest
```

### Container with Custom Name
```bash
docker run --rm -it --privileged \
  --name lfcs-practice-session \
  lfcs-practice-ubuntu:latest
```

## Testing Images

After building, you can test the images:

```bash
# Test Ubuntu
docker run --rm -it lfcs-practice-ubuntu:latest /bin/bash -c "
  echo 'Testing Ubuntu image...'
  which sudo vim systemctl ip
  sudo -u student whoami
  ls -la /practice
"

# Test CentOS
docker run --rm -it lfcs-practice-centos:latest /bin/bash -c "
  echo 'Testing CentOS image...'
  which sudo vim systemctl ip
  sudo -u student whoami
  ls -la /practice
"

# Test Rocky
docker run --rm -it lfcs-practice-rocky:latest /bin/bash -c "
  echo 'Testing Rocky image...'
  which sudo vim systemctl ip
  sudo -u student whoami
  ls -la /practice
"
```

## Image Sizes

Approximate sizes after building:
- Ubuntu: ~400-500 MB
- CentOS: ~500-600 MB
- Rocky: ~500-600 MB

## Systemd Support

All images are configured to run systemd as the init system, which is required for:
- Service management (systemctl)
- Timer units
- Socket activation
- System logging

**Important**: When running containers that need systemd, use the `--privileged` flag and mount cgroups.

## Customization

To add additional packages or configurations:

1. Edit the respective Dockerfile
2. Add packages to the `RUN dnf install` or `RUN apt-get install` command
3. Rebuild the image using the build script

## Troubleshooting

### Image Build Fails
- Ensure Docker daemon is running
- Check internet connectivity for package downloads
- Verify base image availability

### Container Won't Start
- Use `--privileged` flag for systemd support
- Check Docker logs: `docker logs <container-id>`

### Package Not Found
- Update package lists in Dockerfile
- Verify package name for the specific distribution

## Security Notes

These images are designed for **practice and learning purposes only**:
- Default passwords are simple and well-known
- Root access is enabled
- SSH permits password authentication
- Sudo requires no password

**Do not use these images in production environments.**

## License

These Dockerfiles are part of the LFCS Practice Tool project.

## Contributing

To add support for additional distributions or tools:
1. Create a new directory under `base_images/`
2. Add a Dockerfile with required packages
3. Create a build script
4. Update this README
5. Test thoroughly with LFCS scenarios
