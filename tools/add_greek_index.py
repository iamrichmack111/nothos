import sqlite3
import unicodedata
import betacode

DB = "data/dictionaries/lsj.sqlite3"

def normalize(text):
    return unicodedata.normalize("NFC", text).casefold()

con = sqlite3.connect(DB)

columns = {
    row[1]
    for row in con.execute("PRAGMA table_info(entries)")
}

if "greek_lemma" not in columns:
    con.execute("ALTER TABLE entries ADD COLUMN greek_lemma TEXT")

if "greek_normalized" not in columns:
    con.execute("ALTER TABLE entries ADD COLUMN greek_normalized TEXT")

rows = con.execute("SELECT id, beta_key FROM entries").fetchall()

print(f"Converting {len(rows):,} dictionary headwords...")

batch = []

for entry_id, beta in rows:
    try:
        greek = betacode.conv.beta_to_uni(beta)
        normalized = normalize(greek)
    except Exception:
        greek = beta
        normalized = normalize(beta)

    batch.append((greek, normalized, entry_id))

    if len(batch) >= 1000:
        con.executemany("""
            UPDATE entries
            SET greek_lemma = ?, greek_normalized = ?
            WHERE id = ?
        """, batch)
        con.commit()
        batch.clear()

if batch:
    con.executemany("""
        UPDATE entries
        SET greek_lemma = ?, greek_normalized = ?
        WHERE id = ?
    """, batch)

con.execute("""
CREATE INDEX IF NOT EXISTS idx_lsj_greek_normalized
ON entries(greek_normalized)
""")

con.commit()
con.close()

print("Greek Unicode index created successfully.")
