"""Exploratory Greek morpheme analyzer — candidate splits are not etymologies."""
import argparse
import json
import unicodedata
from dataclasses import dataclass

@dataclass(frozen=True)
class Part:
    greek: str
    roman: str
    meaning: str
    category: str
    note: str = ''

# Starter lexicon: add reviewed entries here, with source references later.
PREFIXES = (
    Part('ἀ-', 'a-', 'not; without', 'privative prefix', 'Before vowels, often an-; do not mistake any initial a for this prefix.'),
    Part('ἀν-', 'an-', 'not; without', 'privative prefix', 'Variant before vowels; context-dependent.'),
    Part('δυσ-', 'dys-', 'badly; difficult', 'prefix'),
    Part('εὐ-', 'eu-', 'well; good', 'prefix'),
    Part('ἀντι-', 'anti-', 'against; in place of', 'prefix'),
    Part('συν-', 'syn-', 'with; together', 'prefix', 'Assimilation often changes spelling.'),
    Part('ὑπέρ-', 'hyper-', 'over; beyond', 'prefix'),
    Part('ὑπο-', 'hypo-', 'under', 'prefix'),
    Part('περι-', 'peri-', 'around; concerning', 'prefix'),
    Part('προ-', 'pro-', 'before; forward', 'prefix'),
    Part('μετα-', 'meta-', 'after; change; among', 'prefix'),
)
ROOTS = (
    Part('θεός', 'theos', 'god', 'lexical root'),
    Part('λόγος', 'logos', 'word; account; reason', 'lexical root'),
    Part('βίος', 'bios', 'life', 'lexical root'),
    Part('γράφω', 'graph-', 'write; draw', 'lexical root'),
    Part('φίλος', 'phil-', 'loving; dear; friend', 'lexical root'),
    Part('φόβος', 'phob-', 'fear', 'lexical root'),
    Part('κράτος', 'krat-', 'power; rule', 'lexical root'),
    Part('ἀφρός', 'aphros', 'foam', 'lexical root', 'Ancient association with Aphrodite; name origin disputed.'),
    Part('νύξ', 'nykt-', 'night', 'lexical root', 'Inflection changes stem: νυκτ-.'),
    Part('φῶς', 'phot-', 'light', 'lexical root', 'Inflection changes stem: φωτ-.'),
)
SUFFIXES = (
    Part('-λογία', '-logia', 'study; discourse; account', 'productive compound ending'),
    Part('-φοβία', '-phobia', 'fear', 'productive compound ending'),
    Part('-κρατία', '-kratia', 'rule; power', 'productive compound ending'),
    Part('-ῖτις', '-itis', 'pertaining to; (modern medical) inflammation', 'suffix', 'Ancient and modern meanings differ.'),
    Part('-ικός', '-ikos', 'pertaining to', 'adjectival suffix'),
    Part('-σις', '-sis', 'action; process', 'nominal suffix', 'Not an independent word.'),
    Part('-μα', '-ma', 'result of an action', 'nominal suffix', 'Not an independent word.'),
)

# Treat lexical identities as whole forms, rather than combining fragments at will.
KNOWN = {
    'αθεοσ': {'lemma':'ἄθεος', 'gloss':'without a god; godless', 'segments':('ἀ-', 'θεός'),
              'note':'Conventional privative-alpha + θεός analysis.'},
    'δυσλογια': {'lemma':'δυσλογία', 'gloss':'bad speaking; abusive language', 'segments':('δυσ-', 'λόγος'),
                 'note':'Theoretical breakdown only; inspect attestations for this exact formation.'},
    'αφροδιτη': {'lemma':'Ἀφροδίτη', 'gloss':'Aphrodite, proper divine name', 'segments':(),
                'note':'Etymology disputed. Association with ἀφρός (foam) is ancient; '
                       'a- | phro- | di- | -te is NOT a verified Greek morpheme breakdown.'},
    'νυξ': {'lemma':'νύξ', 'gloss':'night; also divine name Nyx when context identifies the goddess', 'segments':(),
            'note':'The word has a νυκτ- stem in inflected forms; no prefix/suffix splitting required.'},
}


def norm(s):
    s = unicodedata.normalize('NFD', s.casefold())
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn').replace('ς', 'σ')


def translit(s):
    mapping = {'α':'a','β':'b','γ':'g','δ':'d','ε':'e','ζ':'z','η':'ē','θ':'th','ι':'i',
               'κ':'k','λ':'l','μ':'m','ν':'n','ξ':'x','ο':'o','π':'p','ρ':'r',
               'σ':'s','τ':'t','υ':'y','φ':'ph','χ':'kh','ψ':'ps','ω':'ō'}
    # Preserve rough breathing (dasia) before removing accent marks.
    # E.g. Ἑρμῆς -> hermēs; ἄθεος -> atheos.
    decomposed = unicodedata.normalize('NFD', s.casefold())
    chars = []
    for ch in decomposed:
        if unicodedata.category(ch).startswith('M'):
            if ch == '\u0314' and chars:  # Greek rough breathing mark
                chars[-1] = 'h' + chars[-1]
            continue
        chars.append(mapping.get(ch, ch))
    return ''.join(chars)


