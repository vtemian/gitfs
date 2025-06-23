# Refactor to Python 3.11

Refactor $ARGUMENTS from Python 2.7/3.x to modern Python 3.11.

## Workflow:

1. **Analysis Phase**:
   - Check Python version constraints in setup.py, Makefile
   - Search for Python 2 patterns: `print` statements, `unicode`, old imports
   - Identify outdated dependencies in requirements.txt

2. **Code Updates**:
   - Update string/unicode handling
   - Fix imports (`ConfigParser` → `configparser`, etc.)
   - Update exception syntax (`except E, e:` → `except E as e:`)
   - Replace deprecated methods and patterns

3. **Dependency Upgrade**:
   - Update to Python 3.11 compatible versions
   - Address security vulnerabilities
   - Test each upgrade incrementally

4. **Testing & Validation**:
   - Run full test suite: `make test`
   - Test FUSE mounting functionality
   - Verify git operations work correctly
   - Check performance hasn't degraded

5. **Documentation**:
   - Update README.md, setup.py classifiers
   - Document breaking changes in CHANGELOG.txt
   - Update development docs

Target: $ARGUMENTS (e.g., "gitfs/worker module", "entire codebase", "test suite")