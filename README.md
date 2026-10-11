# 🏛️ NOTHOS

**Ancient Greek Philology, Mythology & Evidence-Aware Research CLI**

NOTHOS is a local-first research environment combining the
Liddell–Scott–Jones Greek-English Lexicon (LSJ), semantic search,
Ollama language models, and evidence-aware retrieval-augmented generation.

## Features

- 🇬🇷 Ancient Greek lexical research
- 📖 LSJ dictionary integration
- 🔮 Semantic search with local embeddings
- 🧠 Ollama-powered explanations
- 📜 Ancient-source abbreviation extraction
- 🔒 Dictionary-attested vocabulary reporting
- 🏛️ Mythology and ritual terminology research
- 🎨 ANSI-colored Greek and English output
- 🐍 Medusa-themed terminal interface
- 🛡️ Separation of LSJ evidence from AI interpretation
- 🔐 Local-first operation

## Research Pipeline

1. Receive research query
2. Retrieve semantically related LSJ entries
3. Display original dictionary evidence
4. Extract Greek vocabulary and source abbreviations
5. Generate optional Ollama interpretation
6. Separate dictionary evidence from unverified AI claims

## Requirements

- Python 3
- Ollama
- LSJ SQLite dictionary
- Local embedding database
- Compatible Ollama embedding and generation models

## Example

    python tools/lsj_rag.py "mystery" --top-k 5

## Research Integrity

NOTHOS distinguishes dictionary evidence from AI-generated interpretation.

Ancient-source references are extracted from LSJ entries.
Their original passages are not independently verified.

AI interpretations may contain inaccuracies and should be checked
against the original Greek texts.

## Project Status

**NOTHOS v5 — Evidence-Aware RAG**

Active development.
