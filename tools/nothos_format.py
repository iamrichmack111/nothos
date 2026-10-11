from lsj_explain import explain_with_ollama
from lsj_explain import explain_entry
"""Shared Greek formatting for NOTHOS."""

import re
import sys
import unicodedata

from nothos_theme import (
    GREEN, YELLOW, CYAN, MAGENTA, WHITE, RESET,
    heading, paint, banner,
)

from clean_lsj import clean_definition, transliterate



_banner_shown = False

def ensure_banner():
    """Display Medusa and the NOTHOS banner once per process."""
    global _banner_shown

    if not _banner_shown:
        banner()
        _banner_shown = True




def highlight_lsj(text):
    """Highlight complete Greek words and selected English meanings."""
    import re
    import unicodedata

    text = unicodedata.normalize("NFC", text)

    # Complete Greek words, including accented and polytonic Greek.
    greek_pattern = re.compile(
        r"[\u0370-\u03FF\u1F00-\u1FFF\u0300-\u036F]+"
    )

    meaning_pattern = re.compile(
        r"\b("
        r"mystery|mysteries|secret|secrecy|hidden|concealed|"
        r"initiation|initiating|initiated|sacred|rite|rites|"
        r"divine|revelation|prophecy|oracle|magic|magical|"
        r"talisman|symbol|mystical|mysticism|religious|"
        r"medicine|remedy|knowledge|wisdom|inspiration"
        r")\b",
        re.IGNORECASE
    )

    # Match Greek words or selected English meanings in one pass.
    combined = re.compile(
        f"({greek_pattern.pattern})|({meaning_pattern.pattern})",
        re.IGNORECASE
    )

    def color_match(match):
        word = match.group(0)

        if greek_pattern.fullmatch(word):
            return YELLOW + word + RESET

        return GREEN + word + RESET

    return combined.sub(color_match, text)


def greek_entry(lemma, definition, source=None, similarity=None):
    """Print a complete, selectively highlighted LSJ entry."""
    ensure_banner()

    import unicodedata

    lemma = unicodedata.normalize("NFC", lemma or "")
    definition = clean_definition(definition or "")

    print()
    print(paint("═" * 70, CYAN))
    print(paint(f"🇬🇷  {lemma}", YELLOW))
    print(paint(f"🗣️  Transliteration: {transliterate(lemma)}", CYAN))

    if similarity is not None:
        print(paint(f"🔮  Similarity: {similarity:.3f}", MAGENTA))

    print(paint("═" * 70, CYAN))

    print()
    print(paint("📜 DEFINITION", YELLOW))
    print(highlight_lsj(definition))

    if source:
        print()
        print(paint(f"🏛️ SOURCE: {source}", WHITE))

    print()
    print(paint("📖 PLAIN ENGLISH EXPLANATION", YELLOW))
    print(explain_entry(lemma, definition))



def ai_explanation(lemma, definition):
    """Display an optional AI-generated explanation."""
    import os

    if os.getenv("NOTHOS_AI_EXPLAIN") != "1":
        return

    print()
    print(paint("🧠 OLLAMA — PLAIN ENGLISH EXPLANATION", MAGENTA))

    try:
        explanation = explain_with_ollama(lemma, definition)
        print(paint(explanation, WHITE))
    except Exception as exc:
        print(paint(f"⚠️ AI explanation unavailable: {exc}", YELLOW))


def section(title):
    ensure_banner()
    heading(title)


def ai_response(text):
    """Format an AI-generated response."""
    ensure_banner()
    section("🧠 NOTHOS AI")
    print(paint(text, WHITE))


def corpus_result(title, text, source=None):
    """Format a primary-source search result."""
    ensure_banner()
    print()
    print(paint("═" * 70, CYAN))
    print(paint(f"🏺 {title}", YELLOW))
    print(paint("═" * 70, CYAN))
    print(paint(text, GREEN))

    if source:
        print(paint(f"📜 SOURCE: {source}", WHITE))
