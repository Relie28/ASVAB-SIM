#!/bin/bash
PORT=8765
DIR="$(cd "$(dirname "$0")" && pwd)"
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "unknown")

PYTHON_BIN=$(which python3)
/usr/libexec/ApplicationFirewall/socketfilterfw --add "$PYTHON_BIN" >/dev/null 2>&1
/usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp "$PYTHON_BIN" >/dev/null 2>&1

echo ""
echo "  Laptop:  http://localhost:${PORT}/?dev"
echo "  Phone:   http://${LOCAL_IP}:${PORT}/?dev"
echo "  (same WiFi required · Ctrl+C to stop)"
echo ""

open "http://localhost:${PORT}/?dev" 2>/dev/null &
python3 "${DIR}/server.py"