def analyze(term, variants=False):
    token = norm(term.strip())
    if not token:
        raise ValueError('Empty Greek term')
    known = KNOWN.get(token)
    parts = {x.greek: x for x in PREFIXES + ROOTS + SUFFIXES}
    result = {'term':term, 'transliteration':translit(term), 'dictionary_gloss':None,
              'status':'EXPLORATORY — NOT VERIFIED', 'notes':[], 'attested_components':[],
              'possible_components':[], 'unverified_segmentation':None}
    if known:
        result['dictionary_gloss'] = known['gloss']
        result['notes'].append(known['note'])
        if known['segments']:
            result['status'] = 'CURATED COMPONENT ANALYSIS (not independently source-verified)'
            result['attested_components'] = [vars(parts[x]) for x in known['segments']]
        if token == 'αφροδιτη':
            result['unverified_segmentation'] = ['a-', 'phro-', 'di-', '-tē']
            result['possible_components'].append(vars(next(p for p in ROOTS if p.greek == 'ἀφρός')))
    else:
        # These are *hints*, not proven morphological analyses.
        candidates = []
        for p in PREFIXES:
            base = norm(p.greek.replace('-', ''))
            if token.startswith(base) and len(token) > len(base) + 2:
                candidates.append(p)
        for p in SUFFIXES:
            base = norm(p.greek.replace('-', ''))
            if token.endswith(base) and len(token) > len(base) + 2:
                candidates.append(p)
        result['possible_components'] = [vars(x) for x in candidates]
        if not candidates:
            result['notes'].append('No reviewed decomposition found. An absent match is not evidence against a compound.')
        else:
            result['notes'].append('Spelling overlap is not evidence that the word was formed from these pieces.')
    if variants:
        add_variants(result)
    return result



# NOTHOS_V17_1_COLORS
# Presentation only: do not alter the semantic report or saved files.
def _nothos_ety_colorize(report, mode='auto'):
    import os
    import re
    import sys
    if mode == 'never' or os.getenv('NO_COLOR') is not None:
        return report
    if mode == 'auto' and (not sys.stdout.isatty() or os.getenv('TERM') == 'dumb'):
        return report

    R = '\x1b[0m'
    GOLD = '\x1b[1;33m'       # Greek text and lexical headwords
    MAGENTA = '\x1b[1;35m'    # Section titles
    CYAN = '\x1b[1;36m'       # Search metadata
    GREEN = '\x1b[1;32m'      # Meanings
    YELLOW = '\x1b[1;33m'     # Cautions and uncertainty
    DIM = '\x1b[2;37m'        # Scope / confidence notes
    greek_re = re.compile(r'[\u0370-\u03ff\u1f00-\u1fff]+(?:[\u0300-\u036f])*')

    def paint_greek(line):
        return greek_re.sub(lambda m: GOLD + m.group(0) + R, line)

    rendered = []
    art_lines = False
    for line in report.splitlines(keepends=True):
        # Gold banner/Medusa picture, with no ANSI in saved text/JSON.
        if line.startswith('╔'):
            art_lines = True
        if art_lines:
            if line.startswith('🏛️ NOTHOS — GREEK ROOT & MORPHEME LAB'):
                art_lines = False
            else:
                rendered.append('\x1b[1;35m' + line.rstrip('\r\n') + '\x1b[0m' + line[len(line.rstrip('\r\n')):])
                continue
        base = line.lstrip()
        if base.startswith('━' * 20):
            rendered.append('\x1b[1;35m' + line.rstrip('\r\n') + '\x1b[0m' + line[len(line.rstrip('\r\n')):])
            continue
        # Bold section labels; preserve text verbatim, including whitespace.
        if (base.startswith(('🏛️ NOTHOS', 'POSSIBLE CONNECTIONS',
                             '🔬 DI / DE', '🔎 POSSIBLE COMPONENT',
                             '🧩 DYNAMIC SEGMENTATION', '📚 COMPONENT LSJ',
                             '📖 LSJ ', '📖 DIRECT LSJ', '🧠 NOTHOS',
                             'CURATED COMPONENTS', 'USER-STYLE HYPOTHESIS'))):
            rendered.append(MAGENTA + paint_greek(line.rstrip('\r\n')) + R
                            + line[len(line.rstrip('\r\n')):])
        elif base.startswith(('⚠', 'NOTE:', '🛡️', 'No direct LSJ evidence',
                              'UNRESOLVED REMAINDER:')):
            rendered.append(YELLOW + paint_greek(line.rstrip('\r\n')) + R
                            + line[len(line.rstrip('\r\n')):])
        elif base.startswith(('QUERY:', 'MODEL:', 'WHOLE-WORD GLOSS:')):
            rendered.append(CYAN + paint_greek(line.rstrip('\r\n')) + R
                            + line[len(line.rstrip('\r\n')):])
        elif base.startswith(('STATUS:', 'TYPE:', 'LEXICAL CONNECTION ONLY',
                              'ATTESTED WORD; CONNECTION UNPROVEN')):
            rendered.append(DIM + paint_greek(line.rstrip('\r\n')) + R
                            + line[len(line.rstrip('\r\n')):])
        elif ' — ' in line and base and not base.startswith(('=', '━', '═')):
            # Highlight Greek headwords separately, with English gloss in green.
            left, right = line.split(' — ', 1)
            rendered.append(paint_greek(left) + ' — ' + GREEN
                            + paint_greek(right.rstrip('\r\n')) + R
                            + right[len(right.rstrip('\r\n')):])
        else:
            rendered.append(paint_greek(line))
    return ''.join(rendered)



