# GitFS Refactoring Commands

Streamlined slash commands for refactoring GitFS from Python 2.7/3.x to Python 3.11.

## Available Commands

- **`/refactor-to-python3 [target]`** - Refactor code to Python 3.11
- **`/refactor-legacy-code [module]`** - Modernize legacy patterns in specific modules  
- **`/upgrade-dependencies [focus]`** - Upgrade dependencies with security focus
- **`/validate-refactoring [area]`** - Validate functionality after changes

## Quick Start

```bash
# Refactor a specific module
/refactor-to-python3 "gitfs/worker module"

# Upgrade dependencies
/upgrade-dependencies "security vulnerabilities"

# Refactor legacy patterns
/refactor-legacy-code "gitfs/cache"

# Validate changes
/validate-refactoring "FUSE operations"
```

## Typical Workflow

1. **Start small**: Pick a module and use `/refactor-to-python3`
2. **Fix dependencies**: Use `/upgrade-dependencies` when needed
3. **Validate often**: Run `/validate-refactoring` after changes
4. **Test thoroughly**: Always run `make test` before committing

## Parameters

All commands accept `$ARGUMENTS` to target specific areas:
- Module names: `gitfs/worker`, `gitfs/cache`, `gitfs/views`
- Scopes: `entire codebase`, `test suite`, `core modules`
- Focus areas: `security vulnerabilities`, `Python 3.11 compatibility`

These commands work with the project's development workflow defined in `CLAUDE.md`.