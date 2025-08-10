# Repository Guidelines

## Project Structure & Module Organization
- `gitfs/`: core package (mounting, repository, router, views, workers). Example: `gitfs/mounter.py`, `gitfs/repository.py`.
- `tests/`: pytest suite mirroring package layout (e.g., `tests/test_mount.py`, `tests/views/`).
- `script/`: helper scripts for test env and CI (`script/test`, `script/testenv`).
- Tooling: `Makefile`, `pyproject.toml` (deps, ruff, pytest), `Dockerfile.test`, `Vagrantfile`, `docs/`.

## Build, Test, and Development Commands
- `make venv-dev`: create local dev environment via `uv` (installs dev extras).
- `make testenv && make test`: prepare ephemeral test env and run pytest with coverage.
- `make all`: build a single-file executable at `build/gitfs` using `pex`.
- `make format` / `make lint`: format and lint with Ruff; `make verify-lint` ensures no diffs.
- Run locally: `uv run gitfs <bare_repo> <mount_dir> -o repo_path=<workdir>,foreground=true,debug=true,log=/dev/stderr`.

## Coding Style & Naming Conventions
- Python 3.11+. Use 4-space indentation, 88-char lines, double quotes, and import sorting (Ruff configured in `pyproject.toml`).
- Names: modules and functions `snake_case`, classes `CamelCase`, constants `ALL_CAPS`.
- Keep changes minimal; avoid drive-by formatting outside touched files.

## Testing Guidelines
- Framework: `pytest` with coverage (`--cov=gitfs`); markers: `slow`, `integration`.
- Test files: `tests/test_*.py`; structure tests near matching package modules.
- Run subset: `uv run pytest tests/test_router.py -k scenario`.
- Aim to maintain or improve coverage; include integration tests when touching FUSE interactions.

## Commit & Pull Request Guidelines
- Use Conventional Commits: `feat:`, `fix(scope):`, `docs:`, `chore:`, etc. (see `git log`).
- PRs must include: clear description, linked issues, test coverage, and docs updates if flags/CLI change.
- CI readiness: run `make format && make lint && make test` before pushing.

## Security & Configuration Tips
- Requires FUSE and `libgit2`; prefer the Vagrant box for reproducibility (`vagrant up`).
- For `allow_other=true`, ensure `/etc/fuse.conf` contains `user_allow_other`.
- Do not commit secrets or local paths; prefer environment-agnostic tests using `script/testenv`.

