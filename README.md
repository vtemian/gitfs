gitfs [![CI](https://github.com/vtemian/gitfs/workflows/CI/badge.svg)](https://github.com/vtemian/gitfs/actions) [![Coverage Status](https://coveralls.io/repos/PressLabs/gitfs/badge.png?branch=HEAD)](https://coveralls.io/r/PressLabs/gitfs?branch=HEAD) ![PyPI](https://img.shields.io/pypi/v/gitfs)
========

# Welcome to GitFS v1.0.0 🎉

**gitfs** is a [FUSE](https://github.com/libfuse/libfuse) file system that fully integrates with git. You can mount a remote repository's branch locally, and any subsequent changes made to the files will be automatically committed to the remote.

gitfs was originally developed by the awesome engineering team at [Presslabs](https://www.presslabs.com/), a Managed WordPress Hosting provider, and is now maintained by the community with modern Python 3 support.

## 🚀 Version 1.0.0 - Major Release

This major release brings significant modernization:
- **Full Python 3.11+ support** - Modern Python with type hints and improved performance
- **FUSE 3 compatibility** - Works with latest Linux distributions
- **Modern packaging** - Uses `uv` and `pyproject.toml` for dependency management
- **Enhanced stability** - Comprehensive test coverage (>90%)
- **Better maintainability** - Clean, well-structured codebase

## What's its purpose?

gitfs was designed to bring the full powers of git to everyone, no matter how little they know about versioning. A user can mount any repository and all their changes will be automatically converted into commits. gitfs will also expose the history of the branch you're currently working on by simulating snapshots of every commit.

gitfs is useful in places where you want to keep track of all your files, but at the same time you don't have the possibility of organizing everything into commits yourself. A FUSE filesystem for git repositories, with local cache.

## System Requirements

- **Python 3.11 or higher**
- **FUSE 3** (libfuse3)
- **libgit2 1.8.1+**
- Linux (Ubuntu 20.04+, Debian 11+, etc.) or macOS

## Installing

### Ubuntu 22.04+ / Debian 12+

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-dev python3-pip
sudo apt-get install -y libfuse3-dev fuse3 libgit2-dev

# Install gitfs via pip
pip install gitfs
```

### Ubuntu 20.04 / Debian 11

```bash
# Add Python 3.11 repository
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update

# Install dependencies
sudo apt-get install -y python3.11 python3.11-dev python3.11-venv
sudo apt-get install -y libfuse3-dev fuse3 libgit2-dev

# Install gitfs
python3.11 -m pip install gitfs
```

### macOS

```bash
# Install FUSE for macOS (macFUSE)
brew install --cask macfuse

# Install gitfs
brew install gitfs
```

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/vtemian/gitfs.git
cd gitfs

# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies and run tests
uv sync --extra test --extra dev
make test

# Build and install
make all
sudo make install
```

### Docker

```bash
docker run -it --device /dev/fuse --cap-add SYS_ADMIN \
    -v /path/to/mount:/mnt/gitfs \
    gitfs/gitfs:1.0.0 \
    https://github.com/user/repo.git /mnt/gitfs
```

## Usage

Mount a remote or local repository easily:

```bash
gitfs https://github.com/user/repository.git /mount/directory
```

With custom options:

```bash
gitfs git@github.com:user/repo.git /mypath -o \
    repo_path=/tmp/repo,branch=main,fetch_timeout=30,merge_timeout=30
```

For a complete list of options, check the [arguments documentation](https://www.presslabs.com/code/gitfs/arguments/).

## Features

* **Automatic commit generation** - All changes are automatically converted to git commits
* **History browsing** - Navigate through commit history as directories
* **Smart merging** - Automatically handles merge conflicts by accepting local changes
* **Performance optimizations** - Intelligent caching reduces memory footprint
* **Batch operations** - Reduces push frequency by batching commits
* **FUSE 3 support** - Compatible with modern Linux distributions
* **Full Python 3 compatibility** - Type hints and modern Python features

## Development

### Prerequisites

- Python 3.11+
- FUSE 3 development headers
- libgit2 development files
- uv package manager

### Quick Start

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/vtemian/gitfs.git
cd gitfs
uv sync --extra test --extra dev

# Run tests
make test

# Format code
make format

# Build executable
make all
```

### Testing with Vagrant

```bash
# Start VM with FUSE 3 environment
vagrant up

# SSH into VM and run tests
vagrant ssh
cd /vagrant
make test
```

## Documentation

Full documentation is available at [gitfs homepage](https://www.presslabs.com/code/gitfs/).

## Contributing

Development happens at https://github.com/vtemian/gitfs

Issues are tracked at https://github.com/vtemian/gitfs/issues

The Python package is published at https://pypi.python.org/pypi/gitfs/

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## What's New in 1.0.0

- **Python 3.11+ only** - Dropped Python 2 support
- **FUSE 3 support** - Migrated from FUSE 2 for modern Linux compatibility
- **mfusepy** - Replaced fusepy with mfusepy for better FUSE 3 support
- **Modern packaging** - Uses `pyproject.toml` and `uv` for dependency management
- **Updated dependencies** - pygit2 1.18.0, libgit2 1.8.1, sentry-sdk 2.30.0
- **Improved testing** - 90%+ test coverage with GitHub Actions CI/CD
- **Better development experience** - Vagrant, Makefile, and modern tooling

See [CHANGELOG.md](CHANGELOG.md) for detailed release notes.

## License

This project is licensed under the Apache 2.0 license. Read the [LICENSE](LICENSE) file in the top distribution directory for the full license text.