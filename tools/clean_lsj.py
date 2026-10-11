from nothos_theme import banner, YELLOW, GREEN, CYAN, RESET
import re
import sys
import sqlite3
import unicodedata
import betacode
from pathlib import Path

DB = Path("data/dictionaries/lsj.sqlite3")

# Match Greek Beta Code words, including accent/breathing markers.
BETA_WORD = re.compile(
    r"(?<![A-Za-z])"
    r"(?=[A-Za-z()\\/=+|_*'-]*[()/\\=+|_*])"
    r"[A-Za-z()\\/=+|_*'-]+"
    r"(?![A-Za-z])"
)


def convert_beta(text):
    """Conservatively convert Greek Beta Code without altering English."""

    import re
    import betacode

    # Common English words and LSJ scholarly abbreviations.
    protected = {
        "of", "in", "on", "or", "to", "the", "and", "for",
        "with", "from", "by", "as", "at", "is", "are",
        "sc", "cf", "euphem", "esp", "usu", "pl", "sg",
        "metaph", "later", "first", "secret", "mystery",
        "samothrace", "pessinus", "andania",
        "ad", "bc", "b", "c", "d", "a",
    }

    def replace(match):
        token = match.group(0)

        # Remove punctuation to inspect the underlying word.
        plain = re.sub(r"[^A-Za-z]", "", token).lower()

        if plain in protected:
            return token

        # Greek Beta Code must contain a meaningful diacritic marker.
        if not re.search(r"[/\\\\=()|+*]", token):
            return token

        # Avoid converting isolated citation fragments.
        if len(plain) < 2:
            return token

        try:
            return betacode.conv.beta_to_uni(token)
        except Exception:
            return token

    return BETA_WORD.sub(replace, text)

def clean_definition(text):
    text = convert_beta(text)
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def transliterate(greek):
    import unicodedata

    letters = {
        "α":"a", "β":"b", "γ":"g", "δ":"d",
        "ε":"e", "ζ":"z", "η":"ē", "θ":"th",
        "ι":"i", "κ":"k", "λ":"l", "μ":"m",
        "ν":"n", "ξ":"x", "ο":"o", "π":"p",
        "ρ":"r", "σ":"s", "ς":"s", "τ":"t",
        "υ":"y", "φ":"ph", "χ":"kh", "ψ":"ps",
        "ω":"ō"
    }

    greek = unicodedata.normalize("NFD", greek.lower())

    output = []
    for char in greek:
        if unicodedata.combining(char):
            continue
        output.append(letters.get(char, char))

    return "".join(output)


def highlight_definition(text, lemma):
    import re
    import unicodedata

    # Highlight important English meanings.
    meanings = (
        "utter by inspiration",
        "foretell",
        "prophesy",
        "divine",
        "oracle",
        "inspiration",
        "predict",
    )

    green = "\033[1;92m"
    yellow = "\033[1;93m"
    reset = "\033[0m"

    import os
    import sys

    if not sys.stdout.isatty() or "NO_COLOR" in os.environ:
        green = yellow = reset = ""

    # Highlight the Greek lemma, regardless of Unicode normalization.
    normalized_text = unicodedata.normalize("NFC", text)
    normalized_lemma = unicodedata.normalize("NFC", lemma)

    normalized_text = normalized_text.replace(
        normalized_lemma,
        yellow + normalized_lemma + reset
    )

    # Highlight meaning phrases, longest first.
    pattern = re.compile(
        r"\b(" + "|".join(
            re.escape(x) for x in sorted(meanings, key=len, reverse=True)
        ) + r")\b",
        re.IGNORECASE
    )

    return pattern.sub(
        lambda m: green + m.group(0) + reset,
        normalized_text
    )

def lookup(word):
    con = sqlite3.connect(DB)

    key = unicodedata.normalize("NFC", word).casefold()

    rows = con.execute("""
        SELECT greek_lemma, definition, source_file
        FROM entries
        WHERE greek_normalized = ?
        LIMIT 3
    """, (key,)).fetchall()

    if not rows:
        print("No exact LSJ entry found.")
        return

    for lemma, definition, source in rows:
        print("\n" + "═" * 65)
        print(YELLOW + "  🇬🇷 " + unicodedata.normalize("NFC", lemma) + RESET)
        print(CYAN + "  🗣️ Transliteration: " + transliterate(lemma) + RESET)
        print("═" * 65)
        print("\n📜 " + highlight_definition(clean_definition(definition), lemma))
        print("\nSource: LSJ (" + source + ")")

    con.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python tools/clean_lsj.py "λόγος"')
    lookup(sys.argv[1])
