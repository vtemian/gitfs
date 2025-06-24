# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Git Workflow Requirements

**Always follow these practices BEFORE each commit:**
1. Create a new branch for each feature/fix: `git checkout -b feature/description`
2. Use conventional commits: `type(scope): description`
3. **Run `make format`** to ensure code formatting compliance
4. **Run `make test`** to verify all integration tests pass
5. **Write comprehensive integration tests** for all new features
6. Never commit directly to main branch

### Pre-Commit Checklist
Before every commit, ensure you have run:
```bash
make format  # Fix all formatting and linting issues
make test    # Verify all tests pass
```
**Do not commit if either command fails or shows errors.**

### Post-Commit Workflow
After a successful commit, push to the current branch:
```bash
git push -u origin HEAD  # Push current branch to remote
```

### Commit Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code refactoring
- `test`: Tests
- `chore`: Maintenance


## Project Overview

GitFS is a Python FUSE (Filesystem in Userspace) filesystem that integrates with Git repositories. It allows mounting remote repositories as local filesystems where file changes are automatically committed and synchronized with the remote.

### Git LFS Support

GitFS includes comprehensive Git LFS (Large File Storage) support for handling large files efficiently:

- **Automatic LFS Detection**: Files larger than the configured threshold are automatically stored using LFS
- **Transparent Access**: LFS files are seamlessly accessible through the filesystem interface
- **Configurable Thresholds**: Size-based and pattern-based LFS usage via mount options
- **Background Operations**: Automatic LFS fetch/push operations with repository synchronization

#### LFS Configuration Options

Available via `-o` mount parameter:

- `lfs_enabled=true/false` - Enable/disable LFS support (default: true)
- `lfs_size_threshold=100` - Size threshold in MB for automatic LFS usage (default: 100MB)
- `lfs_auto_fetch=true/false` - Automatically fetch missing LFS objects (default: true)
- `lfs_auto_push=true/false` - Automatically push LFS objects during sync (default: true)

#### Usage Examples

```bash
# Enable LFS with 50MB threshold
gitfs git@github.com:user/repo.git /mount/point -o lfs_size_threshold=50

# Disable LFS entirely
gitfs git@github.com:user/repo.git /mount/point -o lfs_enabled=false

# LFS with manual sync control
gitfs git@github.com:user/repo.git /mount/point -o lfs_auto_fetch=false,lfs_auto_push=false
```

## Development Commands

### Testing
- **Run all tests**: `make test` (sets up test environment and runs pytest with coverage)
- **Test environment setup**: `make testenv` (creates virtual environment and installs test dependencies)
- **Clean test artifacts**: `make clean` (removes build and test directories)

### Code Quality
- **Format code**: `make format` (runs ruff formatter with Python 3.11+ compatibility)
- **Lint code**: `make lint` (checks code formatting with ruff)
- **Verify formatting**: `make verify-lint` (ensures code is properly formatted)

### Building
- **Build executable**: `make all` (creates build/gitfs executable using pex)
- **Install**: `make install` (installs to /usr/local/bin)

### Documentation
- **Build docs**: `make docs` (builds MkDocs documentation)

## Architecture

### Core Components

**Filesystem Views** (`gitfs/views/`):
- `IndexView`: Root view exposing `current/` and `history/` directories
- `CurrentView`: Read-write view of working directory with git staging
- `HistoryView`: Read-only hierarchical view organized by date (YYYY-MM-DD)
- `CommitView`: Read-only view of specific commits via `history/date/time-hash` paths
- `ReadOnlyView`/`PassthroughView`: Base classes for filesystem operations

**Background Workers** (`gitfs/worker/`):
- `FetchWorker`: Periodic `git fetch` operations with configurable timeouts
- `SyncWorker`: Commit batching, merging, and push operations with retry logic
- `CommitQueue`: Thread-safe queue for batching filesystem operations into commits

**Caching System** (`gitfs/cache/`):
- `LRUCache`: Thread-safe LRU cache with size limits
- `CommitCache`: Specialized cache for git commits organized by date
- Decorators for method-level caching

**Repository Interface** (`gitfs/repository.py`):
- Central git operations facade wrapping pygit2
- Handles cloning, branching, commits, and synchronization

**Routing System** (`gitfs/routes.py`, `gitfs/router.py`):
- URL-based view routing with regex pattern matching
- Caches view instances to avoid repeated instantiation

### Key Decorators (`gitfs/utils/decorators/`)

- `@write_operation`: Ensures write safety and tracks active writers
- `@not_in`: Validates operations against gitignore patterns
- `@retry`: Exponential backoff for failed operations
- `@lru_cache`: Method-level LRU caching

### Data Flow

**Read Operations**: Path → Router → View → Repository/Cache → FUSE Response
**Write Operations**: Write → Validation → Filesystem → Git Staging → Commit Queue → Background Sync

## Testing Structure

- **Unit tests**: `tests/` mirrors `gitfs/` structure
- **Integration tests**: `tests/integrations/` tests complete filesystem operations
- **Test fixtures**: Uses temporary git repositories and mount points
- **Coverage**: Configured in `.coveragerc` with pytest-cov

## Development Setup

The test system uses:
- Temporary directories for git repositories and mount points
- Background GitFS process managed via PID file
- Clean teardown with forced unmounting

## Key Dependencies

- `fusepy`: FUSE bindings for Python
- `pygit2`: Git operations via libgit2
- `atomiclong`: Thread-safe counters
- `sentry-sdk`: Error reporting (Sentry)