# NOTHOS_V17_2_BANNER_ART
_NOTHOS_ETYMOLOGY_BANNER = """╔══════════════════════════════════════════════════════╗
║              🏛️  N O T H O S  🏛️                 ║
╚══════════════════════════════════════════════════════╝
  ⚡ MYTHOLOGY   📖 PHILOLOGY   🏺 LEXICONS
  🔮 SEMANTIC SEARCH   🇬🇷 ANCIENT GREEK
  🧠 OLLAMA   📜 PRIMARY SOURCES   🔎 EVIDENCE

                  .-\\\\\\|////-.
                 /  _       _  \\
                |  (o)     (o)  |
                |       ^        |
                 \\   \\___/     /
                  '._       _.'
                 /_  '-._.-'  _\\
                // \\         / \\\\
               //   MEDUSA    \\\\
             ~~~  GREEK ROOTS  ~~~
"""


# NOTHOS_V17_5_SECTION_DIVIDERS
# Presentation only: plain Unicode dividers, safe for UTF-8 and JSON exports.
def _nothos_etymology_separators(report):
    """Insert dividers before semantic sections; preserve all existing text."""
    if not isinstance(report, str):
        return report
    headings = (
        'POSSIBLE CONNECTIONS',
        '🔬 DI / DE / DĒ HYPOTHESES',
        '🔎 POSSIBLE COMPONENT MEANINGS',
        '🧩 DYNAMIC SEGMENTATION',
        '📚 COMPONENT LSJ CHECKS',
        '📖 LSJ WHOLE-WORD LOOKUP',
        '📖 DIRECT LSJ',
        'USER-STYLE HYPOTHESIS:',
        '🧠 NOTHOS — OLLAMA ETYMOLOGY HYPOTHESES',
        'CURATED COMPONENTS',
    )
    divider = '━' * 60
    out = []
    for line in report.splitlines():
        if any(line.lstrip().startswith(h) for h in headings):
            # The Ollama section already has its own box rule. Avoid stacking them.
            if out and out[-1].strip() == divider:
                pass
            else:
                if out and out[-1].strip() != '':
                    out.append('')
                out.append(divider)
        out.append(line)
    return '\n'.join(out) + ('\n' if report.endswith('\n') else '')


