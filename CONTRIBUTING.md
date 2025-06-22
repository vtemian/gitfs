# Contributing

We love pull requests. Here's a quick guide.

Fork, then clone the repo:
```
git clone git@github.com:your-username/gitfs.git
```

## Development Environment Setup

### Option 1: Vagrant (Recommended for consistent environment)

Start a Vagrant box with Ubuntu 24.04 LTS and Python 3.11 pre-configured:
```bash
vagrant up
vagrant ssh
cd /vagrant
source ~/gitfs/bin/activate
```

The Vagrant environment includes:
- Ubuntu 24.04 LTS (using Bento box)
- Python 3.11 with virtual environment
- All required system dependencies (FUSE, libgit2, etc.)
- Development tools (ruff, pytest, etc.)

### Option 2: Local Development

For local development, ensure you have:
- Python 3.11+
- FUSE filesystem support
- libgit2 development headers
- Git

Make your changes, write the tests and then:
```bash
make clean
make test
```

Push to your fork and submit the pull request.

## Mounting for development

In order to mount for development, you should mount with `foreground` and
`debug` set to `true` and `log` set to `/dev/stderr`:

```
gitfs /path/to/bare/repo /path/to/mount/point -o repo_path="/cloned/repo",foreground=true,debug=true,log=/dev/stderr
```

## Code style

The code should be properly formatted according to Python standards:
- Uses 4 spaces for indentation (not tabs)
- Line length limit of 88 characters
- Formatted using `ruff format`
- Linted using `ruff check`

Before committing, always run:
```bash
make format  # Format code with ruff
make lint    # Check code quality
make test    # Run tests
```
