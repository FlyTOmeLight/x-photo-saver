#!/usr/bin/env python3
"""Validate a JSON file against a JSON Schema. Exits non-zero on failure."""

import json
import sys
from pathlib import Path

import jsonschema


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: validate.py <data.json> <schema.json>", file=sys.stderr)
        return 2
    data = json.loads(Path(sys.argv[1]).read_text())
    schema = json.loads(Path(sys.argv[2]).read_text())
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        print(f"FAIL {sys.argv[1]}: {e.message}")
        print(f"  at: {'/'.join(str(p) for p in e.absolute_path)}")
        return 1
    print(f"OK   {sys.argv[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
