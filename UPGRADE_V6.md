# NOTHOS V6 — Obsidian / Gold research update

## Install (overlay existing directory, preserve SQLite)

```sh
cd ~/Downloads
unzip -o nothos_v6_obsidian.zip
cd nothos_v5
source .venv/bin/activate
python nothos.py doctor
python nothos.py ingest
python nothos.py web --host 127.0.0.1 --port 8789
```

Open http://127.0.0.1:8789 in your browser. To show Medusa in the terminal: `python nothos.py banner`.

Other commands:

```sh
python nothos.py evidence 'Hermes Apollo Pan lyre syrinx'
python nothos.py ask 'Explain Hermes, Apollo, Pan, the lyre, and the syrinx' --mode strict
python nothos.py ask 'Explore possible symbolism of Pan and the syrinx' --mode exploratory
python nothos.py graph --entity hermes
python nothos.py timeline
python nothos.py morph 'σύριγξ'
python nothos.py evaluate
python -m unittest discover -s tests -v
```

## Included

- Black/gold browser dashboard with six evidence colors and transparent provenance.
- Query-entity coverage report and source-first evidence selection.
- Interactive SVG relationship atlas with clearly marked unverified graph edges.
- Passage desk with instructions for adding original UTF-8 text and citations.
- Conservative Unicode Greek word inspector (not a morphological analyzer).
- Source tradition timeline (approximate period groupings).
- Strict and exploratory answer modes; hypotheses explicitly labeled.
- Offline regression fixture checks and test suite.
- Original Medusa-style terminal ASCII banner.

## Important limitations

The visual graph is a dataset visualization, not a historically validated relationship graph. No primary Greek/Latin corpus or lexicon is bundled. Original-text collation, automated translation/transliteration, historical date assignment per record, true lemma parsing, semantic claim-by-claim entailment, and reliable myth-variant contradiction detection are **not yet implemented**. Citation audits are heuristic; the answer model may still hallucinate. Evidence tier is provenance, not truth. The UI serves locally by default, without authentication; do not expose it to public networks. No models or SQLite database are included in the ZIP.
