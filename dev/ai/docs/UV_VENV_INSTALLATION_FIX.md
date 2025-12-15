# UV VENV Installation Fix

## Issue Summary

**Date**: December 15, 2025  
**Context**: Integration test failures due to missing dependencies on remote machines

## Problem

When using `uv venv` to create virtual environments and `uv pip install` without explicit Python paths, packages were not being installed into the virtual environment correctly. This caused the ChatrixCD bot to fail with `ModuleNotFoundError: No module named 'nio'` despite successful installation commands.

### Root Cause

`uv venv` creates lightweight virtual environments using **symlinks** to the system Python instead of copying the Python interpreter. When using:

```bash
uv pip install --python .venv/bin/python -r requirements.txt
```

Without absolute paths, `uv` would follow the symlink and install packages to the **system Python** location instead of the virtual environment's `site-packages`. This meant:

1. ✅ Installation command succeeded
2. ✅ `uv pip list` showed packages installed
3. ❌ But `.venv/bin/python -c "import nio"` failed because packages weren't in the venv

### Manifestation

```bash
$ .venv/bin/python -c "import nio"
ModuleNotFoundError: No module named 'nio'

$ uv pip install --python .venv/bin/python matrix-nio
Audited 2 packages in 3ms  # Says already installed!

$ ls -la .venv/bin/python
lrwxrwxrwx ... .venv/bin/python -> /usr/bin/python3  # Symlink!
```

## Solution

Use **absolute paths** when specifying the Python interpreter to `uv pip install`:

### ✅ Correct Usage

```bash
# Method 1: Use absolute path (RECOMMENDED)
uv venv
uv pip install --python /full/path/to/project/.venv/bin/python -r requirements.txt
uv pip install --python /full/path/to/project/.venv/bin/python -e .

# Method 2: Activate venv and use pip directly
uv venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### ❌ Incorrect Usage

```bash
# These may install to system Python instead of venv!
uv venv
uv pip install -r requirements.txt  # No --python flag
uv pip install --python .venv/bin/python -r requirements.txt  # Relative path
```

## Files Updated

Updated all installation documentation to use correct `uv` commands:

1. **CONTRIBUTING.md** - Development setup instructions
2. **.github/copilot-instructions.md** - AI assistant guidance
3. **tests/README_integration.md** - Integration test setup
4. **SECURITY.md** - Security update commands
5. **SUPPORT.md** - Troubleshooting dependency installation
6. **tests/run_integration_tests.py** - Integration test runner dependency installation

### Integration Test Runner Changes

In `tests/run_integration_tests.py`, the dependency installation was fixed:

```python
# OLD (broken):
deps_cmd = (
    f"su - {chatrix_user} -c '"
    f"cd {chatrix_dir} && "
    f"uv venv .venv && "
    f"uv pip install --python .venv/bin/python -r requirements.txt && "
    f"uv pip install --python .venv/bin/python -e .'"
)

# NEW (fixed):
# Remove old venv to avoid conflicts
venv_cmd = (
    f"su - {chatrix_user} -c '"
    f"cd {chatrix_dir} && "
    f"rm -rf .venv && "
    f"uv venv --python python3.12 .venv'"
)

# Install with absolute path
deps_cmd = (
    f"su - {chatrix_user} -c '"
    f"cd {chatrix_dir} && "
    f"uv pip install --python {chatrix_dir}/.venv/bin/python -r requirements.txt'"
)

# Install package separately
editable_cmd = (
    f"su - {chatrix_user} -c '"
    f"cd {chatrix_dir} && "
    f"uv pip install --python {chatrix_dir}/.venv/bin/python -e .'"
)
```

## Verification

After applying the fix, verify packages are in the venv:

```bash
# Should work without errors
.venv/bin/python -c "import nio; print(nio.__version__)"

# Should show packages installed in venv
.venv/bin/python -m pip list
```

## Best Practices

### For Development

1. **Always use absolute paths** with `--python` flag when using `uv pip install`
2. **Activate the venv** and use `pip` directly for simpler workflow
3. **Test imports** after installation to verify packages are accessible

### For CI/CD and Automation

1. **Use absolute paths** in all automated scripts
2. **Remove old venv** before creating new one to avoid conflicts: `rm -rf .venv`
3. **Specify Python version** explicitly: `uv venv --python python3.12`
4. **Verify installation** with test imports before running the application

### For Documentation

1. **Always show the `--python` flag** in code examples
2. **Provide both methods**: absolute path uv and activated venv pip
3. **Explain the reason**: helps users understand why absolute paths matter

## Related Issues

- **Integration Test Timeouts**: Bots failing to start due to missing dependencies
- **"ModuleNotFoundError" on Remote Machines**: Packages not actually installed in venv
- **"Audited X packages" but imports fail**: uv reporting success but packages not accessible

## References

- [uv Documentation](https://docs.astral.sh/uv/)
- [Integration Test Encryption Setup](INTEGRATION_TEST_ENCRYPTION_SETUP.md)
- [GitHub Copilot Instructions](.github/copilot-instructions.md)

## Lessons Learned

1. **Symlink-based venvs can be tricky**: Tools like `uv` optimize by using symlinks, but this requires careful path handling
2. **Always test in target environment**: What works locally may fail in production/CI due to path differences
3. **Absolute paths are safer**: When in doubt, use absolute paths for critical operations
4. **Document tool-specific quirks**: Not all virtual environment tools behave identically
5. **Verify, don't assume**: Always verify packages are actually importable after installation
