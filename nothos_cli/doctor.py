"""Installation and runtime diagnostics."""

import importlib.util
import os
import platform
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def doctor():
    print("\n🏛️ NOTHOS v6 — SYSTEM DIAGNOSTICS")
    print("=" * 55)
    print("Operating system:", platform.platform())
    print("Python:", sys.version.split()[0])
    print("Terminal encoding:", sys.stdout.encoding)
    print("Terminal type:", os.getenv("TERM", "unknown"))
    print("ANSI color:", "disabled" if "NO_COLOR" in os.environ else "auto")
    print()

    for name in ("chafa", "figlet", "ollama"):
        path = shutil.which(name)
        print(f"{name:12}", path or "NOT FOUND")

    print()
    for name in ("numpy", "requests", "fastapi", "uvicorn"):
        found = importlib.util.find_spec(name)
        print(f"{name:12}", "INSTALLED" if found else "MISSING")

    print()
    for name in (
        "assets/medusa.png",
        "data/dictionaries/lsj.sqlite3",
        "data/dictionaries/lsj_embeddings.sqlite3",
    ):
        path = ROOT / name
        print(
            f"{name:48}",
            "FOUND" if path.is_file() else "MISSING",
        )

    print("\nDiagnostics complete.")
