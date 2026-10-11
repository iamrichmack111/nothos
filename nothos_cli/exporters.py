"""NOTHOS research report exporters."""

import html
import json
from pathlib import Path


def render(data, fmt="text"):
    report = data.get("report", "")

    if fmt == "json":
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)

    if fmt == "text":
        if report:
            return report

        lines = [
            f"NOTHOS Research: {data.get('query', '')}",
            "",
        ]

        for i, item in enumerate(data.get("results", []), 1):
            lemma = item.get("lemma", item.get("word", item.get("title", "")))
            definition = item.get(
                "definition",
                item.get("body", item.get("meaning", "")),
            )

            lines.append(f"[{i}] {lemma}")
            lines.append(str(definition))
            lines.append("")

        return "\n".join(lines)

    if fmt == "markdown":
        body = report or render(data, "text")

        return (
            f"# NOTHOS Research: {data.get('query', '')}\n\n"
            "## Research Output\n\n"
            "```text\n"
            + body.replace("```", "'''")
            + "\n```\n"
        )

    if fmt == "html":
        body = report or render(data, "text")

        return (
            "<!doctype html>"
            "<html lang='en'>"
            "<head>"
            "<meta charset='utf-8'>"
            "<title>NOTHOS Research</title>"
            "<style>"
            "body{background:#101018;color:#eee;"
            "font:16px/1.6 system-ui;max-width:1000px;"
            "margin:40px auto;padding:20px}"
            "h1{color:#d4af37}"
            "pre{white-space:pre-wrap;overflow-wrap:anywhere}"
            "</style>"
            "</head>"
            "<body>"
            "<h1>🏛️ NOTHOS Research</h1>"
            "<pre>"
            + html.escape(body)
            + "</pre>"
            "</body></html>"
        )

    raise ValueError(f"Unsupported format: {fmt}")


def export(data, fmt, output):
    content = render(data, fmt)

    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    return path
