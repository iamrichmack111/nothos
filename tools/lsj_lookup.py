import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "data/dictionaries/lsj.sqlite3"

try:
    import betacode
except ImportError:
    raise SystemExit("Install dependency: pip install betacode")

def to_greek(beta):
    try:
        return betacode.conv.beta_to_uni(beta)
    except Exception:
        return beta

def lookup(term):
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    rows = con.execute("""
        SELECT beta_key, definition, source_file
        FROM entries
        WHERE beta_key = ?
        LIMIT 5
    """, (term,)).fetchall()

    if not rows:
        rows = con.execute("""
            SELECT beta_key, definition, source_file
            FROM entries
            WHERE beta_key LIKE ?
            LIMIT 10
        """, (f"%{term}%",)).fetchall()

    if not rows:
        print("No entries found.")
        return

    for row in rows:
        print("\n" + "═" * 65)
        print("LSJ:", to_greek(row["beta_key"]))
        print("Beta Code:", row["beta_key"])
        print("Source:", row["source_file"])
        print("═" * 65)

        # Show a manageable preview.
        print(row["definition"][:2500])

    con.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python tools/lsj_lookup.py "lo/gos"')
    lookup(sys.argv[1])
