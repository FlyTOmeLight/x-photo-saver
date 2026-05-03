#!/bin/bash
# Install native messaging host into Chrome / Chrome Canary / Brave / Arc.
# Usage: ./install.sh [chrome|canary|brave|arc]  (default: chrome)
set -euo pipefail

BROWSER="${1:-chrome}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST_PY="$SCRIPT_DIR/host.py"
HOST_NAME="com.x.photosaver"
SUPPORT="$HOME/Library/Application Support"

case "$BROWSER" in
  chrome)  TARGET_DIR="$SUPPORT/Google/Chrome/NativeMessagingHosts" ;;
  canary)  TARGET_DIR="$SUPPORT/Google/Chrome Canary/NativeMessagingHosts" ;;
  brave)   TARGET_DIR="$SUPPORT/BraveSoftware/Brave-Browser/NativeMessagingHosts" ;;
  arc)     TARGET_DIR="$SUPPORT/Arc/User Data/NativeMessagingHosts" ;;
  *) echo "Unknown browser: $BROWSER. Use chrome|canary|brave|arc" >&2; exit 1 ;;
esac

if [[ ! -f "$HOST_PY" ]]; then
  echo "host.py not found at $HOST_PY" >&2; exit 1
fi

chmod +x "$HOST_PY"

if ! command -v exiftool >/dev/null 2>&1; then
  echo "exiftool missing — install with: brew install exiftool" >&2
fi

EXT_ID="cnimapbahdbbaifdpnaknbhmekjbgien"

mkdir -p "$TARGET_DIR"
cat > "$TARGET_DIR/$HOST_NAME.json" <<EOF
{
  "name": "$HOST_NAME",
  "description": "X / Xiaohongshu Photo Saver native host",
  "path": "$HOST_PY",
  "type": "stdio",
  "allowed_origins": [
    "chrome-extension://$EXT_ID/"
  ]
}
EOF

echo "Installed host manifest:"
echo "  $TARGET_DIR/$HOST_NAME.json"
echo
echo "Next:"
echo "  1. Open $BROWSER → chrome://extensions/"
echo "  2. Enable Developer mode"
echo "  3. Load unpacked → select: $SCRIPT_DIR/extension"
echo "  4. Confirm extension ID = $EXT_ID"
