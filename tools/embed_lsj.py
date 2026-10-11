import os
import json
import sqlite3
import time
import requests
import numpy as np
from pathlib import Path

SOURCE = Path("data/dictionaries/lsj.sqlite3")
DEST = Path("data/dictionaries/lsj_embeddings.sqlite3")

OLLAMA = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
MODEL = os.getenv("NOTHOS_EMBED_MODEL", "embeddinggemma-2")

LIMIT = int(os.getenv("LSJ_LIMIT", "100"))

source = sqlite3.connect(SOURCE)
dest = sqlite3.connect(DEST)

dest.execute("""
CREATE TABLE IF NOT EXISTS embeddings (
    entry_id TEXT PRIMARY KEY,
    lemma TEXT,
    definition TEXT,
    vector BLOB,
    model TEXT
)
""")

rows = source.execute("""
SELECT id, greek_lemma, definition
FROM entries
WHERE greek_lemma IS NOT NULL
LIMIT ?
""", (LIMIT,)).fetchall()

print(f"Embedding {len(rows):,} LSJ entries using {MODEL}")

completed = 0

for entry_id, lemma, definition in rows:
    existing = dest.execute(
        "SELECT 1 FROM embeddings WHERE entry_id=? AND model=?",
        (entry_id, MODEL)
    ).fetchone()

    if existing:
        continue

    text = f"Ancient Greek lemma: {lemma}\nLSJ definition: {definition[:4000]}"

    try:
        response = requests.post(
            f"{OLLAMA}/api/embed",
            json={"model": MODEL, "input": text},
            timeout=120
        )
        response.raise_for_status()

        vector = response.json()["embeddings"][0]
        vector = np.asarray(vector, dtype=np.float32)

        dest.execute("""
            INSERT OR REPLACE INTO embeddings
            (entry_id, lemma, definition, vector, model)
            VALUES (?, ?, ?, ?, ?)
        """, (
            entry_id,
            lemma,
            definition,
            vector.tobytes(),
            MODEL
        ))

        completed += 1

        if completed % 10 == 0:
            dest.commit()
            print(f"Embedded {completed:,} entries", flush=True)

    except Exception as exc:
        print(f"Error embedding {lemma}: {exc}")
        time.sleep(2)

dest.commit()

print(f"\nCompleted: {completed:,} new embeddings")
print(f"Database: {DEST}")

source.close()
dest.close()
