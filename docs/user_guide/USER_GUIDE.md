# LFCS Practice Tool - User Guide

Complete guide to using the LFCS Practice Tool for Linux system administration training.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Practice Mode](#practice-mode)
3. [Learning Mode](#learning-mode)
4. [Understanding Statistics](#understanding-statistics)
5. [Advanced Features](#advanced-features)
6. [Tips and Best Practices](#tips-and-best-practices)
7. [FAQ](#faq)

## Getting Started

### First Time Setup

1. **Install the tool from PyPI**:
   ```bash
   pip install lfcs
   ```

2. **Clone repository for Docker files and scenarios**:
   ```bash
   git clone https://github.com/loyality7/lfcs-practice-tool.git
   cd lfcs-practice-tool
   ```

3. **Build Docker images**:
   ```bash
   cd docker/base_images
   ./build_all.sh
   cd ../..
   ```

4. **Verify installation**:
   ```bash
   lfcs --version
   lfcs --help
   ```

5. **Check for updates**:
   The tool automatically checks for updates on startup. You can also manually check:
   ```bash
   lfcs update
   ```

**Note**: The PyPI package contains only Python code. You need the repository for Docker files, scenarios, and learning modules.

### Understanding the Interface

The tool uses a clean, terminal-based interface with:
- **Color coding**: Green for success, red for errors, yellow for warnings
- **Interactive menus**: Number-based selection with "Back" (0) navigation
- **Progress indicators**: Visual feedback on your performance
- **Detailed feedback**: Specific information about what passed/failed

## Practice Mode

### Starting a Practice Session

#### Interactive Mode (Recommended)

```bash
lfcs start
```

This launches an interactive menu where you:
1. Select a category (networking, storage, etc.)
2. Choose difficulty (easy, medium, hard)
3. Pick a specific scenario
4. Work in the Docker container
5. Get automatic validation

#### Direct Mode (With Filters)

```bash
# Start with specific filters
lfcs start --category networking --difficulty easy

# Choose distribution
lfcs start --distribution centos

# Enable AI features
lfcs start --ai
```

### Working in the Container

Once a scenario starts:

1. **Read the task carefully**: Note all requirements
2. **Review hints**: Available if you get stuck
3. **Work in the shell**: Complete the task
4. **Use live validation**: Type `lfcs-check` in the container to validate without exiting
5. **Exit when done**: Type `exit` to return and get final validation

### Live Validation Feature

While working in the container, you can check your progress:

```bash
# Inside the container
lfcs-check
```

This runs validation without exiting, showing you:
- Which checks passed
- Which checks failed
- Specific feedback for each check

### Understanding Validation Results

After completing a scenario, you'll see:

```
========================================================================
                        SESSION RESULTS
========================================================================

  ✓ PASSED

Summary
-------
  Score: 150 / 150
  Checks Passed: 5 / 5
  Duration: 180 seconds

Detailed Results:

  ✓ File /etc/network/interfaces exists
  ✓ Interface eth0 configured with correct IP
  ✓ Gateway configured correctly
  ✓ DNS servers configured
  ✓ Network connectivity verified

========================================================================
```

### Scenario Categories

#### 1. Essential Commands
Practice core Linux commands:
- Text processing (grep, sed, awk)
- File operations (find, tar, compression)
- Pipes and redirection
- Process substitution

**Example scenarios**:
- Search and replace text in files
- Extract specific data from logs
- Create and extract archives
- Complex command pipelines

#### 2. Operations & Deployment
System administration tasks:
- Service management (systemd)
- Package management (apt, yum)
- Process management
- System monitoring
- Cron jobs and scheduling

**Example scenarios**:
- Create and enable systemd services
- Install and configure packages
- Set up cron jobs
- Monitor system resources

#### 3. Networking
Network configuration and troubleshooting:
- Interface configuration
- Routing and gateways
- DNS configuration
- Firewall rules
- Network troubleshooting

**Example scenarios**:
- Configure static IP addresses
- Set up routing tables
- Configure DNS resolution
- Create firewall rules

#### 4. Storage
Disk and filesystem management:
- Filesystem creation and mounting
- LVM (Logical Volume Management)
- Permissions and ownership
- Disk quotas
- RAID configuration

**Example scenarios**:
- Create and mount filesystems
- Set up LVM volumes
- Configure file permissions
- Implement disk quotas

#### 5. Users & Groups
User and permission management:
- User creation and modification
- Group management
- Password policies
- Sudo configuration
- Access control

**Example scenarios**:
- Create users with specific requirements
- Configure sudo access
- Set up password policies
- Manage group memberships

### Difficulty Levels

#### Easy
- Single-step tasks
- Basic commands
- Clear requirements
- Minimal troubleshooting

**Recommended for**: Beginners, first-time Linux users

#### Medium
- Multi-step tasks
- Requires understanding of concepts
- Some troubleshooting needed
- Integration of multiple commands

**Recommended for**: Intermediate users with basic Linux experience

#### Hard
- Complex scenarios
- Advanced configurations
- Troubleshooting required
- Multiple interconnected tasks

**Recommended for**: Advanced users preparing for LFCS exam

### Distribution Support

Practice on different Linux distributions:

```bash
# Ubuntu (default)
lfcs start --distribution ubuntu

# CentOS
lfcs start --distribution centos

# Rocky Linux
lfcs start --distribution rocky
```

**Note**: Some scenarios are distribution-specific, while others work on all distributions.

## Learning Mode

### Interactive Learning System

Learning mode provides structured lessons from basics to LFCS level:

```bash
# Start learning mode
lfcs learn

# List all modules
lfcs learn --list

# Start specific module
lfcs learn --module 01_beginner/01_linux_basics

# Continue from last lesson
lfcs learn --continue
```

### Learning Path

#### Level 1: Beginner
- Linux basics and file system
- File navigation (cd, ls, pwd)
- File operations (cp, mv, rm, mkdir)
- Viewing files (cat, less, head, tail)

#### Level 2: Intermediate
- Text processing (grep, sed, awk)
- Pipes and redirection
- Process management (ps, top, kill)
- Package management

#### Level 3: Advanced
- Networking basics
- Storage management
- User management

#### Level 4: Expert
- Security hardening
- Automation and scripting
- Troubleshooting

### Interactive Exercises

Learning modules include:
- **Command exercises**: Practice specific commands
- **Question exercises**: Test your knowledge
- **Task exercises**: Complete real-world tasks

- **Countdown Timer**: Live timer at the top of the screen keeps you on track
- **Real Shell Experience**: Enhanced prompt (`student@lfcs:~$`) mimics real environments
- **Progressive hints**: Get help when stuck without losing all points
- **Immediate feedback**: Know instantly if you got it right
- **Points and progress tracking**: Gamified learning experience
- **Hands-on practice in containers**: Real Linux environment, not a simulation

## Understanding Statistics

### Viewing Statistics

```bash
# Overall statistics
lfcs stats

# Category-specific
lfcs stats --category networking
```

### Statistics Breakdown

#### Overall Performance
- **Total Attempts**: Number of scenarios attempted
- **Total Passed**: Number of scenarios completed successfully
- **Pass Rate**: Percentage of successful attempts
- **Average Score**: Mean score across all attempts
- **Current Streak**: Consecutive successful attempts
- **Best Streak**: Longest streak achieved

#### Category Performance
For each category, you'll see:
- Attempts and pass rate
- Average score
- Mastery by difficulty level

#### Mastery Percentages

Mastery is calculated based on:
- Pass rate (60% weight)
- Average score (40% weight)

**Mastery levels**:
- **80%+**: Mastered (★)
- **60-79%**: Proficient (◐)
- **<60%**: Needs practice (○)

### Recommendations

The tool provides personalized recommendations:
- Suggest progression to harder difficulties
- Identify weak areas
- Encourage practice in specific categories
- Celebrate achievements

**Example recommendations**:
```
Recommendations:
  • You've mastered easy networking scenarios (85% mastery)! Try medium difficulty to progress.
  • Practice more storage scenarios to improve
  • Amazing 7-scenario streak! Keep it up!
```

## Advanced Features

### AI-Powered Features

Enable AI for enhanced learning:

```bash
# Set API key
export ANTHROPIC_API_KEY="your-key"

# Start with AI
lfcs start --ai
```

**AI features**:
- Intelligent hints based on your progress
- Dynamic scenario generation
- Advanced validation feedback
- Personalized learning suggestions

### Local Practice Mode

Practice on your local system without Docker:

```bash
lfcs start --local
```

**WARNING**: This modifies your actual system. Use only if you:
- Understand the risks
- Have backups
- Know how to undo changes
- Are practicing on a test system

### Configuration Customization

#### Configuration Files

Edit `config/config.yaml`:

```yaml
general:
  project_name: "LFCS Practice Tool"
  version: "1.0.0"

docker:
  default_image: "ubuntu"
  network_mode: "bridge"
  cleanup_on_exit: true

scoring:
  passing_threshold: 0.70
  time_bonus: true
  difficulty_multipliers:
    easy: 1.0
    medium: 1.5
    hard: 2.0
```

#### Environment Variables

Override settings with environment variables:

```bash
# Docker settings
export DEFAULT_IMAGE="centos"
export CONTAINER_TIMEOUT="7200"

# Logging
export LOG_LEVEL="DEBUG"
export LOGS_PATH="custom/logs"

# Database
export DB_PATH="custom/progress.db"
```

### Custom Scenarios

Create your own practice scenarios:

1. Copy an existing scenario as template
2. Modify task, validation rules, and points
3. Place in appropriate category/difficulty folder
4. Test with `lfcs start`

See [Developer Guide](../developer_guide/DEVELOPER_GUIDE.md) for details.

## Tips and Best Practices

### For Beginners

1. **Start with easy scenarios**: Build confidence with simple tasks
2. **Read hints carefully**: They guide you without giving away answers
3. **Use learning mode**: Structured lessons teach fundamentals
4. **Don't rush**: Take time to understand each concept
5. **Review feedback**: Learn from failed attempts

### For Intermediate Users

1. **Focus on weak areas**: Use statistics to identify gaps
2. **Try different distributions**: Practice on Ubuntu, CentOS, and Rocky
3. **Time yourself**: Simulate exam conditions
4. **Experiment**: Try different approaches to solve problems
5. **Use live validation**: Check progress without exiting

### For Advanced Users

1. **Master hard scenarios**: Challenge yourself with complex tasks
2. **Aim for 100% scores**: Perfect your technique
3. **Practice speed**: Complete scenarios quickly and accurately
4. **Create custom scenarios**: Design your own practice tasks
5. **Help others**: Contribute scenarios and improvements

### Exam Preparation

1. **Cover all categories**: Don't skip any LFCS domain
2. **Practice regularly**: Consistent practice builds muscle memory
3. **Simulate exam conditions**: Time limits, no external resources
4. **Review documentation**: Know where to find information quickly
5. **Understand concepts**: Don't just memorize commands

### Effective Learning

1. **Set goals**: Aim for specific mastery levels
2. **Track progress**: Review statistics regularly
3. **Take breaks**: Avoid burnout with regular breaks
4. **Practice variety**: Mix categories and difficulties
5. **Learn from mistakes**: Review failed attempts carefully

## FAQ

### General Questions

**Q: Do I need Docker to use the tool?**
A: Docker is required for practice mode. Learning mode can work without Docker, but practice scenarios need isolated containers.

**Q: Can I practice on my actual system?**
A: Yes, with `--local` flag, but this is risky and not recommended except on test systems.

**Q: How long does it take to prepare for LFCS?**
A: Varies by experience. Beginners: 2-3 months. Intermediate: 1-2 months. Advanced: 2-4 weeks of focused practice.

**Q: Are the scenarios similar to the actual LFCS exam?**
A: Yes, scenarios are designed to match LFCS exam objectives and difficulty.

### Technical Questions

**Q: Why is Docker required?**
A: Docker provides isolated, reproducible environments. You can practice safely without affecting your system.

**Q: Can I use Podman instead of Docker?**
A: Currently, only Docker is supported. Podman support may be added in future versions.

**Q: How much disk space do I need?**
A: Minimum 10GB for Docker images and scenarios. 20GB recommended for comfortable use.

**Q: Can I run this on Windows?**
A: Yes, with WSL2 (Windows Subsystem for Linux) and Docker Desktop.

### Usage Questions

**Q: How do I reset my progress?**
A: Use `lfcs reset --confirm` and type 'DELETE' to confirm.

**Q: Can I export my statistics?**
A: Statistics are stored in SQLite database at `database/progress.db`. You can query it directly or use `lfcs stats`.

**Q: What if a scenario validation fails incorrectly?**
A: Check container logs, review the scenario YAML, and report issues on GitHub.

**Q: Can I practice offline?**
A: Yes, once Docker images are built and scenarios are downloaded, you can practice offline.

### Troubleshooting

**Q: Docker permission denied error?**
A: Add your user to docker group: `sudo usermod -aG docker $USER`, then log out and back in.

**Q: Container fails to start?**
A: Check Docker daemon status: `sudo systemctl status docker`. Ensure sufficient resources (RAM, disk).

**Q: Database locked error?**
A: Close other instances of the tool. If persistent, check for processes using the database.

**Q: Validation takes too long?**
A: Increase timeout in config or check container performance. Some scenarios require more time.

## Getting Help

### Resources

- **Documentation**: Check docs/ directory
- **Examples**: Review existing scenarios in scenarios/
- **Logs**: Check logs/ directory for detailed information
- **GitHub Issues**: Report bugs and request features

### Community

- **Discussions**: Ask questions on GitHub Discussions
- **Contributing**: See CONTRIBUTING.md for guidelines
- **Email**: Contact maintainers for support

### Reporting Issues

When reporting issues, include:
1. Tool version (`lfcs --version`)
2. Operating system and version
3. Docker version (`docker --version`)
4. Error messages and logs
5. Steps to reproduce

---

**Happy Learning!**

For more information, see:
- [Developer Guide](../developer_guide/DEVELOPER_GUIDE.md)
- [Architecture Documentation](../architecture/ARCHITECTURE.md)
- [Troubleshooting Guide](../TROUBLESHOOTING.md)
