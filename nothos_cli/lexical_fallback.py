"""Read-only LSJ shared-spelling lookup for source concordance expansion.

Matching shared letters is NOT a historical derivation or lemma equivalence.
"""
import sqlite3
import unicodedata
from pathlib import Path


def _norm(s):
    s = unicodedata.normalize('NFD', s).casefold()
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn').replace('ς', 'σ')


def related_lsj_headwords(term, max_results=6):
    root = Path(__file__).resolve().parents[1]
    # Use exactly the LSJ database configured by the original engine.
    import sys
    sys.path.insert(0, str(root / 'tools'))
    from lsj_rag import LEXICON_DB
    needle = _norm(term)
    if len(needle) < 4:
        return []
    results = []
    con = sqlite3.connect(f'file:{LEXICON_DB.resolve()}?mode=ro', uri=True)
    try:
        for (lemma,) in con.execute('SELECT greek_lemma FROM entries WHERE greek_lemma IS NOT NULL AND greek_lemma != ""'):
            word = _norm(lemma)
            if word == needle:
                continue
            common = 0
            for x, y in zip(needle, word):
                if x != y:
                    break
                common += 1
            if common >= 3 and len(word) >= 4:
                # Prefer common prefix ratio and shorter lexical candidates.
                results.append((common / max(len(word), len(needle)), common, len(word), lemma))
    finally:
        con.close()
    results.sort(key=lambda x: (-x[1], -x[0], x[2], x[3]))
    dedup = []
    found = set()
    for _, _, _, lemma in results:
        norm = _norm(lemma)
        if norm not in found:
            found.add(norm)
            dedup.append(lemma)
            if len(dedup) >= max_results:
                break
    return dedup
