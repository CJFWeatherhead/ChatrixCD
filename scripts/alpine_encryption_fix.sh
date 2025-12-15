#!/bin/bash
# Alpine Linux Encryption Fix Deployment Script
# Fixes encryption initialization on Alpine Linux by using system packages
# See docs/ALPINE_ENCRYPTION_FIX.md for detailed explanation

set -e

CHATRIX_HOME="/home/chatrix/ChatrixCD"
CHATRIX_USER="chatrix"

echo "=== ChatrixCD Alpine Linux Encryption Fix ==="
echo ""

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: This script must be run as root"
    exit 1
fi

# Check if running on Alpine
if [ ! -f /etc/alpine-release ]; then
    echo "WARNING: This script is designed for Alpine Linux"
    echo "Are you sure you want to continue? (y/N)"
    read -r response
    if [ "$response" != "y" ] && [ "$response" != "Y" ]; then
        echo "Aborting."
        exit 0
    fi
fi

echo "Step 1: Installing system packages..."
apk add py3-matrix-nio py3-olm py3-peewee py3-cachetools py3-atomicwrites
echo "✓ System packages installed"
echo ""

echo "Step 2: Enabling system site packages in venv..."
if [ -f "$CHATRIX_HOME/.venv/pyvenv.cfg" ]; then
    sed -i 's/include-system-site-packages = false/include-system-site-packages = true/' "$CHATRIX_HOME/.venv/pyvenv.cfg"
    echo "✓ System site packages enabled"
else
    echo "WARNING: venv config not found at $CHATRIX_HOME/.venv/pyvenv.cfg"
fi
echo ""

echo "Step 3: Removing venv matrix-nio to use system package..."
if [ -d "$CHATRIX_HOME/.venv/lib/python3.12/site-packages" ]; then
    rm -rf "$CHATRIX_HOME/.venv/lib/python3.12/site-packages/nio"* 2>/dev/null || true
    echo "✓ Removed venv matrix-nio"
else
    echo "WARNING: venv site-packages not found"
fi
echo ""

echo "Step 4: Verifying olm import..."
if su - "$CHATRIX_USER" -c "cd $CHATRIX_HOME && .venv/bin/python -c 'import olm; print(\"olm imported successfully\")'" 2>&1 | grep -q "successfully"; then
    echo "✓ olm module is importable"
else
    echo "ERROR: olm module cannot be imported"
    echo "Check that system packages are installed correctly"
    exit 1
fi
echo ""

echo "Step 5: Restarting bot..."
su - "$CHATRIX_USER" -c "killall -9 chatrixcd 2>/dev/null || true"
sleep 2
su - "$CHATRIX_USER" -c "cd $CHATRIX_HOME && nohup .venv/bin/chatrixcd -L > chatrix.log 2>&1 &"
echo "✓ Bot restarted"
echo ""

echo "Step 6: Checking encryption status..."
sleep 6
if [ -f "$CHATRIX_HOME/chatrix.log" ]; then
    echo ""
    echo "=== Encryption Status ==="
    cat "$CHATRIX_HOME/chatrix.log" | sed 's/\x1b\[[0-9;]*m//g' | grep -E '(Encryption|olm|vodozemac|Starting)' | tail -10
    echo ""
    
    if cat "$CHATRIX_HOME/chatrix.log" | grep -q "Encryption enabled with vodozemac"; then
        echo "✓✓✓ SUCCESS! Encryption is enabled ✓✓✓"
        echo ""
        echo "Expected warnings for old messages:"
        echo "  'Error decrypting megolm event' - Normal for messages sent before bot joined"
        echo ""
        exit 0
    else
        echo "⚠ WARNING: Bot started but encryption status unclear"
        echo "Check logs manually: tail -f $CHATRIX_HOME/chatrix.log"
        exit 1
    fi
else
    echo "ERROR: Log file not found at $CHATRIX_HOME/chatrix.log"
    exit 1
fi
