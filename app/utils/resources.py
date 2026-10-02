"""Locate bundled, read-only application resources independently of the working directory."""

import sys
from pathlib import Path


def resource_path(relative_path: str | Path) -> Path:
    """Resolve a resource from the source root or PyInstaller's bundle directory.

    Use only for static application files, never for projects or generated reports.
    This function does not create files or directories.
    """
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return root / relative_path
