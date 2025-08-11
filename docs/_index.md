---
title: GitFS v1.0.0 - Version Controlled File System
linktitle: What is GitFS
description: GitFS is a FUSE 3 file system that fully integrates with git, providing automatic version control for all file operations
keywords: [gitfs, versioned filesystem, git filesystem, fuse3, linux filesystem, macos filesystem, python3, automatic commits]
---

## Welcome to GitFS v1.0.0

GitFS is a [FUSE 3](https://github.com/libfuse/libfuse) file system that fully integrates with git. You can mount a remote repository's branch locally, and any subsequent changes made to the files will be automatically committed to the remote.

### 🎉 Major Release Highlights

Version 1.0.0 represents a complete modernization of GitFS:

- **Python 3.11+ Support** - Full compatibility with modern Python, dropping Python 2
- **FUSE 3 Integration** - Updated to work with latest Linux distributions 
- **Modern Packaging** - Uses `uv` and `pyproject.toml` for dependency management
- **Enhanced Performance** - Improved caching and optimized git operations
- **Better Stability** - Comprehensive test coverage (>90%) and continuous integration

## What's its purpose?

GitFS was designed to bring the full powers of git to everyone, irrespective of their experience using the tool. You can mount any repository, and all the changes you make will be automatically converted into commits. GitFS will also expose the history of the branch you're currently working on by simulating snapshots of every commit.

GitFS is useful in places where you want to keep track of all your files, but at the same time you don't have the possibility of organizing everything into commits yourself. It provides a FUSE file system for git repositories with intelligent local caching.

## Key Features

- **Automatic commit generation** - All file operations are automatically converted to git commits
- **History browsing** - Navigate through commit history as directories
- **Smart conflict resolution** - Merges with upstream by automatically accepting local changes
- **Flexible permissions** - Mount the file system as a specific user or group
- **Performance optimizations** - Intelligent caching reduces memory footprint and speeds up navigation
- **Batch operations** - Reduces the number of pushes by grouping commits
- **FUSE 3 compatibility** - Works with modern Linux kernels and distributions
- **Python 3.11+ support** - Modern Python with type hints and improved performance

## System Requirements

- **Python 3.11 or higher**
- **FUSE 3** (libfuse3)
- **libgit2 1.8.1+**
- **mfusepy 3.0.0** (FUSE 3 Python bindings)
- Linux (Ubuntu 20.04+, Debian 11+, RHEL 8+) or macOS

## Quick Start

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get install libfuse3-dev fuse3 libgit2-dev python3.11

# Install GitFS
pip install gitfs

# Mount a repository
gitfs https://github.com/user/repo.git /mount/point
```

## What's New in 1.0.0

### Breaking Changes
- Requires Python 3.11+ (dropped Python 2 support)
- Requires FUSE 3 instead of FUSE 2
- Uses mfusepy instead of fusepy

### Major Improvements
- Modern Python packaging with pyproject.toml
- Integration with uv package manager
- Updated to pygit2 1.18.0 and libgit2 1.8.1
- Comprehensive test suite with >90% coverage
- GitHub Actions CI/CD pipeline
- Vagrant development environment with FUSE 3

### Technical Enhancements
- Removed deprecated FUSE options
- Improved error handling and logging
- Better memory management
- Optimized git operations
- Clean, maintainable codebase

## Development

GitFS is actively maintained and welcomes contributions. Development happens at [github.com/vtemian/gitfs](https://github.com/vtemian/gitfs).

### Getting Started with Development

```bash
# Clone the repository
git clone https://github.com/vtemian/gitfs.git
cd gitfs

# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync --extra test --extra dev

# Run tests
make test

# Format code
make format
```

### Testing with Vagrant

The project includes a Vagrant configuration for testing with FUSE 3:

```bash
vagrant up
vagrant ssh
cd /vagrant
make test
```

## Contributing

We welcome contributions! Please see the [CONTRIBUTING.md](https://github.com/vtemian/gitfs/blob/main/CONTRIBUTING.md) file for guidelines.

Issues are tracked at [github.com/vtemian/gitfs/issues](https://github.com/vtemian/gitfs/issues).

## License

This project is licensed under the Apache 2.0 license. See the [LICENSE](https://github.com/vtemian/gitfs/blob/main/LICENSE) file for the complete text.