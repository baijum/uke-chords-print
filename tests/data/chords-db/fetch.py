"""
Download the pinned chords-db ukulele data used by the test suite.

Fetches lib/ukulele.json and LICENSE from tombatossals/chords-db at the
commit recorded in README.md and checks the data file's SHA-256, so a
changed upstream file can't silently change what the tests check.
"""

from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

COMMIT = "df06fa7b425cf5fd29485ff6591236b3557e3fac"
BASE_URL = f"https://raw.githubusercontent.com/tombatossals/chords-db/{COMMIT}"
SHA256 = "233b7018ec35785a8bfa985bad90f4745cee04614c0fd1d5b819cff7406ec601"
HERE = Path(__file__).parent


def _download(path: str) -> bytes:
    """Fetch one file from the pinned commit."""
    with urllib.request.urlopen(f"{BASE_URL}/{path}", timeout=30) as resp:
        return resp.read()


def main() -> int:
    data = _download("lib/ukulele.json")
    digest = hashlib.sha256(data).hexdigest()
    if digest != SHA256:
        print(f"SHA-256 mismatch: expected {SHA256}, got {digest}",
              file=sys.stderr)
        return 1
    (HERE / "ukulele.json").write_bytes(data)
    (HERE / "LICENSE").write_bytes(_download("LICENSE"))
    print(f"Fetched chords-db {COMMIT[:7]} into {HERE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
