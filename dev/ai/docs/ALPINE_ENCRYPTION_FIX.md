# Alpine Linux Encryption Fix

## Problem

On Alpine Linux deployments, ChatrixCD bots were showing "Encryption not enabled" errors despite having `vodozemac` installed. The root cause was that **matrix-nio 0.25.2 requires the `python-olm` package to be importable** to set its internal `ENCRYPTION_ENABLED` flag, even though `vodozemac` provides the actual encryption implementation.

## Root Cause Analysis

### Why Both Packages Are Needed

1. **matrix-nio Detection Logic** (`/src/nio/crypto/__init__.py`):
   ```python
   if package_installed("olm"):
       ENCRYPTION_ENABLED = True
   else:
       ENCRYPTION_ENABLED = False
   ```
   - matrix-nio checks for "olm" package name, NOT "vodozemac"
   - Without this flag set, encryption is completely disabled

2. **Actual Encryption**: 
   - vodozemac provides the superior Rust-based encryption backend
   - python-olm is only needed for the detection flag

3. **Alpine Package Management**:
   - Alpine venvs don't include system site-packages by default
   - Installing via pip on production Alpine is not available/desirable
   - System packages must be used instead

## Solution: Use System Packages

The fix involves using Alpine's `py3-matrix-nio` system package with all dependencies, rather than the venv-installed version.

### Step-by-Step Fix

#### 1. Install Required System Packages

```bash
# Install complete matrix-nio package with all dependencies
apk add py3-matrix-nio

# Install python-olm (for ENCRYPTION_ENABLED flag)
apk add py3-olm

# Install missing dependencies not included in py3-matrix-nio
apk add py3-peewee py3-cachetools py3-atomicwrites
```

#### 2. Enable System Site Packages in Venv

Edit `.venv/pyvenv.cfg`:
```ini
include-system-site-packages = true
```

Or via command:
```bash
sed -i 's/include-system-site-packages = false/include-system-site-packages = true/' .venv/pyvenv.cfg
```

#### 3. Remove Venv's matrix-nio

The venv's matrix-nio takes precedence over system packages, so remove it:
```bash
rm -rf .venv/lib/python3.12/site-packages/nio*
```

#### 4. Restart Bot

```bash
killall -9 chatrixcd
cd /home/chatrix/ChatrixCD
nohup .venv/bin/chatrixcd -L > chatrix.log 2>&1 &
```

### Complete Deployment Script

```bash
#!/bin/bash
# Alpine Linux Encryption Fix Deployment Script

set -e

echo "Installing system packages..."
apk add py3-matrix-nio py3-olm py3-peewee py3-cachetools py3-atomicwrites

echo "Enabling system site packages in venv..."
sed -i 's/include-system-site-packages = false/include-system-site-packages = true/' /home/chatrix/ChatrixCD/.venv/pyvenv.cfg

echo "Removing venv matrix-nio to use system package..."
rm -rf /home/chatrix/ChatrixCD/.venv/lib/python3.12/site-packages/nio*

echo "Restarting bot..."
su - chatrix -c 'killall -9 chatrixcd 2>/dev/null; cd /home/chatrix/ChatrixCD && nohup .venv/bin/chatrixcd -L > chatrix.log 2>&1 &'

sleep 5

echo "Checking encryption status..."
cat /home/chatrix/ChatrixCD/chatrix.log | sed 's/\x1b\[[0-9;]*m//g' | grep -E '(Encryption|Starting)' | tail -10

echo "Done! Bot should now have encryption enabled."
```

## Verification

After applying the fix, check logs for these indicators:

### Success Indicators ✅
```
INFO - Encryption enabled with vodozemac-python
INFO - Starting ChatrixCD bot...
INFO - Encryption store loaded successfully
```

### Expected Warnings (Not Errors!) ⚠️
```
WARNING - Error decrypting megolm event, no session found with session id...
```
- These are **expected** for old messages sent before the bot joined
- The bot will request keys and decrypt future messages

### Failure Indicators ❌
```
WARNING - Encryption not enabled, skipping encryption setup
WARNING - Encryption support is NOT available - olm not initialized
```
- If you see these, the fix was not applied correctly

## Why Previous Approaches Failed

### Attempt 1: Install python-olm via pip
- **Problem**: Remote Alpine venvs don't have pip/uv installed
- **Result**: Cannot install packages into venv

### Attempt 2: Symlink Individual Packages
- **Problem**: python-olm has many dependencies (cffi, cachetools, atomicwrites, peewee)
- **Result**: Cascading dependency errors, too complex to maintain

### Attempt 3: Install Only py3-olm
- **Problem**: System packages not visible to venv by default
- **Result**: `ModuleNotFoundError: No module named 'olm'`

### Attempt 4: Enable system-site-packages + Install py3-olm
- **Problem**: Venv's matrix-nio still used instead of system's
- **Result**: System python-olm not imported by venv's matrix-nio

