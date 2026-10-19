"""Permite `python -m prumo` (útil em Windows, onde o script pode não estar no PATH)."""

from __future__ import annotations

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
