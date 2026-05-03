#!/usr/bin/env python3
"""Verify the extension ID derived from manifest's `key` matches the
allowed_origins entry in the native messaging host manifest."""

import base64
import hashlib
import json
import sys
from pathlib import Path


def derive_id(pubkey_b64: str) -> str:
    der = base64.b64decode(pubkey_b64)
    digest = hashlib.sha256(der).digest()[:16]
    # Chrome maps each hex nibble (0-f) to letters a-p.
    return "".join(chr(ord("a") + b) for nibble in digest.hex() for b in [int(nibble, 16)])


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    ext_manifest = json.loads((root / "extension" / "manifest.json").read_text())
    host_manifest = json.loads((root / "com.x.photosaver.json").read_text())
    install_sh = (root / "install.sh").read_text()

    key = ext_manifest.get("key")
    if not key:
        print("FAIL: extension/manifest.json has no `key` field", file=sys.stderr)
        return 1

    derived = derive_id(key)
    expected_origin = f"chrome-extension://{derived}/"

    fail = False
    if expected_origin not in host_manifest.get("allowed_origins", []):
        print("FAIL: host manifest allowed_origins does not contain derived ID")
        print(f"  derived: {expected_origin}")
        print(f"  actual:  {host_manifest.get('allowed_origins')}")
        fail = True

    if derived not in install_sh:
        print("FAIL: install.sh does not embed derived extension ID")
        print(f"  derived: {derived}")
        fail = True

    if fail:
        return 1
    print(f"OK   extension ID = {derived} (consistent across manifest, host, install.sh)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
