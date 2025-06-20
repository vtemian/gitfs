# Upgrade Dependencies

Upgrade dependencies for $ARGUMENTS with security and compatibility focus.

## Workflow:

1. **Security Scan**:
   ```bash
   pip install pip-audit
   pip-audit
   ```

2. **Analyze Current Dependencies**:
   - Review requirements.txt and test_requirements.txt
   - Check which packages are outdated or unmaintained
   - Identify Python 3.11 compatibility issues

3. **Upgrade Strategy**:
   - Start with test dependencies (pytest, mock, etc.)
   - Upgrade utility libraries next
   - Save critical dependencies (pygit2, fusepy) for last
   - Test after each upgrade

4. **Critical Dependencies**:
   - **pygit2**: Check libgit2 compatibility
   - **fusepy**: Consider if alternatives needed
   - **raven**: Migrate to newer sentry-sdk if needed

5. **Validation**:
   - Run tests after each change: `make test`
   - Test FUSE mount operations
   - Verify no performance regression
   - Check for deprecation warnings

6. **Documentation**:
   - Update requirements files
   - Document any API changes
   - Note security fixes in CHANGELOG.txt

Target: $ARGUMENTS (e.g., "security vulnerabilities", "Python 3.11 compatibility", "all dependencies")