def main(argv=None):
    parser = argparse.ArgumentParser(prog='nothos etymology',
        description='Greek prefix, root and suffix proposals with confidence warnings')
    parser.add_argument('term', help='Greek word or name')
    parser.add_argument('--variants', action='store_true',
                        help='Explore δι/δε/δη alternatives; not verified etymologies')
    parser.add_argument('--ai', action='store_true',
                        help='Ask local Ollama to compare proposed components (unverified)')
    parser.add_argument('--model', metavar='OLLAMA_MODEL',
                        help='Select the local Ollama model for --ai')
    parser.add_argument('--color', choices=['auto','always','never'], default='auto',
                        help='Terminal highlighting: auto, always, or never')
    parser.add_argument('--format', choices=['text','json'], default='text')
    parser.add_argument('--output', metavar='FILE', help='Write UTF-8 analysis to file')
    args = parser.parse_args(argv)
    try:
        r = analyze(args.term, variants=args.variants)
    except ValueError as e:
        parser.error(str(e))
    if args.model and not args.ai:
        parser.error('--model requires --ai')
    if args.ai:
        r['ollama'] = _nothos_etymology_ai(r, args.model)
    if args.format == 'json':
        output = json.dumps(r, ensure_ascii=False, indent=2)
    else:
        lines = ['🏛️ NOTHOS — GREEK ROOT & MORPHEME LAB',
                 f'QUERY: {r["term"]} | TRANSLITERATION: {r["transliteration"]}',
                 f'STATUS: {r["status"]}']
        if r['dictionary_gloss']:
            lines.append('WHOLE-WORD GLOSS: ' + r['dictionary_gloss'])
        for title, key in [('CURATED COMPONENTS','attested_components'),
                           ('POSSIBLE CONNECTIONS (UNVERIFIED)','possible_components')]:
            if r[key]:
                lines.append('\n' + title)
                for p in r[key]:
                    lines.append(f'  {p["greek"]} ({p["roman"]}) — {p["meaning"]} [{p["category"]}]')
                    if p['note']:
                        lines.append('    ⚠ ' + p['note'])
        if r.get('variants'):
            lines.append('\n🔬 DI / DE / DĒ HYPOTHESES — NOT AN ETYMOLOGY')
            for v in r['variants']:
                lines.append(f'  {v["form"]} ({v["transliteration"]}) — {v["meaning"]}')
                lines.append(f'    {v["confidence"]} | {v["category"]}')
                lines.append(f'    ⚠ {v["caution"]}')
        if r.get('candidate_morpheme_meanings'):
            lines.append('\n🔎 POSSIBLE COMPONENT MEANINGS — NOT VERIFIED DERIVATIONS')
            for p in r['candidate_morpheme_meanings']:
                lines.append(f'  {p["greek"]} ({p["roman"]}) — {p["meaning"]}')
                lines.append(f'    TYPE: {p["category"]} | STATUS: LEXICAL / GRAMMATICAL COMPARISON')
                if p.get('note'):
                    lines.append('    ⚠ ' + p['note'])
        if r.get('dynamic_segmentations'):
            lines.append('\n🧩 DYNAMIC SEGMENTATION — SPELLING CANDIDATES')
            for c in r['dynamic_segmentations']:
                lines.append(f'  {c["greek"]} — {c["meaning"]}')
                lines.append(f'    {c["category"]}; {c["match"]}')
                if c.get('remainder'):
                    lines.append(f'    UNRESOLVED REMAINDER: {c["remainder"]}')
                if c.get('note'):
                    lines.append('    ⚠ ' + c['note'])
        if r.get('component_lsj_evidence'):
            lines.append('\n📚 COMPONENT LSJ CHECKS (NOT ETYMOLOGY PROOF)')
            for e in r['component_lsj_evidence']:
                lines.append('  '+e['component']+': '+(e.get('entry','Unavailable: '+e.get('reason','unknown'))[:650]))
        if not args.ai:
            lookup = r.get('lsj_lookup', {})
            lines.append('\n📖 DIRECT LSJ ENTRY (LEXICAL EVIDENCE ONLY)')
            lines.append(lookup.get('entry','Unavailable: ' + lookup.get('reason','unknown')))
        if r['unverified_segmentation']:
            lines.append('\nUSER-STYLE HYPOTHESIS: ' + ' | '.join(r['unverified_segmentation']))
        lines.extend('\nNOTE: ' + n for n in r['notes'])
        lines.append('\n🛡️ Preliminary starter dictionary only; check LSJ and an etymological dictionary before treating any split as historical fact.')
        if args.ai:
            lookup = r.get('lsj_lookup', {})
            lines.append('\n📖 LSJ WHOLE-WORD LOOKUP (NOT ETYMOLOGY PROOF)')
            if lookup.get('status') == 'retrieved':
                lines.append(lookup['entry'])
            else:
                lines.append('No direct LSJ evidence available: ' + lookup.get('reason', 'unknown'))
            response = r['ollama']
            lines.extend(['', '═' * 60, '🧠 NOTHOS — OLLAMA ETYMOLOGY HYPOTHESES',
                          'MODEL: ' + response['model'], '═' * 60])
            if response.get('error'):
                lines.append('⚠️ Ollama unavailable: ' + response['error'])
            else:
                lines.append(response['analysis'])
                lines.append('🛡️ ' + response['warning'])
        output = '\n'.join(lines)
        output = _nothos_etymology_separators(output)
        output = _nothos_display_real_medusa(output)
    if args.output:
        from pathlib import Path
        p = Path(args.output).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(output+'\n', encoding='utf-8')
        print(f'Saved: {p}')
    print(_nothos_ety_colorize(output, args.color) if args.format == 'text' else output)
    return 0


