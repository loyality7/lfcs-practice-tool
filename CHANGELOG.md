# Changelog

All notable changes to the LFCS Practice Tool will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-11-29

### Added
- **Countdown timer for learning exercises** - Live timer display showing time remaining (MM:SS format)
  - Color-coded (green > 2min, yellow > 1min, red < 1min)
  - Configurable time limit per exercise (default 5 minutes)
  - Timer stops on correct answer or when time expires
- **Prominent version warning in welcome banner** - Update notification integrated directly in banner
  - Shows "UPDATE AVAILABLE" warning box when outdated
  - Displays which version you're on vs latest available
  - Shows "(Outdated!)" or "(Latest)" status next to version number
  - Provides update command directly
- **Improved menu navigation** - "Back" option (0) now returns to previous menu instead of exiting

### Fixed
- Removed duplicate divider lines in welcome banner
- Banner now displays cleanly with single set of dividers

## [1.0.9] - 2025-11-29

### Fixed
- Version display now shows actual installed package version instead of hardcoded config value
- CLI now uses `get_current_version()` from version_check utility for accurate version reporting

## [1.0.8] - 2025-11-29

### Fixed
- Update notification now displays on welcome screen (when running `lfcs` without arguments)
- Moved update check before welcome screen display to ensure all users see update notifications

## [1.0.7] - 2025-11-29

### Fixed
- **Critical bug in learning module validation** - Commands are now properly validated
  - Fixed validation logic that was accepting any command as correct
  - Exercises with validation dictionaries now execute validation commands properly
  - Users will now receive accurate feedback on command correctness

### Added
- **Automatic update checking** - CLI now checks PyPI for new versions on startup
  - Non-intrusive notification when updates are available
  - Cached checks (once per day) to avoid excessive API calls
  - `lfcs update` command to easily upgrade to latest version
  - `lfcs update --check` to only check without installing

### Changed
- Update notifications display current and latest version with upgrade command
- Help text now includes update command documentation

## [1.0.6] - 2025-11-29

### Added
- **Automatic Docker image building** - Images now build automatically on first use with progress display
- New `src/docker_manager/image_builder.py` module for building images
- Dockerfiles now included in pip package (`src/data/docker/`)

### Changed
- Simplified installation - no longer need to manually clone repo and build images
- Updated `DockerManager.create_container()` to trigger automatic builds when images are missing
- Installation now just `pip install lfcs` + `lfcs start` (images build on first run)

### Improved
- Real-time progress display during image building
- Better user experience with automatic setup
- First run takes 5-20 minutes (one-time), subsequent runs are instant


## [1.0.4] - 2025-11-29

### Fixed
- Fixed missing man pages in Docker containers by running `unminimize` in Ubuntu image
- Added `man-pages` package to CentOS and Rocky Linux images
- Man and whatis commands now work correctly in learning mode

### Changed
- Updated Docker base images to include full documentation

## [1.0.3] - 2025-11-29

### Fixed
- Fixed missing validation agent (`src/agent/lfcs-check`) in package
- Validation now works correctly after installation from PyPI

### Changed
- Updated `MANIFEST.in` and `setup.py` to include validation agent

## [1.0.2] - 2025-11-29

### Added
- Automatic workspace initialization - scenarios, learning modules, and schema are now copied automatically on first run
- New `src/utils/init.py` module for workspace initialization
- Scenarios and learning modules are now included in the PyPI package

### Fixed
- Fixed missing scenarios and learning modules after installation from PyPI
- Database schema is now correctly initialized

### Changed
- Moved `scenarios`, `learn_modules`, and `database/schema.sql` to `src/data` directory
- Updated package configuration to include data files
- Simplified installation process - no longer need to manually copy files

## [1.0.1] - 2025-11-28

### Fixed
- Initial PyPI release fixes
- Package metadata corrections

## [1.0.0] - 2025-11-27

### Added
- Initial release of LFCS Practice Tool
- 83+ practice scenarios across 5 LFCS exam categories
- Interactive learning mode with 14 structured modules
- Docker-based isolated practice environments
- Automatic validation with detailed feedback
- Progress tracking and statistics
- Multi-distribution support (Ubuntu, CentOS, Rocky Linux)
- AI-powered hints and validation (optional)
- Live validation during practice sessions
- Achievement system and streak tracking

### Categories
- Essential Commands (18 scenarios)
- Operations & Deployment (18 scenarios)
- Networking (18 scenarios)
- Storage (18 scenarios)
- Users & Groups (18 scenarios)

### Learning Modules
- Beginner: Linux basics, file navigation, basic commands
- Intermediate: Text processing, process management, packages
- Advanced: Networking, storage management, user administration
- Expert: Security hardening, automation, troubleshooting

---

## Version History Summary

- **1.0.4**: Man pages fix
- **1.0.3**: Validation agent fix
- **1.0.2**: Auto-initialization of scenarios and learning modules
- **1.0.1**: PyPI release fixes
- **1.0.0**: Initial release
