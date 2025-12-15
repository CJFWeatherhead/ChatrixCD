# Remote Machine Setup Instructions

## For ChatrixCD Integration Tests with Encryption Support

After pulling the latest code changes, remote ChatrixCD instances automatically get the updated dependencies including python-olm. However, you should verify the installation worked correctly.

## Quick Verification (< 1 minute)

Run these commands on each remote machine:

```bash
# SSH to remote machine
ssh root@<remote_host>

# Verify python-olm is installed
python3 -c "import olm; print(f'python-olm version: {olm.__version__}')"
# Expected output: python-olm version: 3.2.0 (or newer)

# Verify matrix-nio version
python3 -c "import nio; print(f'matrix-nio version: {nio.__version__}')"
# Expected output: matrix-nio version: 0.26.0 (or newer)

# Check encryption is enabled
python3 -c "from nio.crypto import ENCRYPTION_ENABLED; print(f'Encryption enabled: {ENCRYPTION_ENABLED}')"
# Expected output: Encryption enabled: True

# Exit
exit
```

## If python-olm is Not Installed

On the remote machine:

```bash
cd /home/chatrix/ChatrixCD

# Activate virtual environment
source .venv/bin/activate

# Install python-olm manually
pip install python-olm>=3.2.0

# Verify installation
python -c "import olm; print(olm.__version__)"
```

## What the Integration Test Runner Does Automatically

The [tests/run_integration_tests.py](../tests/run_integration_tests.py) script automatically:

1. **Updates code** via git pull
2. **Creates/updates virtualenv** with uv
3. **Installs dependencies** including python-olm via: `uv pip install -r requirements.txt`
4. **Starts bot with encryption** using `-L` flag (log mode with auto-verification)

So if you just run the integration test runner, everything should be installed automatically.

## Verifying Encryption Works

After the bot starts, check the logs for these messages:

```bash
# SSH to remote machine
ssh root@<remote_host>

# Check bot logs
tail -f /home/chatrix/ChatrixCD/chatrix.log | grep -E "Encryption|python-olm|store"
```

You should see:
```
INFO - Encryption enabled and dependencies available
INFO - Encryption store loaded successfully
```

## Running Integration Tests

Once python-olm is confirmed installed on all remote machines:

```bash
# From your local ChatrixCD directory
python tests/run_integration_tests.py tests/integration_config.json
```

Expected behavior:
1. Both bots start in log mode with auto-verification enabled
2. Test sends commands from Bot A to Bot B
3. Bot B responds with encrypted messages
4. Both bots auto-verify each other's devices
5. Encrypted messages flow freely between bots
6. Test checks that messages were received and decrypted correctly

## Troubleshooting

### Error: "ImportError: No module named 'olm'"

```bash
# On remote machine
cd /home/chatrix/ChatrixCD
source .venv/bin/activate
pip install python-olm>=3.2.0
```

### Error: "Encryption dependencies not properly detected"

This means ENCRYPTION_ENABLED is False. Check:

```bash
python3 << 'EOF'
import sys
print(f"Python: {sys.version}")

# Check if olm module can be imported
try:
    import olm
    print(f"✓ olm module found: {olm.__version__}")
except ImportError as e:
    print(f"✗ olm not found: {e}")

# Check matrix-nio's encryption detection
from nio._compat import package_installed
print(f"package_installed('olm'): {package_installed('olm')}")

# Check ENCRYPTION_ENABLED flag
from nio.crypto import ENCRYPTION_ENABLED
print(f"ENCRYPTION_ENABLED: {ENCRYPTION_ENABLED}")

# If olm is installed but ENCRYPTION_ENABLED is False, try reinitializing
if not ENCRYPTION_ENABLED:
    print("\nTrying to fix by reloading nio modules...")
    import importlib
    import nio
    importlib.reload(nio)
    from nio.crypto import ENCRYPTION_ENABLED as ENC_ENABLED
    print(f"After reload: ENCRYPTION_ENABLED = {ENC_ENABLED}")
EOF
```

### Bot still can't decrypt messages

Check that:
1. Both bots are in the same encrypted room
2. Room encryption is properly configured (should be m.megolm.v1.aes-sha2)
3. Bot has fully synced before messages are sent
4. Bot logs show auto-verification messages

## Machine-Specific Notes

### For IPv6-only machines (like our integration test hosts)

The bots should work fine with IPv6 addresses. If you have Matrix connectivity issues:

```bash
# Test Matrix homeserver connectivity
curl -6 https://<homeserver_host>/_matrix/client/versions

# If that fails, check IPv6 DNS resolution
ping6 <homeserver_host>
```

### For Alpine Linux systems

Alpine uses musl libc, which is compatible with python-olm. However:

```bash
# Make sure build tools are installed for building python-olm wheels
apk add python3-dev gcc musl-dev libffi-dev

# Then install python-olm
pip install python-olm>=3.2.0
```

## Questions?

If you encounter any issues:

1. Check [ENCRYPTION_FIXES_SUMMARY.md](ENCRYPTION_FIXES_SUMMARY.md) for detailed explanation of what was fixed
2. Check [INTEGRATION_TEST_ENCRYPTION_SETUP.md](INTEGRATION_TEST_ENCRYPTION_SETUP.md) for encryption flow details
3. Review bot logs for specific error messages
4. Run the verification commands above and check all are passing

## What Changed

- **python-olm**: Primary encryption backend (was vodozemac)
- **matrix-nio**: Updated to 0.26.0 (was 0.24.0)
- **Bot initialization**: Now explicitly enables encryption via AsyncClientConfig
- **Auto-verification**: Enabled in log mode (integration test mode) for automatic device trust

All changes are backward compatible and require no configuration changes.