# NOTHOS_V15_1_VARIANTS
# The displayed pieces are exploratory comparisons, not a claim that the name
# derives from their combination. A Greek vowel change needs its own evidence.
ALTERNATE_FORMS = (
    {'form': 'δι-', 'transliteration': 'di-', 'meaning': 'in some compounds: through/across (cf. διά); or two-related formations', 'category': 'possible combining element', 'confidence': 'LEXICAL CONNECTION ONLY', 'caution': 'Not every δι sequence is a prefix. Check formation and chronology.'},
    {'form': 'δις', 'transliteration': 'dis', 'meaning': 'twice', 'category': 'independent adverb', 'confidence': 'ATTESTED WORD; CONNECTION UNPROVEN', 'caution': 'δις is not equivalent to every di- sequence.'},
    {'form': 'Διός', 'transliteration': 'Dios', 'meaning': 'of Zeus', 'category': 'inflected divine name', 'confidence': 'ATTESTED WORD; CONNECTION UNPROVEN', 'caution': 'Δι- in a divine name must be demonstrated, not assumed.'},
    {'form': 'δέ', 'transliteration': 'de', 'meaning': 'but; and; on the other hand', 'category': 'particle', 'confidence': 'ATTESTED WORD; CONNECTION UNPROVEN', 'caution': 'δέ is not generally a productive prefix.'},
    {'form': 'δέω¹', 'transliteration': 'deō', 'meaning': 'bind; tie', 'category': 'verb', 'confidence': 'ATTESTED WORD; CONNECTION UNPROVEN', 'caution': 'Do not infer a root from a matching two-letter string.'},
    {'form': 'δέω²', 'transliteration': 'deō', 'meaning': 'lack; need', 'category': 'distinct verb', 'confidence': 'ATTESTED WORD; CONNECTION UNPROVEN', 'caution': 'Distinguish this verb from δέω meaning bind.'},
    {'form': 'δέκα', 'transliteration': 'deka', 'meaning': 'ten', 'category': 'numeral', 'confidence': 'ATTESTED WORD; CONNECTION UNPROVEN', 'caution': 'A shared de- spelling does not establish a ten-related stem.'},
    {'form': 'δή', 'transliteration': 'dē', 'meaning': 'indeed; certainly; now', 'category': 'particle', 'confidence': 'ATTESTED WORD; CONNECTION UNPROVEN', 'caution': 'η is not the same vowel as ε or ι.'},
)


def add_variants(result):
    """Add candidate readings where a di/de resemblance is relevant."""
    word = norm(result['term'])
    # Only suggest di/de when Greek delta+iota or delta+epsilon is actually
    # present, or when the user has proposed the Aphrodite segmentation.
    if 'δι' not in word and 'δε' not in word and word != 'αφροδιτη':
        result['variants'] = []
        result['notes'].append('No δι/δε sequence detected; no di/de variants proposed.')
        return result
    result['variants'] = [dict(v) for v in ALTERNATE_FORMS]
    for item in result['variants']:
        item['matched_in_original'] = norm(item['form'].rstrip('¹²-')) in word
        # A two-letter sequence is only orthographic overlap, not morphemic proof.
        item['historical_derivation_verified'] = False
    result['notes'].append('δι (iota), δε (epsilon), and δη (eta) differ in spelling. ' 
                           'Vowel substitution is a hypothetical change requiring external evidence.')
    if word == 'αφροδιτη':
        result['notes'].append('Ἀφροδίτη does not have a verified segmentation ' 
                               'aphro + di/de + tē; -tē is not assigned an independent meaning.')
    return result


# NOTHOS_V16_ETYMOLOGY_AI
# NOTHOS_V16_1_EVIDENCE_GATE
# LSJ is a *lexical* lookup, never proof of historical segmentation.
def _nothos_lsj_lookup(term):
    """Return *only* LSJ's labeled direct-entry text, not FAISS neighbors.

    Calls the already installed legacy LSJ engine, with AI disabled.
    """
    import os
    import re
    import subprocess
    from pathlib import Path
    exe = Path.home() / 'nothos/.venv/bin/nothos'
    if not exe.is_file():
        return {'status':'unavailable', 'reason':'Legacy LSJ executable missing'}
    cmd = [str(exe), 'research', term, '--engine', 'lsj', '--top-k', '1',
           '--no-ai', '--banner', 'auto']
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding='utf-8', errors='replace', timeout=40,
                              env={**os.environ, 'NO_COLOR':'1'})
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {'status':'unavailable', 'reason':str(exc)}
    clean = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', proc.stdout)
    # Direct entry MUST be explicitly labeled. Never promote FAISS similar words.
    start = re.search(r'(?im)^\s*(?:📖\s*)?LSJ\s*\[1\]\s*[-—:]?\s*direct dictionary evidence[^\n]*$', clean)
    if not start:
        return {'status':'unavailable', 'reason':
                ('Legacy LSJ engine returned no labeled direct entry'
                 + (f' (exit {proc.returncode})' if proc.returncode else ''))}
    rem = clean[start.end():].lstrip('\r\n')
    end = re.search(r'(?m)^\s*(?:🔮\s*RELATED LSJ|🧠\s*AI|🏛️\s*NOTHOS|📖\s*LSJ\s*\[2\]|={8,}|═{8,})', rem)
    entry = (rem[:end.start()] if end else rem).strip()
    if not entry:
        return {'status':'unavailable', 'reason':'Labeled direct LSJ entry was empty'}
    return {'status':'retrieved', 'type':'direct LSJ lexical entry',
            'entry':entry[:2400],
            'caution':'Direct lexical entry does not prove historical derivation.'}


