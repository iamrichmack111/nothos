# NOTHOS V5.3 corrective patch

Adds the previously proposed **working** `evidence` command, which uses the exact same evidence selection as `ask` without calling the chat model. Strengthens the prompt against reversing the lyre transfer and inventing irrelevant Orpheus/Siren connections. This is **not** claim-by-claim semantic verification; the model can still make errors. No database rebuild or model download needed.

Install by extracting this ZIP over `~/Downloads/nothos_v5`, preserving `.venv` and `nothos.sqlite3`.

```
python nothos.py evidence "Hermes Apollo Pan lyre syrinx" --top-k 12
python nothos.py ask "Explain Hermes, Apollo, Pan, the lyre, and the syrinx" --top-k 12
```
