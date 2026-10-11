"""NOTHOS primary-text corpus: searchable, auditable, offline, stdlib only."""
import argparse
import json
import os
import re
import shutil
import sqlite3
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / 'data' / 'primary_sources'
DB = CORPUS / 'primary_index.sqlite3'  # separate from LSJ databases

def norm(s):
    s = unicodedata.normalize('NFD', str(s)).casefold()
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn' and c.isalnum() or c.isspace()).strip()

def tokens(s):
    return [x for x in norm(s).split() if len(x) > 1]

def records():
    for path in sorted(CORPUS.glob('*.json')):
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            for d in data if isinstance(data, list) else [data]:
                if isinstance(d, dict) and d.get('greek') and d.get('author') and d.get('work'):
                    yield d, path.name
        except (OSError, ValueError):
            continue

def index():
    CORPUS.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(DB))
    try:
        db.execute('CREATE TABLE IF NOT EXISTS passages (id TEXT PRIMARY KEY, author TEXT, work TEXT, reference TEXT, greek TEXT, translation TEXT, keywords TEXT, notes TEXT, source_file TEXT, normalized TEXT)')
        db.execute('DELETE FROM passages')
        count = 0
        for d, file in records():
            ref = str(d.get('reference') or d.get('lines') or '?')
            ident = str(d.get('id') or f"{d['author']}:{d['work']}:{ref}")
            keys = ' '.join(map(str, d.get('keywords', []))) if isinstance(d.get('keywords', []), list) else str(d.get('keywords', ''))
            searchable = norm(' '.join([str(d['author']), str(d['work']), ref, d['greek'], d.get('translation',''), keys]))
            db.execute('INSERT OR REPLACE INTO passages VALUES (?,?,?,?,?,?,?,?,?,?)', (ident, d['author'], d['work'], ref, d['greek'], d.get('translation',''), keys, d.get('notes', d.get('explanation','')), file, searchable))
            count += 1
        db.commit()
        return count
    finally:
        db.close()

def search(q, k):
    # No embedding score is presented as a historical evidence score.
    if not DB.exists():
        index()
    with sqlite3.connect(str(DB)) as db:
        db.row_factory = sqlite3.Row
        rows = list(db.execute('SELECT * FROM passages'))
    qn = norm(q)
    qt = set(tokens(q))
    stop = {'what','which','who','where','when','why','how','are','the','and','for','from','about','according','names','name','tell','does','did','their','they','were','with','text','passage','ancient','greek','lines'}
    qt -= stop
    ranked = []
    for row in rows:
        hay = row['normalized']
        words = set(hay.split())
        hits = qt & words
        partial = sum(1 for t in qt if len(t) >= 4 and t in hay and t not in hits)
        score = len(hits) * 4 + partial
        if qn and qn in hay:
            score += 10
        if score:
            ranked.append((score, dict(row)))
    ranked.sort(key=lambda x: (-x[0], x[1]['author'], x[1]['work'], x[1]['reference']))
    return ranked[:k]

def colors(enabled):
    def c(code, txt): return f'\033[{code}m{txt}\033[0m' if enabled else txt
    return c

def banner(enabled, mode):
    if mode == 'none': return
    c = colors(enabled)
    if mode in ('auto', 'medusa', 'full') and sys.stdout.isatty():
        import subprocess
        art = ROOT / 'assets' / 'medusa.png'
        chafa = shutil.which('chafa')
        if art.is_file() and chafa:
            subprocess.run(
                [chafa, '--size', '45x25', str(art)],
                check=False,
            )
    print(c('1;35', '🏛️  N O T H O S  ·  PRIMARY TEXTS'))
    print(c('36', '⚡ MYTHOLOGY  📖 PHILOLOGY  🏺 LEXICONS  📜 SOURCES  🛡️ EVIDENCE'))

def run(argv):
    p = argparse.ArgumentParser(prog='nothos research', description='Offline primary-source passage search')
    p.add_argument('query', nargs='?')
    p.add_argument('--engine', default='primary')
    p.add_argument('--sources', default=None)
    p.add_argument('--top-k', type=int, default=8)
    p.add_argument('--no-ai', action='store_true')
    p.add_argument('--banner', choices=['auto','none','full','medusa'], default='auto')
    p.add_argument('--full', action='store_true')
    p.add_argument('--format', choices=['text','json'], default='text')
    p.add_argument('--output')
    p.add_argument('--reindex', action='store_true')
    args = p.parse_args(argv)
    if args.reindex:
        print(f'Indexed {index()} primary passages in {DB}')
        if not args.query: return 0
    if not args.query:
        p.error('query is required unless --reindex is used')
    if args.top_k < 1: p.error('--top-k must be positive')
    hits = search(args.query, args.top_k)
    payload = {'query': args.query, 'corpus_count': sum(1 for _ in records()), 'results': [d for _, d in hits], 'method': 'lexical passage retrieval; no passage-level AI verification'}
    if args.format == 'json':
        output = json.dumps(payload, ensure_ascii=False, indent=2)
    else:
        color = sys.stdout.isatty() and os.getenv('NO_COLOR') is None and os.getenv('TERM') != 'dumb'
        c = colors(color)
        if not args.output: banner(color, args.banner)
        lines = [c('1;36', f'🔎 QUERY: {args.query}'), c('90', f'📚 Indexed corpus: {payload["corpus_count"]} passage(s)')]
        if not hits:
            lines.extend([c('1;33','⚠️  No matching primary passage in the installed corpus.'), 'No quotation or historical conclusion generated.', 'Add licensed/public-domain passages as JSON and run --reindex.'])
        for i, (score, d) in enumerate(hits, 1):
            lines.extend(['', c('1;35', '═'*64), c('1;33', f'[{i}] 📜 {d["author"]}, {d["work"]} {d["reference"]}'), c('1;32', '🔒 PRIMARY GREEK TEXT'), d['greek']])
            if d['translation']:
                lines.extend(['', c('1;36','🗣️  ENGLISH TRANSLATION (CORPUS-SUPPLIED)'), d['translation']])
            if d['notes']:
                lines.extend(['', c('1;33','📝 CURATOR NOTES (NOT PRIMARY TEXT)'), d['notes']])
            lines.append(c('90', f'🛡️ Source file: {d["source_file"]}; citation: {d["author"]}, {d["work"]} {d["reference"]}'))
        lines.extend(['', c('1;35','🛡️ EVIDENCE BOUNDARY'), 'Retrieved passages are corpus text; translations and notes are separate editorial content.', 'Matches are lexical, not proof of a claim. Verify Greek against a critical edition.'])
        output = '\n'.join(lines)
    if args.output:
        dest = Path(args.output).expanduser()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(output + '\n', encoding='utf-8')
        print(f'Saved: {dest}')
    else:
        print(output)
    return 0