def _nothos_etymology_ai(result, model=None):
    import json
    import os
    import re
    import unicodedata
    import urllib.request
    import urllib.error

    selected_model = model or os.environ.get('NOTHOS_AI_MODEL', 'gemma3:4b')
    term = str(result['term'])
    components = list(result.get('attested_components') or [])
    # Possible spelling overlaps are NOT evidence that the pieces compose term.
    possible = list(result.get('possible_components') or [])
    lsj = result.get('lsj_lookup') or _nothos_lsj_lookup(term)
    result['lsj_lookup'] = lsj
    warning = ('LSJ is lexical evidence, not proof of any historical decomposition; '
               'AI suggestions require external etymological verification.')
    if not components:
        comparisons = list(result.get('candidate_morpheme_meanings') or [])
        if comparisons:
            explanations = '; '.join(
                f"{c['greek']} ({c['roman']}): {c['meaning']}"
                for c in comparisons
            )
            message = ('No verified historical segmentation is available for ' + term + '. '
                       'However, these Greek lexical or grammatical forms have meanings '
                       'worth comparing: ' + explanations + '. '
                       'They are hypotheses or grammatical observations, NOT established '
                       'roots from which this term derives.')
        else:
            message = ('No reviewed segmentation or candidate component meanings are available '
                       'for ' + term + ' in this starter dictionary. No roots are invented.')
        return {'model': selected_model, 'analysis': message,
                'warning': warning, 'generation': 'deterministic: lexical candidates only'}

    endpoint = os.environ.get('NOTHOS_OLLAMA_URL', 'http://127.0.0.1:11434').rstrip('/')
    evidence = {
        'term': term,
        'transliteration': result.get('transliteration'),
        'whole_word_gloss': result.get('dictionary_gloss'),
        'reviewed_components': components,
        'possible_unverified_connections': possible,
        'alternative_spelling_hypotheses': result.get('variants') or [],
        'notes': result.get('notes') or [],
        'lsj_direct_whole_word_entry': lsj if lsj.get('status') == 'retrieved' else None,
    }
    allowed_greek = set()
    for item in [term] + [str(x.get('greek','')) for x in components + possible]:
        allowed_greek.update(re.findall(r'[\u0370-\u03ff\u1f00-\u1fff]+', item))
    if lsj.get('status') == 'retrieved':
        allowed_greek.update(re.findall(r'[\u0370-\u03ff\u1f00-\u1fff]+', lsj['entry']))
    # Restrict AI analysis to supplied candidates; quoted Greek must occur in input.
    system = (
        'You are a strictly evidence-bound Ancient Greek morphology explainer. '
        'Only discuss the supplied reviewed components as demonstrated; others are hypotheses. '
        'Do not invent Greek lemmas, grammatical roots, sound laws, etymologies, or citations. '
        'If historical derivation is not established, explicitly say so. '
        'Do not present lexical relations as derivations. '
        'Quote Greek only if it is verbatim present in supplied evidence. '
        'Never silently change Greek vowels or breathing marks. '
        'Keep the answer brief and distinguish lexicon glosses from derivational claims.'
    )
    payload = {'model': selected_model, 'stream': False,
               'messages': [{'role': 'system', 'content': system},
                            {'role': 'user', 'content': json.dumps(evidence, ensure_ascii=False)}],
               'options': {'temperature': 0, 'num_ctx': 8192, 'num_predict': 900}}
    req = urllib.request.Request(endpoint + '/api/chat',
                                 data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                                 headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=240) as response:
            response_data = json.load(response)
        answer = str((response_data.get('message') or {}).get('content') or '').strip()
        if not answer:
            raise ValueError('Ollama returned an empty response')
        # Guard against invented Greek terms: normalize accents only for comparison.
        normalize = lambda x: ''.join(c for c in unicodedata.normalize('NFD',x.casefold())
                                       if unicodedata.category(c) != 'Mn')
        allowed_norm = {normalize(x) for x in allowed_greek}
        unknown = sorted({x for x in re.findall(r'[\u0370-\u03ff\u1f00-\u1fff]+', answer)
                          if normalize(x) not in allowed_norm})
        if unknown:
            answer = ('⚠️ AI response withheld: it introduced Greek forms not present '
                      'in the supplied evidence: ' + ', '.join(unknown[:12]) + '. '
                      'No new root claims were accepted.')
            return {'model': selected_model, 'analysis': answer, 'warning': warning,
                    'generation': 'rejected: unsupported Greek forms'}
        return {'model': selected_model, 'analysis': answer, 'warning': warning,
                'generation': 'generated: unverified explanatory text'}
    except (OSError, ValueError, TimeoutError, urllib.error.URLError) as exc:
        return {'model': selected_model, 'analysis': None, 'error': str(exc)}


