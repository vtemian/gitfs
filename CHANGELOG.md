# Changelog

All notable changes to GitFS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-08-11

### 🎉 Major Release

This is a major release of GitFS, marking a significant modernization of the codebase with updated dependencies, improved maintainability, and full Python 3 compatibility.

### Added
- Full **FUSE 3** support - migrated from FUSE 2 to FUSE 3 for compatibility with modern Linux distributions
- **uv** package manager integration for faster, more reliable dependency management
- Modern Python packaging with `pyproject.toml` configuration
- Comprehensive test coverage (>90%) with GitHub Actions CI/CD
- Claude AI agent configuration for automated development assistance
- Improved error handling and logging throughout the codebase

### Changed
- **BREAKING**: Now requires Python 3.11+ (dropped Python 2 support)
- **BREAKING**: Requires FUSE 3 instead of FUSE 2
- Migrated from `fusepy` to `mfusepy` for better FUSE 3 compatibility
- Updated to `pygit2` v1.18.0 with libgit2 v1.8.1
- Modernized build system using `pex` for executable generation
- Replaced legacy `setup.py` with modern `pyproject.toml`
- Improved test infrastructure with Vagrant for consistent testing environment
- Updated all GitHub workflows to use modern actions and Python 3.11

### Fixed
- Resolved all FUSE 3 compatibility issues
- Fixed deprecated FUSE mount options (removed `nonempty`)
- Corrected test failures related to FUSE version differences
- Various bug fixes and performance improvements

### Technical Improvements
- Clean, maintainable codebase with consistent formatting (ruff)
- Type hints and modern Python idioms throughout
- Simplified dependency management with uv
- Automated testing on Ubuntu 24.04 with FUSE 3
- Improved development workflow with Makefile targets

### Dependencies
- Python 3.11+
- mfusepy 3.0.0 (FUSE 3 compatible)
- pygit2 1.18.0
- libgit2 1.8.1
- FUSE 3.14+
- sentry-sdk 2.30.0

## [0.5.2] - Previous Release

### Changed
- Updated dependencies and minor bug fixes

## [0.4.5.1] - Historical

### Fixed
- Fix typo for max_open_files argument on mount

## [0.4.5] - Historical

### Added
- Add max_open_files mount option which allow to specify a files open hard and soft limit

## [0.4.4] - Historical

### Added
- Show a helpful message when trying to clone an empty repository #239
- Add sentry tags #244

### Changed
- Upgrade pygit2 to 0.24.1

### Fixed
- Log exception only on failed push #240

## [0.4.3] - Historical

### Changed
- Improve commit message thanks to @tusharmakkar08

## [0.4.2] - Historical

### Fixed
- Fix pending writers bug #223
- Cleanup code and error messages (thanks to @promulo and @ChristianAlexander)

## [0.4.1] - Historical

### Added
- Add credentials to push and fetch operations #226 (hotfix)

## [0.4.0] - Historical

### Added
- Retry mechanism for push #201
- Port to Python 3 thanks to @justuswilhelm #199
- Improve test running speed thanks to @rciorba
- Improve development using vagrant

### Fixed
- Delete directories on force checkout #221

### Changed
- Improve logging #222

[Previous versions omitted for brevity - see CHANGELOG.txt for complete history]