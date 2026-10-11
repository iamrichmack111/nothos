#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "NOTHOS v6 — macOS/Linux Installer"

PYTHON="${PYTHON:-python3}"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "Python 3.11+ is required."
    exit 1
fi

if ! command -v chafa >/dev/null 2>&1; then
    case "$(uname -s)" in
        Darwin)
            echo "Install Medusa artwork support:"
            echo "  brew install chafa figlet"
            ;;
        Linux)
            if command -v apt-get >/dev/null; then
                echo "Install artwork support:"
                echo "  sudo apt install chafa figlet"
            elif command -v dnf >/dev/null; then
                echo "Install artwork support:"
                echo "  sudo dnf install chafa figlet"
            elif command -v pacman >/dev/null; then
                echo "Install artwork support:"
                echo "  sudo pacman -S chafa figlet"
            fi
            ;;
    esac
fi

"$PYTHON" -m venv .venv
. .venv/bin/activate

python -m pip install -e .

nothos doctor

echo
echo "NOTHOS installation complete."
echo "Activate: source .venv/bin/activate"
echo "Help:     nothos --help"
echo "API:      nothos serve --port 8790"
