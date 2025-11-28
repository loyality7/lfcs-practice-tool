FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install essential LFCS packages
RUN apt-get update && apt-get install -y \
    # System utilities
    sudo \
    vim \
    nano \
    less \
    man-db \
    manpages \
    manpages-posix \
    bash-completion \
    # Networking tools
    net-tools \
    iproute2 \
    iputils-ping \
    traceroute \
    dnsutils \
    netcat \
    openssh-server \
    openssh-client \
    # System management
    systemd \
    systemd-sysv \
    cron \
    at \
    # Storage and filesystem
    lvm2 \
    parted \
    gdisk \
    xfsprogs \
    e2fsprogs \
    btrfs-progs \
    nfs-common \
    # Package management
    apt-transport-https \
    software-properties-common \
    # User management
    passwd \
    # Process management
    psmisc \
    procps \
    htop \
    # File management
    rsync \
    tar \
    gzip \
    bzip2 \
    xz-utils \
    # Text processing
    grep \
    sed \
    gawk \
    # Development tools
    git \
    make \
    gcc \
    # Monitoring
    sysstat \
    # Firewall
    iptables \
    ufw \
    # SELinux (AppArmor on Ubuntu)
    apparmor \
    apparmor-utils \
    && rm -rf /var/lib/apt/lists/*

# Create student user with sudo privileges
RUN useradd -m -s /bin/bash -G sudo student && \
    echo "student:student" | chpasswd && \
    echo "student ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Create practice directories
RUN mkdir -p /practice /opt/data /mnt/test && \
    chown student:student /practice

# Configure SSH
RUN mkdir -p /var/run/sshd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Set root password
RUN echo "root:root" | chpasswd

# Keep container running
# Note: For systemd scenarios, container needs to be started with --privileged and proper mounts
CMD ["/bin/bash", "-c", "tail -f /dev/null"]

# Labels
LABEL maintainer="LFCS Practice Tool"
LABEL description="Ubuntu 22.04 base image for LFCS practice scenarios"
LABEL distribution="ubuntu"
LABEL version="22.04"
