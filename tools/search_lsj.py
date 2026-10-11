from nothos_format import greek_entry

import re
from betacode.conv import beta_to_uni

def clean_greek(text):
    """Convert Greek Beta Code tokens to Unicode Greek."""
    if not text:
        return ""

    def convert(match):
        token = match.group(0)
        try:
            return beta_to_uni(token)
        except Exception:
            return token

    # Convert Beta Code tokens containing Greek diacritics.
    pattern = r"(?<![A-Za-z])[A-Za-z*()\\/=+|]+(?:[A-Za-z*()\\/=+|]*)"

    def safe_convert(match):
        token = match.group(0)

        # Avoid converting ordinary English words.
        if not any(c in token for c in "*/\\()=+|"):
            return token

        return convert(match)

    return re.sub(pattern, safe_convert, text)

import argparse
import os
import sqlite3
import requests
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data/dictionaries/lsj_embeddings.sqlite3"

OLLAMA = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
MODEL = os.getenv("NOTHOS_EMBED_MODEL", "embeddinggemma-2")


def search(query, top_k=5):
    response = requests.post(
        f"{OLLAMA}/api/embed",
        json={"model": MODEL, "input": query},
        timeout=120
    )
    response.raise_for_status()

    query_vector = np.asarray(
        response.json()["embeddings"][0],
        dtype=np.float32
    )

    query_vector /= max(np.linalg.norm(query_vector), 1e-12)

    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)

    rows = con.execute("""
        SELECT lemma, definition, vector
        FROM embeddings
        WHERE model = ?
    """, (MODEL,))

    results = []

    for lemma, definition, blob in rows:
        vector = np.frombuffer(blob, dtype=np.float32)

        if vector.shape != query_vector.shape:
            continue

        norm = np.linalg.norm(vector)

        if norm == 0:
            continue

        similarity = float(
            np.dot(query_vector, vector) / norm
        )

        results.append((similarity, lemma, definition))

    con.close()

    results.sort(key=lambda item: item[0], reverse=True)


    print(f"\n🔮 LSJ SEMANTIC RESULTS: {query}\n")

    for rank, (score, lemma, definition) in enumerate(
        results[:top_k], 1
    ):
        print(f"📖 RESULT {rank} OF {min(top_k, len(results))}")

        greek_entry(
            lemma=lemma,
            definition=definition,
            source="LSJ",
            similarity=score,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--top-k", type=int, default=5)

    args = parser.parse_args()

    search(args.query, args.top_k)
