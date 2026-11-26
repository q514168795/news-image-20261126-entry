# SPDX-License-Identifier: MIT
"""Entrypoint for make.fun news-image-20261126.

Copies the pre-rendered deterministic front-page image (entry.png) into
$MAKEFUN_OUTPUT_DIR/entry.png with zero network access.
"""

import os
import pathlib
import sys


def main() -> int:
    root = pathlib.Path(__file__).resolve().parent
    src = root / "entry.png"
    if not src.is_file():
        raise FileNotFoundError(f"Missing rendered front page: {src}")
    data = src.read_bytes()
    if len(data) > 1048576 or not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError(f"Invalid PNG payload ({len(data)} bytes)")
    out_dir = pathlib.Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    dst = out_dir / "entry.png"
    dst.write_bytes(data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
