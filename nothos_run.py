import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))

from nothos_theme import banner

def main():
    banner()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python nothos_run.py ask 'Who was Hermes?'")
        print("  python nothos_run.py search 'Apollo'")
        print("  python nothos_run.py lsj 'ἀποφοιβάζω'")
        print("  python nothos_run.py semantic 'divine inspiration'")
        return

    command = sys.argv[1]
    args = sys.argv[2:]

    if command == "lsj":
        script = ROOT / "tools" / "clean_lsj.py"
    elif command == "semantic":
        script = ROOT / "tools" / "search_lsj.py"
    else:
        script = ROOT / "nothos.py"
        args = [command] + args

    env = __import__("os").environ.copy()
    env["NOTHOS_NO_BANNER"] = "1"

    result = subprocess.run(
        [sys.executable, str(script), *args],
        cwd=ROOT,
        env=env,
    )
    raise SystemExit(result.returncode)

if __name__ == "__main__":
    main()
