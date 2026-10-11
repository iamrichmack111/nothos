from pathlib import Path
import sqlite3
import xml.etree.ElementTree as ET
import re

SOURCE = Path("data/lexicons/perseus/CTS_XML_TEI/perseus/pdllex/grc/lsj")
DEST = Path("data/dictionaries/lsj.sqlite3")

files = sorted(SOURCE.glob("*.xml"))
if not files:
    raise SystemExit(f"No LSJ XML files found in {SOURCE}")

con = sqlite3.connect(DEST)
con.execute("PRAGMA journal_mode=WAL")
con.execute("""
CREATE TABLE IF NOT EXISTS entries (
    id TEXT PRIMARY KEY,
    beta_key TEXT,
    definition TEXT,
    source_file TEXT
)
""")
con.execute("CREATE INDEX IF NOT EXISTS idx_lsj_beta ON entries(beta_key)")
con.execute("""
CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts
USING fts5(id UNINDEXED, beta_key, definition)
""")

total = 0

for number, path in enumerate(files, 1):
    print(f"[{number}/{len(files)}] Importing {path.name}", flush=True)

    batch = []

    for event, elem in ET.iterparse(path, events=("end",)):
        tag = elem.tag.rsplit("}", 1)[-1]

        if tag != "entryFree":
            continue

        key = elem.attrib.get("key", "").strip()
        entry_id = elem.attrib.get("id", "")
        text = " ".join(" ".join(elem.itertext()).split())

        if key and text:
            unique_id = f"{path.stem}:{entry_id}"
            batch.append((unique_id, key, text, path.name))

        elem.clear()

    with con:
        con.executemany("""
            INSERT OR REPLACE INTO entries
            (id, beta_key, definition, source_file)
            VALUES (?, ?, ?, ?)
        """, batch)

    total += len(batch)
    print(f"  {len(batch):,} entries")

# Rebuild FTS so rerunning the importer doesn't duplicate search records.
with con:
    con.execute("DELETE FROM entries_fts")
    con.execute("""
        INSERT INTO entries_fts (id, beta_key, definition)
        SELECT id, beta_key, definition FROM entries
    """)

print(f"\nImported {total:,} LSJ entries")
print(f"Database: {DEST}")
print(f"Database size: {DEST.stat().st_size / 1024 / 1024:.1f} MB")
con.close()
