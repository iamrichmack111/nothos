#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PYTHON_BIN="${PYTHON_BIN:-python3}"
export OLLAMA_URL="${OLLAMA_URL:-${OLLAMA_HOST:-http://localhost:11434}}"
export OLLAMA_HOST="${OLLAMA_HOST:-$OLLAMA_URL}"
export NOTHOS_EMBED_MODEL="${NOTHOS_EMBED_MODEL:-embeddinggemma-2}"
export NOTHOS_CHAT_MODEL="${NOTHOS_CHAT_MODEL:-gemma3:4b}"
command -v ollama >/dev/null || { echo 'Install Ollama: https://ollama.com/download' >&2;exit 1; }
"$PYTHON_BIN" -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
printf '\nPulling embedding model on %s ...\n' "$OLLAMA_HOST"
ollama pull "$NOTHOS_EMBED_MODEL"
if [[ "${NOTHOS_SKIP_CHAT_PULL:-0}" != "1" ]]; then
  echo "Pulling chat model: $NOTHOS_CHAT_MODEL"
  ollama pull "$NOTHOS_CHAT_MODEL"
fi
python nothos.py doctor
python nothos.py ingest
printf '\nReady! Try: python nothos.py ask "Which Sirens were associated with Persephone?"\n'