# NOTHOS_V16_2_CANDIDATE_ROOTS
# Candidates refer to *real Greek lexical forms or grammatical endings*;
# similarity does NOT demonstrate that a name was historically derived from them.
CANDIDATE_NAME_CONNECTIONS = {
    'ερμησ': [
        {'greek': 'ἕρμα', 'roman': 'herma', 'meaning': 'support; prop; ballast; (in some contexts) a rock or stone',
         'category': 'lexical comparison', 'note': 'Candidate word association only. Check LSJ senses and historical phonology; not a demonstrated component of Ἑρμῆς.'},
        {'greek': 'ἑρμῆς', 'roman': 'hermēs', 'meaning': 'herm; stone pillar or boundary marker with a head',
         'category': 'lexical comparison', 'note': 'A related noun worth investigating, not proof of the divine name’s derivation.'},
        {'greek': 'ἑρμηνεύς', 'roman': 'hermēneus', 'meaning': 'interpreter; explainer; translator',
         'category': 'lexical comparison', 'note': 'Resemblance to the name does not prove derivation. Treat ancient wordplay separately from historical etymology.'},
        {'greek': '-ης', 'roman': '-ēs', 'meaning': 'masculine nominative singular ending in some noun/name declensions; grammatical case, not a stand-alone lexical meaning',
         'category': 'inflectional ending', 'note': 'The -ης ending is observable in the written form; its exact paradigm must be checked separately.'},
    ],
}


def _v162_candidates(term):
    """Conservative comparisons: exact ending, prefix overlap, and curated names."""
    word = norm(term)
    out = [dict(x) for x in CANDIDATE_NAME_CONNECTIONS.get(word, ())]
    seen = {x['greek'] for x in out}
    for group, placement in ((PREFIXES, 'prefix'), (SUFFIXES, 'suffix')):
        for part in group:
            spelling = norm(part.greek.replace('-', ''))
            if len(spelling) < 2 or len(word) <= len(spelling) + 1:
                continue
            matches = word.startswith(spelling) if placement == 'prefix' else word.endswith(spelling)
            if matches and part.greek not in seen:
                out.append({**vars(part), 'category': f'{placement} spelling candidate',
                            'note': 'Spelling match only: the actual morphological boundary is unverified. ' + part.note})
                seen.add(part.greek)
    return out


_v162_prior_analyze = analyze

def analyze(term, variants=False):
    result = _v162_prior_analyze(term, variants=variants)
    candidates = _v162_candidates(term)
    result['candidate_morpheme_meanings'] = candidates
    if candidates:
        result['notes'].append('Candidate forms have dictionary/grammatical meanings; they are NOT demonstrated historical components of this word.')
    else:
        result['notes'].append('No reviewed candidates match this word in the starter lexicon; expand the dictionary for more possibilities.')
    return result


# NOTHOS_V17_DYNAMIC_LSJ
# All splits are hypothetical spelling boundaries, NEVER attested etymologies.
# Lightweight and bounded: one LSJ whole-word call per analysis; lexical
# meanings come from curated Part entries, not from an AI model's inventions.
V17_ENDINGS = (
    ('-ης','-ēs','nominative singular ending in some masculine paradigms'),
    ('-ος','-os','nominative singular ending in many masculine nouns'),
    ('-ον','-on','neuter nominative/accusative singular ending in many nouns'),
    ('-η','-ē','feminine nominative singular ending in some paradigms'),
    ('-α','-a','feminine nominative singular ending in some paradigms'),
    ('-σις','-sis','action/process noun formation in some words'),
    ('-μα','-ma','result noun formation in some words'),
)

