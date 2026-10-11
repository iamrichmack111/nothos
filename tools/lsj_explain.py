"""Readable explanations for LSJ dictionary entries."""

import re

ABBREVIATIONS = {
    "pecul.": "peculiar",
    "fem.": "feminine",
    "masc.": "masculine",
    "neut.": "neuter",
    "gen.": "genitive",
    "dat.": "dative",
    "acc.": "accusative",
    "nom.": "nominative",
    "sg.": "singular",
    "pl.": "plural",
    "esp.": "especially",
    "usu.": "usually",
    "cf.": "compare",
    "metaph.": "metaphorically",
    "lit.": "literally",
    "fig.": "figuratively",
    "Adv.": "adverb",
    "Comp.": "comparative",
    "Sup.": "superlative",
    "Dim.": "diminutive",
    "Pass.": "passive",
    "Act.": "active",
}

GREEK_TERMS = {
    "μυστήριον": "mystery, secret rite, or sacred initiation",
    "μυστήρια": "mysteries or sacred rites",
    "μυστηρικός": "relating to mysteries",
    "μυστηρίς": "a feminine form associated with mysteries",
    "μύστης": "an initiate into sacred mysteries",
    "μυέω": "to initiate someone into mysteries",
    "τελετή": "rite, ceremony, or initiation",
    "τελεταί": "rites, ceremonies, or initiations",
    "κρυπτός": "hidden or concealed",
    "ἀπόρρητος": "forbidden to disclose",
    "ἄρρητος": "unspoken or ineffable",
    "αἴνιγμα": "riddle or enigmatic expression",
}


def expand_abbreviations(text):
    """Expand recognized LSJ abbreviations without changing citations."""
    for abbreviation, meaning in ABBREVIATIONS.items():
        text = re.sub(
            rf"(?<!\w){re.escape(abbreviation)}",
            meaning,
            text,
        )
    return text


def explain_entry(lemma, definition):
    """Produce a conservative, readable explanation of an LSJ entry."""

    # Only use the definition for explanations.
    text = expand_abbreviations(definition)

    explanations = []

    if lemma in GREEK_TERMS:
        explanations.append(
            f"Core meaning: {GREEK_TERMS[lemma]}."
        )

    # Explain recognized Greek terms appearing in the entry.
    found = []

    for greek, meaning in GREEK_TERMS.items():
        if greek != lemma and greek in text:
            found.append(f"{greek} = {meaning}")

    if found:
        explanations.append(
            "Related Greek vocabulary: " + "; ".join(found[:8]) + "."
        )

    # Provide a readable excerpt with expanded abbreviations.
    excerpt = text[:900].strip()

    if len(text) > 900:
        excerpt += "…"

    explanations.append(
        "Dictionary explanation (abbreviations expanded): " + excerpt
    )

    return "\n\n".join(explanations)


def explain_with_ollama(lemma, definition):
    """Explain an LSJ entry using a local Ollama language model."""
    import os
    import requests

    url = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
    model = os.getenv("NOTHOS_EXPLAIN_MODEL", "gemma3:4b")

    prompt = f"""You are NOTHOS, an Ancient Greek philology assistant.

Explain the following LSJ Ancient Greek dictionary entry in clear English.

GREEK HEADWORD:
{lemma}

ORIGINAL LSJ ENTRY:
{definition}

Instructions:
1. Give the principal English meaning.
2. Explain grammatical information and important abbreviations.
3. Translate Greek examples when their meaning is sufficiently clear.
4. Explain historical, religious, mythological, or medical meanings where present.
5. Distinguish different senses and historical periods.
6. Explain relevant Greek roots only when supported by the entry.
7. Identify significant ancient authors and references.
8. Do not invent translations, citations, etymologies, or historical claims.
9. If something is uncertain, say so.
10. Keep the explanation readable and organized.

Use these headings:

CORE MEANING
GRAMMAR AND ROOTS
GREEK EXAMPLES
HISTORICAL AND CULTURAL CONTEXT
ANCIENT REFERENCES
"""

    response = requests.post(
        f"{url}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 900,
            },
        },
        timeout=240,
    )

    response.raise_for_status()
    return response.json().get("response", "").strip()