### Final Solution: System py3-matrix-nio + Remove Venv Version
- **Success**: All dependencies included, encryption works!

## Package Versions

- **Alpine Linux**: 3.22+
- **Python**: 3.12+
- **py3-matrix-nio**: 0.25.2-r0
- **py3-olm**: 3.2.16-r1
- **py3-peewee**: 3.18.1-r0
- **py3-cachetools**: 5.5.2-r0
- **py3-atomicwrites**: 1.4.1-r3

## Future Considerations

### Option 1: Switch to vodozemac-only when matrix-nio supports it
- Monitor matrix-nio releases for vodozemac-only support
- May require matrix-nio >= 0.26.0 (not yet released as of Dec 2025)

### Option 2: Document Alpine-specific deployment
- Add Alpine deployment guide to main documentation
- Include this fix as standard procedure
- Create Alpine Dockerfile with proper package installation

### Option 3: System-wide Python packages
- Consider using system Python entirely instead of venv
- Simplifies dependency management on Alpine
- Trade-off: Less isolation between projects

## Related Documentation

- [INSTALL.md](../INSTALL.md) - Installation guide (should be updated)
- [DEPLOYMENT.md](../DEPLOYMENT.md) - Deployment instructions
- [requirements.txt](../requirements.txt) - Python dependencies (includes python-olm now)

## Changelog Entry

```markdown
### Fixed
- Alpine Linux encryption initialization by using system py3-matrix-nio package
- Added py3-olm system package requirement for Alpine deployments
- Enabled system-site-packages in venv to access Alpine system packages
- Removed venv matrix-nio to prevent conflict with system package
```

## Technical Details

### Why matrix-nio Checks for "olm"

From `matrix-nio/src/nio/crypto/__init__.py`:
```python
def package_installed(package_name: str) -> bool:
    """Check if a package is installed."""
    try:
        return importlib.util.find_spec(package_name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False

if package_installed("olm"):
    from .olm_machine import Olm
    ENCRYPTION_ENABLED = True
else:
    ENCRYPTION_ENABLED = False
```

This check happens at **import time**, before any client code runs. If `olm` is not importable, `ENCRYPTION_ENABLED` is set to `False` globally.

### AsyncClient Behavior

From `matrix-nio/src/nio/client/base_client.py`:
```python
@dataclass
class AsyncClientConfig:
    encryption_enabled: bool = True
    
    def __post_init__(self):
        if not ENCRYPTION_ENABLED and self.encryption_enabled:
            raise ImportWarning(
                "Encryption is enabled in the client configuration but "
                "dependencies for E2E encryption aren't installed."
            )
```

Our bot catches this `ImportWarning` and disables encryption:
```python
try:
    config_obj = AsyncClientConfig(encryption_enabled=encryption_available)
except ImportWarning:
    logger.warning("AsyncClient could not enable encryption...")
    config_obj = AsyncClientConfig(encryption_enabled=False)
```

### Why System Packages Work

Alpine's `py3-matrix-nio` package includes:
- matrix-nio Python code
- All required dependencies as Alpine packages
- Proper dependency resolution via apk

When venv has `include-system-site-packages = true`:
- Python looks in venv site-packages first
- Falls back to system site-packages
- By removing venv's nio, system's nio is used
- System's nio finds system's olm → encryption enabled!

## Troubleshooting

### Bot Still Shows "Encryption not enabled"

1. **Check system packages installed**:
   ```bash
   apk list | grep -E '(py3-matrix-nio|py3-olm|py3-peewee)'
   ```

2. **Verify venv configuration**:
   ```bash
   cat .venv/pyvenv.cfg | grep include-system-site-packages
   ```
   Should show `true`

3. **Confirm venv matrix-nio removed**:
   ```bash
   ls .venv/lib/python3.12/site-packages/ | grep nio
   ```
   Should show no results

4. **Test olm import from venv**:
   ```bash
   .venv/bin/python -c "import olm; print('Success')"
   ```

### ImportError for Other Packages

If you see errors like `ModuleNotFoundError: No module named 'X'`:

1. Search for Alpine package:
   ```bash
   apk search py3-X
   ```

2. Install if available:
   ```bash
   apk add py3-X
   ```

3. If not available, may need to install via pip with build dependencies

### Deployment to Non-Alpine Systems

This fix is **Alpine-specific**. On other systems:
- Standard pip installation works fine
- `pip install matrix-nio python-olm vodozemac` installs everything
- No special configuration needed

## Credits

This fix was discovered through systematic debugging:
1. Identified `client.olm is None` in production logs
2. Traced to matrix-nio's `ENCRYPTION_ENABLED` flag
3. Found package detection logic in matrix-nio source
4. Tested various approaches (pip, symlinks, system packages)
5. Discovered venv precedence issue
6. Final solution: system packages + venv matrix-nio removal

Date: 2025-12-15
Issue: Production encryption failures on Alpine Linux
Resolution: Use Alpine system packages for matrix-nio