def _v17_dynamic(term):
    token = norm(term.strip())
    if not token:
        return []
    candidates = []
    seen = set()
    def add(greek, meaning, kind, fit, rest='', note=''):
        key = (norm(greek), kind, fit, norm(rest))
        if key in seen:
            return
        seen.add(key)
        candidates.append({'greek':greek, 'roman':translit(greek.strip('-')),
                           'meaning':meaning, 'category':kind,
                           'match':fit, 'remainder':rest, 'note':note,
                           'verified_etymology':False})
    for p in PREFIXES:
        form = norm(p.greek.strip('-'))
        if len(form)>=1 and token.startswith(form) and len(token)>len(form)+2:
            add(p.greek,p.meaning,'prefix candidate','literal initial match',
                token[len(form):], 'Boundary not verified; prefix meaning is attested, use here hypothetical.')
    for p in SUFFIXES:
        form = norm(p.greek.strip('-'))
        if len(form)>=2 and token.endswith(form) and len(token)>len(form)+1:
            add(p.greek,p.meaning,'suffix candidate','literal final match',
                token[:-len(form)],'No proof this suffix was used in the name.')
    for greek, roman, meaning in V17_ENDINGS:
        form=norm(greek.strip('-'))
        if token.endswith(form) and len(token)>len(form)+1:
            add(greek,meaning,'grammatical ending candidate','literal final match',
                token[:-len(form)], 'Grammatical function varies by declension.')
    # Lexical roots from the reviewed starter list; allow common Greek
    # combining forms only when the corresponding stem is explicitly provided.
    stems = {
        'θεός': ('θεο',), 'λόγος': ('λογ',), 'βίος': ('βιο',),
        'γράφω': ('γραφ',), 'φίλος': ('φιλ',), 'φόβος': ('φοβ',),
        'κράτος': ('κρατ',), 'ἀφρός': ('αφρο',), 'νύξ': ('νυκτ',),
        'φῶς': ('φωτ',),
    }
    for p in ROOTS:
        forms = [norm(p.greek)] + list(stems.get(p.greek, ()))
        for form in forms:
            if len(form)<3 or form not in token:
                continue
            if form == token:
                add(p.greek,p.meaning,'whole word / root comparison',
                    'same normalized spelling', '', p.note)
            elif len(form) >= 3:
                idx = token.find(form)
                add(p.greek,p.meaning,'possible lexical stem',
                    'substring/stem match', token[:idx]+' | '+token[idx+len(form):],
                    'An attested lemma with overlapping letters; the proposed segmentation is unverified. '+p.note)
            break
    # Unresolved splits are shown as boundaries only: no invented meanings.
    if not candidates and len(token)>=5:
        for i in range(2,min(5,len(token)-1)):
            add(token[:i]+' | '+token[i:], '(unresolved: no dictionary meaning assigned)',
                'exploratory spelling split', 'unverified division', '',
                'Both parts require independent lexical verification.')
    return candidates[:18]

_v17_prior_analyze = analyze

def analyze(term, variants=False):
    result = _v17_prior_analyze(term,variants=variants)
    result['dynamic_segmentations'] = _v17_dynamic(term)
    # Preserve existing comparisons and existing AI evidence gate.
    result['candidate_morpheme_meanings'] = list(result.get('candidate_morpheme_meanings') or [])
    existing = {(x.get('greek'), x.get('category')) for x in result['candidate_morpheme_meanings']}
    for piece in result['dynamic_segmentations']:
        if piece['category'] == 'exploratory spelling split':
            continue
        key=(piece['greek'],piece['category'])
        if key not in existing:
            result['candidate_morpheme_meanings'].append(piece)
            existing.add(key)
    result['lsj_lookup'] = _nothos_lsj_lookup(term)
    result['component_lsj_evidence'] = []
    looked = set()
    for piece in result['candidate_morpheme_meanings']:
        if piece.get('category') not in ('lexical comparison', 'possible lexical stem', 'lexical root'):
            continue
        greek = piece.get('greek','').strip('-')
        if not greek or norm(greek) == norm(term) or norm(greek) in looked:
            continue
        looked.add(norm(greek))
        if len(looked)>3:
            break
        evidence = _nothos_lsj_lookup(greek)
        result['component_lsj_evidence'].append({'component':greek, **evidence})
    return result

if __name__ == '__main__':
    raise SystemExit(main())


# NOTHOS_V17_3_ORIGINAL_MEDUSA
def _nothos_original_medusa_banner(output):
    """Reuse the existing NOTHOS terminal artwork without duplicating it."""
    import io
    import contextlib

    try:
        from .terminal import print_banner

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            print_banner()

        banner = buffer.getvalue()
        if banner.strip():
            return banner.rstrip() + "\n\n" + output

    except (ImportError, AttributeError, TypeError):
        pass

    return output



# NOTHOS_V17_4_REAL_MEDUSA
def _nothos_display_real_medusa(output):
    """Display the original NOTHOS Medusa before the etymology report."""
    from .terminal import show_banner
    import sys

    if sys.stdout.isatty():
        show_banner(style="full")

    return output
