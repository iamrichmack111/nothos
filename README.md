# NOTHOS v6 — Medusa Edition

Ancient Greek philology, mythology, semantic search, and evidence-aware
research powered by LSJ dictionaries and local Ollama models.

## Features

- Ancient Greek LSJ semantic search
- Greek lemma definitions and lexical evidence
- Ollama-powered research explanations
- Mythology knowledge graph research
- JSON, Markdown, HTML, and plain-text exports
- FastAPI REST API
- Interactive OpenAPI documentation
- Cross-platform command-line interface
- Medusa terminal artwork
- Installation diagnostics

## Requirements

Python 3.11 or newer, subject to dependency compatibility.

Python dependencies:

- NumPy
- Requests
- FastAPI
- Uvicorn

External dependencies:

- Ollama for embeddings and AI explanations
- Chafa for Medusa image rendering (optional)
- FIGlet for terminal typography (optional)

Python dependencies are defined in `pyproject.toml` and
`requirements.txt`.

## Installation

### macOS

    brew install python chafa figlet
    ./install.sh
    source .venv/bin/activate
    nothos doctor

### Ubuntu / Debian / Pop!_OS

    sudo apt update
    sudo apt install -y python3 python3-venv python3-pip chafa figlet
    ./install.sh
    source .venv/bin/activate
    nothos doctor

### Fedora

    sudo dnf install -y python3 python3-pip chafa figlet
    ./install.sh
    source .venv/bin/activate
    nothos doctor

### Arch Linux

    sudo pacman -S --needed python python-pip chafa figlet
    ./install.sh
    source .venv/bin/activate
    nothos doctor

### Windows PowerShell

Install Python 3.11 or newer, then run:

    .\install.ps1
    .\.venv\Scripts\nothos.exe doctor

Windows Terminal is recommended for Unicode and ANSI support.

The ASCII banner works without Chafa.

## Ollama

Install Ollama separately.

Default models:

- Embeddings: `embeddinggemma-2`
- Chat: `gemma3:4b`

Download the models if available in your Ollama installation:

    ollama pull embeddinggemma-2
    ollama pull gemma3:4b

Check the configured model names before downloading.

Environment variables:

| Variable | Default | Purpose |
|---|---|---|
| OLLAMA_URL | http://localhost:11434 | Ollama server |
| NOTHOS_EMBED_MODEL | embeddinggemma-2 | Embedding model |
| NOTHOS_CHAT_MODEL | gemma3:4b | Mythology chat model |
| NOTHOS_EXPLAIN_MODEL | gemma3:4b | LSJ explanation model |
| NOTHOS_NO_BANNER | unset | Disable original banner |
| NO_COLOR | unset | Disable ANSI colors |

Use the same embedding model that created your existing vector database.

## Command-line interface

Display help:

    nothos --help
    nothos research --help
    nothos serve --help

Research a Greek lemma:

    nothos research "μυστήριον"

Retrieve LSJ evidence without AI:

    nothos research "μυστήριον" --no-ai

Increase semantic results:

    nothos research "Hermes" --top-k 20

Research mythology:

    nothos research "Who was Hermes?" --engine mythology

## Research flags

| Flag | Purpose |
|---|---|
| --top-k N | Number of retrieved results |
| --engine lsj | LSJ research |
| --engine mythology | Mythology research |
| --no-ai | Retrieve LSJ evidence without AI |
| --format text | Plain-text output |
| --format json | JSON output |
| --format markdown | Markdown output |
| --format html | HTML output |
| -o, --output PATH | Save to a file |
| --banner auto | Automatic banner |
| --banner full | Full Medusa banner |
| --banner compact | Compact banner |
| --banner ascii | ASCII-only banner |
| --banner none | Suppress banner |

## Export examples

JSON:

    nothos research "μυστήριον" --no-ai --format json --output reports/mystery.json

Markdown:

    nothos research "Hermes" --format markdown --output reports/hermes.md

HTML:

    nothos research "Galen" --format html --output reports/galen.html

Text:

    nothos research "Apollo" --format text --output reports/apollo.txt

AI reports currently contain captured research text.
No-AI LSJ searches return structured lexical results.

## Medusa banner

The original banner renderer is preserved in
`tools/nothos_theme.py`.

Its image is located at `assets/medusa.png`.

Commands:

    nothos banner
    nothos banner --style full
    nothos banner --style compact
    nothos banner --style ascii

Chafa renders the image when available in an interactive terminal.
Otherwise NOTHOS uses its text fallback.

## REST API

Start the server:

    nothos serve --host 127.0.0.1 --port 8790

Local API documentation:

    http://127.0.0.1:8790/docs

OpenAPI specification:

    http://127.0.0.1:8790/openapi.json

### Health

    curl http://127.0.0.1:8790/health

### LSJ search

    curl -G http://127.0.0.1:8790/api/v1/search --data-urlencode "q=μυστήριον" --data-urlencode "top_k=5"

### AI research

    curl -X POST http://127.0.0.1:8790/api/v1/research -H "Content-Type: application/json" -d '{"query":"Hermes","top_k":5,"ai":true,"engine":"lsj"}'

### API endpoints

| Method | Path | Description |
|---|---|---|
| GET | /health | Health check |
| GET | /api/v1/search | Semantic LSJ search |
| POST | /api/v1/research | AI or non-AI research |
| GET | /docs | Interactive documentation |
| GET | /openapi.json | OpenAPI specification |

## Security

The REST API has no authentication.

Keep it bound to `127.0.0.1` unless you implement
authentication and additional security controls.

## Existing research engines

NOTHOS v6 preserves:

- `nothos.py`
- `nothos_run.py`
- `tools/lsj_rag.py`
- `tools/clean_lsj.py`
- `tools/search_lsj.py`
- `tools/nothos_theme.py`

The unified CLI is implemented in `nothos_cli/`.

## Databases

Existing LSJ databases:

- `data/dictionaries/lsj.sqlite3`
- `data/dictionaries/lsj_embeddings.sqlite3`

The v6 CLI and API do not require re-ingestion.

Do not interrupt active embedding jobs.

Do not publish SQLite databases, WAL files, or journal files
without checking redistribution rights.

## Tests

    python -m unittest discover -s tests -p 'test_v6_cli_api.py' -v
    python -m compileall -q nothos_cli

## Troubleshooting

### Medusa image does not display

Install Chafa and confirm that `assets/medusa.png` exists.

### Greek text appears incorrectly

Use a UTF-8 terminal and a font with Greek character support.

### Ollama connection fails

Confirm Ollama is running and the configured models exist.

### Exact lemma is missing from semantic results

Semantic search currently ranks by vector similarity.
Exact-lemma prioritization is a planned improvement.

### API connection refused

Start the server:

    nothos serve --port 8790

### Installation diagnostics

    nothos doctor

## Research limitations

Semantic similarity is not proof of lexical identity.

LSJ references are not independently verified quotations
from ancient manuscripts.

AI-generated explanations can contain errors and should
be checked against the underlying Greek evidence.

## License

No repository license has been declared.
Source code, dictionary data, and imported passages may
have different redistribution requirements.
