# LFCS Practice Tool - Troubleshooting Guide

Solutions to common issues and problems.

## Table of Contents

1. [Docker Issues](#docker-issues)
2. [Installation Issues](#installation-issues)
3. [Container Issues](#container-issues)
4. [Validation Issues](#validation-issues)
5. [Database Issues](#database-issues)
6. [Performance Issues](#performance-issues)
7. [Configuration Issues](#configuration-issues)
8. [Scenario Issues](#scenario-issues)
9. [Getting Help](#getting-help)

## Docker Issues

### Docker Daemon Not Running

**Symptoms**:
```
Error: Docker daemon is not running or not accessible
Cannot connect to the Docker daemon
```

**Solutions**:

1. **Check Docker status**:
   ```bash
   sudo systemctl status docker
   ```

2. **Start Docker daemon**:
   ```bash
   # Linux (systemd)
   sudo systemctl start docker
   
   # Linux (service)
   sudo service docker start
   
   # macOS/Windows
   # Start Docker Desktop application
   ```

3. **Enable Docker on boot**:
   ```bash
   sudo systemctl enable docker
   ```

4. **Verify Docker is running**:
   ```bash
   docker ps
   ```

### Permission Denied

**Symptoms**:
```
permission denied while trying to connect to the Docker daemon socket
Got permission denied while trying to connect to the Docker daemon
```

**Solutions**:

1. **Add user to docker group**:
   ```bash
   sudo usermod -aG docker $USER
   ```

2. **Apply group changes**:
   ```bash
   # Option 1: Log out and log back in
   
   # Option 2: Use newgrp (temporary)
   newgrp docker
   
   # Option 3: Restart session
   su - $USER
   ```

3. **Verify group membership**:
   ```bash
   groups
   # Should show 'docker' in the list
   ```

4. **Check Docker socket permissions**:
   ```bash
   ls -l /var/run/docker.sock
   # Should show: srw-rw---- 1 root docker
   ```

### Docker Image Not Found

**Symptoms**:
```
Error: Docker image not found
ImageNotFound: lfcs-practice-ubuntu:latest
```

**Solutions**:

1. **Build base images**:
   ```bash
   cd docker/base_images
   ./build_all.sh
   ```

2. **Build specific image**:
   ```bash
   cd docker/base_images/ubuntu
   docker build -t lfcs-practice-ubuntu:latest .
   ```

3. **Verify images exist**:
   ```bash
   docker images | grep lfcs-practice
   ```

4. **Check build logs**:
   ```bash
   # Review build output for errors
   ./build_all.sh 2>&1 | tee build.log
   ```

### Docker Out of Disk Space

**Symptoms**:
```
no space left on device
Error response from daemon: write /var/lib/docker/...: no space left on device
```

**Solutions**:

1. **Check disk usage**:
   ```bash
   df -h
   docker system df
   ```

2. **Remove unused containers**:
   ```bash
   docker container prune
   ```

3. **Remove unused images**:
   ```bash
   docker image prune -a
   ```

4. **Remove unused volumes**:
   ```bash
   docker volume prune
   ```

5. **Complete cleanup**:
   ```bash
   docker system prune -a --volumes
   ```

## Installation Issues

### Python Version Too Old

**Symptoms**:
```
Python 3.9+ required
SyntaxError: invalid syntax
```

**Solutions**:

1. **Check Python version**:
   ```bash
   python3 --version
   ```

2. **Install Python 3.9+**:
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3.9 python3.9-venv python3.9-dev
   
   # CentOS/RHEL
   sudo yum install python39
   
   # macOS
   brew install python@3.9
   ```

3. **Use specific Python version**:
   ```bash
   python3.9 -m venv venv
   source venv/bin/activate
   pip install -e .
   ```

### Missing Dependencies

**Symptoms**:
```
ModuleNotFoundError: No module named 'docker'
ImportError: cannot import name 'X' from 'Y'
```

**Solutions**:

1. **Install all dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install in development mode**:
   ```bash
   pip install -e ".[dev,test]"
   ```

3. **Upgrade pip**:
   ```bash
   pip install --upgrade pip
   ```

4. **Clear pip cache**:
   ```bash
   pip cache purge
   pip install -e . --no-cache-dir
   ```

### Installation Fails

**Symptoms**:
```
ERROR: Could not install packages
Failed building wheel for X
```

**Solutions**:

1. **Install build dependencies**:
   ```bash
   # Ubuntu/Debian
   sudo apt install python3-dev build-essential
   
   # CentOS/RHEL
   sudo yum install python3-devel gcc
   
   # macOS
   xcode-select --install
   ```

2. **Use virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -e .
   ```

3. **Install specific versions**:
   ```bash
   pip install docker==6.0.0 PyYAML==6.0
   ```

## Container Issues

### Container Fails to Start

**Symptoms**:
```
Error: Container failed to start
APIError: 500 Server Error
```

**Solutions**:

1. **Check Docker daemon logs**:
   ```bash
   sudo journalctl -u docker -n 50
   ```

2. **Check available resources**:
   ```bash
   free -h  # Memory
   df -h    # Disk space
   ```

3. **Try manual container creation**:
   ```bash
   docker run -it --rm lfcs-practice-ubuntu:latest /bin/bash
   ```

4. **Check container logs**:
   ```bash
   docker logs <container-id>
   ```

5. **Reduce resource requirements**:
   - Close other applications
   - Free up disk space
   - Increase Docker resource limits

### Container Hangs or Freezes

**Symptoms**:
- Container doesn't respond
- Commands timeout
- Shell doesn't accept input

**Solutions**:

1. **Check container status**:
   ```bash
   docker ps -a
   docker inspect <container-id>
   ```

2. **Check container resource usage**:
   ```bash
   docker stats <container-id>
   ```

3. **Force stop container**:
   ```bash
   docker stop -t 0 <container-id>
   docker rm -f <container-id>
   ```

4. **Restart Docker daemon**:
   ```bash
   sudo systemctl restart docker
   ```

### Cannot Access Container

**Symptoms**:
```
Error: Cannot connect to container
Container not found
```

**Solutions**:

1. **List all containers**:
   ```bash
   docker ps -a
   ```

2. **Check container name/ID**:
   ```bash
   docker ps --filter "name=lfcs-practice"
   ```

3. **Manually access container**:
   ```bash
   docker exec -it <container-id> /bin/bash
   ```

4. **Check container logs**:
   ```bash
   docker logs <container-id>
   ```

## Validation Issues

### Validation Fails Unexpectedly

**Symptoms**:
- Correct solution marked as failed
- Validation checks don't run
- Unexpected validation errors

**Solutions**:

1. **Check validation manually**:
   ```bash
   # Access container
   docker exec -it <container-id> /bin/bash
   
   # Run validation commands manually
   # Check expected vs actual output
   ```

2. **Review scenario YAML**:
   ```bash
   cat scenarios/category/difficulty/scenario.yaml
   # Check validation rules
   ```

3. **Check container state**:
   ```bash
   # Verify files exist
   ls -la /path/to/file
   
   # Check service status
   systemctl status service-name
   
   # Test commands
   command-to-validate
   ```

4. **Enable debug logging**:
   ```bash
   export LOG_LEVEL=DEBUG
   lfcs start
   # Check logs/lfcs-practice-*.log
   ```

### Validation Timeout

**Symptoms**:
```
Validation check timed out
Command execution timeout
```

**Solutions**:

1. **Increase timeout**:
   Edit `config/config.yaml`:
   ```yaml
   validation:
     timeout: 600  # Increase from 300
   ```

2. **Check command performance**:
   ```bash
   # Run command manually and time it
   time command-to-validate
   ```

3. **Optimize validation commands**:
   - Use more efficient commands
   - Reduce output processing
   - Check for hanging processes

### Custom Validation Script Fails

**Symptoms**:
```
Validation script not found
Script execution failed
```

**Solutions**:

1. **Check script exists**:
   ```bash
   ls -la docker/validation_scripts/script-name.sh
   ```

2. **Check script permissions**:
   ```bash
   chmod +x docker/validation_scripts/script-name.sh
   ```

3. **Test script manually**:
   ```bash
   docker exec -it <container-id> /bin/bash
   /opt/lfcs/validation_scripts/script-name.sh
   ```

4. **Check script syntax**:
   ```bash
   bash -n docker/validation_scripts/script-name.sh
   ```

## Database Issues

### Database Locked

**Symptoms**:
```
database is locked
OperationalError: database is locked
```

**Solutions**:

1. **Close other instances**:
   ```bash
   # Find processes using database
   lsof database/progress.db
   
   # Kill if necessary
   kill <pid>
   ```

2. **Wait and retry**:
   - The tool has automatic retry logic
   - Wait a few seconds and try again

3. **Check file permissions**:
   ```bash
   ls -la database/progress.db
   chmod 644 database/progress.db
   ```

4. **Backup and reset**:
   ```bash
   cp database/progress.db database/progress.db.backup
   rm database/progress.db
   # Database will be recreated
   ```

### Database Corrupted

**Symptoms**:
```
database disk image is malformed
DatabaseError: database is corrupted
```

**Solutions**:

1. **Backup database**:
   ```bash
   cp database/progress.db database/progress.db.backup
   ```

2. **Try SQLite recovery**:
   ```bash
   sqlite3 database/progress.db ".recover" | sqlite3 database/progress_recovered.db
   mv database/progress_recovered.db database/progress.db
   ```

3. **Export and reimport**:
   ```bash
   sqlite3 database/progress.db .dump > backup.sql
   rm database/progress.db
   sqlite3 database/progress.db < backup.sql
   ```

4. **Reset database** (loses progress):
   ```bash
   rm database/progress.db
   # Database will be recreated on next run
   ```

### Cannot Write to Database

**Symptoms**:
```
PermissionError: [Errno 13] Permission denied
Unable to open database file
```

**Solutions**:

1. **Check directory permissions**:
   ```bash
   ls -la database/
   chmod 755 database/
   ```

2. **Check file permissions**:
   ```bash
   ls -la database/progress.db
   chmod 644 database/progress.db
   ```

3. **Check ownership**:
   ```bash
   ls -la database/progress.db
   sudo chown $USER:$USER database/progress.db
   ```

4. **Check disk space**:
   ```bash
   df -h
   ```

## Performance Issues

### Slow Container Startup

**Symptoms**:
- Container takes long to start
- Timeout during container creation

**Solutions**:

1. **Check system resources**:
   ```bash
   free -h  # Memory
   top      # CPU usage
   df -h    # Disk space
   ```

2. **Reduce Docker resource usage**:
   - Close unused containers
   - Remove unused images
   - Clear Docker cache

3. **Optimize Docker settings**:
   - Increase Docker memory limit
   - Use faster storage for Docker
   - Enable Docker BuildKit

4. **Use SSD for Docker**:
   - Move Docker data directory to SSD
   - Configure in Docker settings

### Slow Validation

**Symptoms**:
- Validation takes very long
- Commands timeout

**Solutions**:

1. **Check container performance**:
   ```bash
   docker stats <container-id>
   ```

2. **Optimize validation commands**:
   - Use more efficient commands
   - Reduce output processing
   - Cache results where possible

3. **Increase container resources**:
   Edit `config/config.yaml`:
   ```yaml
   docker:
     memory_limit: "2g"
     cpu_limit: 2
   ```

### High Memory Usage

**Symptoms**:
- System runs out of memory
- Containers killed by OOM

**Solutions**:

1. **Check memory usage**:
   ```bash
   free -h
   docker stats
   ```

2. **Limit container memory**:
   Edit `config/config.yaml`:
   ```yaml
   docker:
     memory_limit: "1g"
   ```

3. **Close unused applications**:
   - Free up system memory
   - Close browser tabs
   - Stop unnecessary services

4. **Increase swap space**:
   ```bash
   # Check current swap
   swapon --show
   
   # Add swap file (if needed)
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

## Configuration Issues

### Configuration File Not Found

**Symptoms**:
```
FileNotFoundError: config/config.yaml
Configuration file not found
```

**Solutions**:

1. **Check file exists**:
   ```bash
   ls -la config/config.yaml
   ```

2. **Create from example**:
   ```bash
   cp config/config.yaml.example config/config.yaml
   ```

3. **Use default configuration**:
   - Tool will use defaults if config file missing
   - Check logs for warnings

### Invalid Configuration

**Symptoms**:
```
ValueError: Configuration error
YAML parsing error
```

**Solutions**:

1. **Validate YAML syntax**:
   ```bash
   python3 -c "import yaml; yaml.safe_load(open('config/config.yaml'))"
   ```

2. **Check for common errors**:
   - Indentation (use spaces, not tabs)
   - Missing colons
   - Unquoted special characters

3. **Compare with example**:
   ```bash
   diff config/config.yaml config/config.yaml.example
   ```

4. **Reset to defaults**:
   ```bash
   cp config/config.yaml config/config.yaml.backup
   cp config/config.yaml.example config/config.yaml
   ```

### Environment Variables Not Working

**Symptoms**:
- Environment variables ignored
- Configuration not overridden

**Solutions**:

1. **Check variable names**:
   ```bash
   env | grep LFCS
   env | grep DOCKER
   ```

2. **Export variables**:
   ```bash
   export DEFAULT_IMAGE="ubuntu"
   export LOG_LEVEL="DEBUG"
   ```

3. **Use .env file**:
   ```bash
   cp .env.example .env
   # Edit .env file
   ```

4. **Check variable precedence**:
   - Environment variables override config file
   - Verify correct variable names

## Scenario Issues

### Scenario Not Found

**Symptoms**:
```
No scenarios found matching criteria
Scenario ID not found
```

**Solutions**:

1. **List available scenarios**:
   ```bash
   lfcs list
   ```

2. **Check scenario file exists**:
   ```bash
   find scenarios -name "*.yaml"
   ```

3. **Verify scenario ID**:
   ```bash
   grep "^id:" scenarios/category/difficulty/*.yaml
   ```

4. **Check file permissions**:
   ```bash
   ls -la scenarios/
   chmod -R 644 scenarios/**/*.yaml
   ```

### Scenario YAML Invalid

**Symptoms**:
```
YAML parsing error
Invalid scenario structure
```

**Solutions**:

1. **Validate YAML syntax**:
   ```bash
   python3 -c "import yaml; yaml.safe_load(open('scenarios/path/to/scenario.yaml'))"
   ```

2. **Check required fields**:
   - id
   - category
   - difficulty
   - task
   - validation
   - points

3. **Compare with working scenario**:
   ```bash
   # Use a known-good scenario as reference
   cat scenarios/storage/easy/create_directory_01.yaml
   ```

4. **Use online YAML validator**:
   - https://www.yamllint.com/
   - Paste scenario content
   - Fix reported errors

## Getting Help

### Collecting Debug Information

When reporting issues, collect:

1. **Version information**:
   ```bash
   lfcs --version
   python3 --version
   docker --version
   ```

2. **System information**:
   ```bash
   uname -a
   cat /etc/os-release
   ```

3. **Error logs**:
   ```bash
   tail -n 100 logs/lfcs-practice-$(date +%Y%m%d).log
   ```

4. **Docker information**:
   ```bash
   docker info
   docker ps -a
   docker images
   ```

5. **Configuration**:
   ```bash
   cat config/config.yaml
   env | grep -E "(DOCKER|LFCS|LOG)"
   ```

### Reporting Issues

1. **Check existing issues**:
   - Search GitHub issues
   - Check if already reported

2. **Create detailed report**:
   - Clear title
   - Steps to reproduce
   - Expected vs actual behavior
   - Debug information
   - Screenshots if applicable

3. **Submit on GitHub**:
   - https://github.com/loyality7/lfcs-practice-tool/issues
   - Use issue template
   - Add relevant labels

### Community Support

- **GitHub Discussions**: Ask questions
- **Documentation**: Check all docs
- **Examples**: Review existing scenarios
- **Email**: Contact maintainers

### Emergency Recovery

If nothing works:

1. **Complete reset**:
   ```bash
   # Backup important data
   cp database/progress.db ~/progress_backup.db
   
   # Remove all containers
   docker rm -f $(docker ps -aq --filter "name=lfcs-practice")
   
   # Remove images
   docker rmi $(docker images -q "lfcs-practice-*")
   
   # Reinstall
   pip uninstall lfcs-practice-tool
   pip install -e .
   
   # Rebuild images
   cd docker/base_images && ./build_all.sh
   ```

2. **Fresh start**:
   ```bash
   # Clone fresh copy
   cd ..
   mv lfcs-practice-tool lfcs-practice-tool.old
   git clone https://github.com/loyality7/lfcs-practice-tool.git
   cd lfcs-practice-tool
   pip install -e .
   cd docker/base_images && ./build_all.sh
   ```

---

For more information, see:
- [User Guide](user_guide/USER_GUIDE.md)
- [Developer Guide](developer_guide/DEVELOPER_GUIDE.md)
- [Architecture Documentation](architecture/ARCHITECTURE.md)
