# NOTHOS V5.2: source-first evidence update

## Safe in-place upgrade (no model downloads)

Unzip `nothos_v5_2_evidence.zip` into `~/Downloads` so the `nothos_v5/` folder overlays your existing directory. **Do not delete your existing `nothos.sqlite3`**. The archive contains no database, no virtual environment, and no Ollama weights.

```bash
cd ~/Downloads
unzip -o nothos_v5_2_evidence.zip
cd nothos_v5
source .venv/bin/activate
export NOTHOS_CHAT_MODEL=gemma3:4b
export NOTHOS_TOP_K=12
python -m unittest discover -s tests -v
python nothos.py ingest
python nothos.py ask 'Explain Hermes, Apollo, Pan, the lyre, and the syrinx' --top-k 12
```

## Changes
- Answer retrieval overfetches candidates, prioritizes source-located passage records, and reduces generic relationship noise.
- Evidence tiers: 1 collated/verified primary text; 2 verified locator; 3 source-located uncollated summary; 4 cited but unchecked or legacy entity; 5 uncited graph relationship; 6 interpretation. **Existing material is not silently promoted to verified.**
- Greek/Latin source-tradition labels and citations appear in the source list.
- Automated citation-range and known instrument-conflation checks display warnings. These checks are heuristics, not independent scholarly verification.
- Corrected editorial wording on Pan and the syrinx to avoid attributing an explicit exclusion of lyre-playing to the ancient hymn.
- Top-K default 12, configurable via `NOTHOS_TOP_K` or `--top-k`.
- No re-embedding of unchanged records; only edited curated records require embedding.

## Limitations
This is not full claim-level entailment checking or independent primary-text collation. A language model may still hallucinate. Source labels are heuristic. Image metadata is not image-vector embedding. Word-overlap chunking is unchanged (220/45).
