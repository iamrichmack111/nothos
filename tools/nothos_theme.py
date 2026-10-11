
import os
import sys
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEDUSA = ROOT / "assets" / "medusa.png"

def color(code):
    if sys.stdout.isatty() and os.environ.get("TERM") != "dumb" and "NO_COLOR" not in os.environ:
        return f"\033[{code}m"
    return ""

RESET = color("0")
GREEN = color("1;92")
YELLOW = color("1;93")
RED = color("1;91")
CYAN = color("1;96")
MAGENTA = color("1;95")
WHITE = color("1;97")

def paint(text, shade):
    return f"{shade}{text}{RESET}"

def heading(text):
    print(paint("═" * 65, CYAN))
    print(paint(f"  {text}", YELLOW))
    print(paint("═" * 65, CYAN))

def success(text):
    print(paint(f"✅ {text}", GREEN))

def warning(text):
    print(paint(f"⚠️ {text}", YELLOW))

def error(text):
    print(paint(f"❌ {text}", RED))

def banner():
    if os.environ.get("NOTHOS_NO_BANNER") == "1":
        return

    print()
    image = ROOT / "assets" / "medusa.png"
    chafa = shutil.which("chafa")

    if image.exists() and chafa and sys.stdout.isatty():
        try:
            subprocess.run(
                [chafa, "--size", "45x25", str(image)],
                timeout=10,
                check=False
            )
        except (OSError, subprocess.SubprocessError):
            pass
    else:
        print(paint("             🐍 MEDUSA 🐍", MAGENTA))

    print()
    print(paint("╔══════════════════════════════════════════════════════╗", CYAN))
    print(paint("║              🏛️  N O T H O S  🏛️                 ║", YELLOW))
    print(paint("╚══════════════════════════════════════════════════════╝", CYAN))
    print(paint("  ⚡ MYTHOLOGY   📖 PHILOLOGY   🏺 LEXICONS", GREEN))
    print(paint("  🔮 SEMANTIC SEARCH   🇬🇷 ANCIENT GREEK", MAGENTA))
    print(paint("  🧠 OLLAMA   📜 PRIMARY SOURCES   🔎 EVIDENCE", WHITE))
    print()
