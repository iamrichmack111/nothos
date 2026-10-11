# NOTHOS V7 — Medusa 45×25 / Text Corpus / Translation

Overlay onto your existing ~/Downloads/nothos_v5 folder. Keep your nothos.sqlite3 and .venv.

## Installation

```bash
cd ~/Downloads
unzip -o nothos_v7_medusa_corpus.zip
cd nothos_v5
cp ~/Downloads/medusa.png assets/medusa.png
brew install chafa figlet
source .venv/bin/activate
python nothos.py banner
```

## Import texts

Import UTF-8 plain text Gutenberg books or local Greek/Latin passages:

```bash
python nothos.py import-text ~/Downloads/greek_texts --author 'Various' --language 'Ancient Greek' --license-note 'Check edition and Gutenberg license'
python nothos.py ingest
```

Or an individual work:

```bash
python nothos.py import-text ~/Downloads/iliad.txt --author Homer --title Iliad --language 'Ancient Greek' --citation 'User-supplied edition; line references not independently verified'
python nothos.py ingest
```

Source files are copied into `passages/imported/` with JSON provenance. The original files are untouched. Gutenberg boilerplate is NOT automatically stripped; clean source files before import. Only text and markdown are supported; no PDFs or EPUB extraction. Re-ingest is incremental, but many books require significant disk space and embeddings.

## Translation

First check installed Ollama models with `ollama list`. Install an available TranslateGemma tag separately if desired. Model names depend on your Ollama registry; set `NOTHOS_TRANSLATE_MODEL` accordingly. This update does NOT pull any models.

```bash
NOTHOS_TRANSLATE_MODEL=translategemma:4b python nothos.py translate --file ~/Downloads/greek_texts/passage.txt --source 'Ancient Greek' --target English --output ~/Downloads/passage_en.txt
```

TranslateGemma support is an Ollama `/api/chat` adapter, not a claim of validated classical-Greek accuracy. Review translations, especially names, lacunae, dialects and meter. Long texts should be split into smaller files; no automatic long-document translation batching yet.

## Terminal visuals

`python nothos.py banner` uses Chafa at **45x25** with your Medusa PNG and FIGlet beneath it. Colors use the existing ANSI evidence tiers. Progress activity goes to stderr and never pretends to show an exact completion percentage for an Ollama request.

`NOTHOS_COLOR=always NOTHOS_PROGRESS=always python nothos.py evidence 'Hermes Apollo Pan lyre syrinx'`

## Genealogy

`python nothos.py genealogy pan` shows provisional source-specific variants. Records are unverified summaries, not transcribed Greek quotations.

## Remaining work

This update does not implement a verified original-language corpus, automatic Greek morphology, semantic claim-by-claim verification, bulk Gutenberg downloading, or a fully curated myth-variant database. Existing dashboard and research modes are retained.
