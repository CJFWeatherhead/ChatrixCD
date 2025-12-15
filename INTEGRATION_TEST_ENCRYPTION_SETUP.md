# Integration Test Encryption Setup Guide

## Overview

ChatrixCD integration tests verify end-to-end encrypted communication between bots in Matrix rooms. This document explains the encryption setup required for successful integration tests.

## Current Status

### ✅ Completed Fixes

1. **Encryption Dependencies** (Fixed in PR)
   - Updated `requirements.txt`: `matrix-nio>=0.26.0` + `python-olm>=3.2.0`
   - Removed incompatible `vodozemac` dependency (matrix-nio 0.26.0 only recognizes `python-olm`)
   - Updated `bot.py` to initialize `AsyncClient` with `AsyncClientConfig(encryption_enabled=True)`

2. **Bug Fixes**
   - Fixed `AttributeError` in `commands.py`: changed `user.displayname` → `user.display_name`
   - Fixed encryption store loading in `bot.py`: removed incorrect conditionals that prevented `load_store()` calls
   - Added encryption diagnostics logging to bot initialization

3. **Auto-Verification Framework**
   - Method `_auto_verify_sender_devices()` is implemented and active in `log` mode
   - Integration tests run with `-L` flag (log mode), so auto-verification is enabled
   - Auto-verification happens on `MegolmEvent` (encrypted message without key), allowing bots to start communicating

### ⏳ Requirements for Remote Machines

When integration tests run on remote machines, the following must be true:

1. **Python-olm Installed**
   ```bash
   pip install python-olm>=3.2.0
   ```
   - This is automatically installed when running `uv pip install -r requirements.txt`
   - Verified in `tests/run_integration_tests.py` line 227

2. **Bot Authentication**
   - Remote bots use OIDC authentication to Matrix homeserver
   - Each bot has its own device ID and encryption keys
   - Integration tests extract `access_token` from bot's session for test client authentication
   - This is a functional workaround; future refactoring should use native session extraction

3. **Encryption Store Directory**
   - Bots maintain encryption keys in `store/` directory
   - Directory created automatically by `bot.py` line 84
   - Persists across bot restarts for device continuity

## How Encryption Works in Integration Tests

### Setup Phase
1. Bot starts with `-L` flag (log mode, no TUI)
2. Bot loads stored encryption keys from `store/` directory
3. Bot initializes `AsyncClient` with `encryption_enabled=True`
4. Auto-verification is enabled (mode is 'log')

### Message Exchange Phase
1. **Bot A sends encrypted message to room**
   - Message encrypted with room's encryption algorithm (e.g., m.megolm.v1.aes-sha2)
   - Encrypted for all verified devices in the room

2. **Bot B receives encrypted message (without key)**
   - `MegolmEvent` callback triggered (encrypted but can't decrypt)
   - Bot B attempts to establish encryption:
     a. Query device keys from Bot A
     b. Claim one-time keys from Bot A
     c. **Auto-verify Bot A's devices** (because mode is 'log')
     d. Request room key from Bot A
   
3. **Bot A shares room key with Bot B**
   - Now Bot B can decrypt the message
   - Bot B decrypts and processes it normally

### Key Sharing
- Room keys are shared automatically by matrix-nio when:
  - A message is sent to encrypted room
  - Keys are requested by other devices
  - Device verification occurs
- This is Matrix protocol standard behavior

## Troubleshooting

### Symptom: Bots can't decrypt messages

**Check 1: Encryption enabled in AsyncClient**
- Look for log: `"Encryption enabled and dependencies available"`
- If not present, check that `python-olm` is installed: `python -c "import olm; print(olm.__version__)"`

**Check 2: Encryption store loaded**
- Look for logs: `"Encryption store loaded successfully"`
- If errors appear, check file permissions on `store/` directory
- Check that bot has logged in before first message

**Check 3: Device verification working**
- Look for logs: `"Auto-verified N device(s) for @user:server"`
- If not present, auto-verification may be disabled (only works in daemon/log/tui modes)
- Check that `load_store()` succeeded (store must exist)

**Check 4: Key claiming**
- Look for logs: `"Claiming one-time keys to establish encryption sessions"`
- If this fails, the remote bot may not be running or may have disconnected

### Symptom: "Cannot establish encryption: encryption store is not loaded"

**Solution:**
1. Ensure bot is fully synced before sending messages
2. Verify `user_id` is correctly set in both config and after `restore_login()`
3. Check that bot reached login state (look for `Successfully logged in` or `Successfully restored session`)

### Symptom: Device verification fails

**Solution:**
1. Check that both bots are in same room
2. Check that room is encrypted
3. Verify `self.client.device_store` is not None (requires successful sync)
4. Look for device store initialization logs

## Next Steps for Full Native OIDC Integration

Current approach uses access tokens extracted from bot sessions, which works but is not ideal. Future improvements:

1. Refactor `run_integration_tests.py` to extract session data from running bot processes
2. Use native OIDC session information instead of access_token workaround
3. Implement session refresh handling for long-running tests
4. This would fully decouple test authentication from bot configuration

## References

- [Matrix E2E Encryption Spec](https://spec.matrix.org/v1.10/client-server-api/#end-to-end-encryption)
- [matrix-nio Encryption Docs](https://matrix-nio.readthedocs.io/en/stable/encryption.html)
- [Python-olm Documentation](https://libolm.readthedocs.io/en/latest/)
