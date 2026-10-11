"""Cross-platform Medusa banner with safe fallbacks."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE = ROOT / "assets" / "medusa.png"


def show_banner(style="auto"):
    if style == "none":
        return

    if style == "ascii":
        print("=== NOTHOS | ANCIENT GREEK RESEARCH ===")
        return

    if style == "compact":
        print("NOTHOS — ANCIENT GREEK RESEARCH")
        return

    if style not in ("auto", "full"):
        raise ValueError("Unknown banner style")

    # Reuse the original renderer; it already supports Chafa and fallback.
    sys.path.insert(0, str(ROOT / "tools"))
    from nothos_theme import banner

    banner()
