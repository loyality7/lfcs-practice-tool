FROM rockylinux:9

# Install essential LFCS packages
RUN dnf install -y \
    # System utilities
    sudo \
    vim \
    nano \
    less \
    man-db \
    bash-completion \
    # Networking tools
    net-tools \
    iproute \
    iputils \
    traceroute \
    bind-utils \
    nmap-ncat \
    openssh-server \
    openssh-clients \
    # System management
    systemd \
    cronie \
    at \
    # Storage and filesystem
    lvm2 \
    parted \
    gdisk \
    xfsprogs \
    e2fsprogs \
    nfs-utils \
    # Package management
    dnf-plugins-core \
    # User management
    passwd \
    shadow-utils \
    # Process management
    psmisc \
    procps-ng \
    # File management
    rsync \
    tar \
    gzip \
    bzip2 \
    xz \
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
    firewalld \
    # SELinux
    selinux-policy \
    selinux-policy-targeted \
    policycoreutils \
    policycoreutils-python-utils \
    && dnf clean all

# Create student user with sudo privileges
RUN useradd -m -s /bin/bash student && \
    usermod -aG wheel student && \
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

# Enable systemd
VOLUME [ "/sys/fs/cgroup" ]
CMD ["/usr/sbin/init"]

# Labels
LABEL maintainer="LFCS Practice Tool"
LABEL description="Rocky Linux 9 base image for LFCS practice scenarios"
LABEL distribution="rocky"
LABEL version="9"
