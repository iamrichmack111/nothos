"""Adapters for the existing NOTHOS research engines."""

import contextlib
import io
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_research(query, top_k=8, ai=True, engine="lsj"):
    query = query.strip()
    if not query:
        raise ValueError("Research query cannot be empty")
    if not 1 <= top_k <= 100:
        raise ValueError("top_k must be between 1 and 100")
    if engine not in ("lsj", "mythology"):
        raise ValueError("Engine must be lsj or mythology")

    if engine == "lsj" and not ai:
        sys.path.insert(0, str(ROOT / "tools"))
        from lsj_rag import retrieve

        # Suppress any decorative terminal output in structured responses.
        with contextlib.redirect_stdout(io.StringIO()):
            results = retrieve(query, top_k=top_k)

        return {
            "query": query,
            "engine": engine,
            "ai": False,
            "results": results,
            "report": "",
        }

    if engine == "mythology" and not ai:
        raise ValueError("--no-ai is currently supported only for LSJ")

    if engine == "lsj":
        command = [
            sys.executable,
            str(ROOT / "tools" / "lsj_rag.py"),
            query,
            "--top-k",
            str(top_k),
        ]
    else:
        command = [
            sys.executable,
            str(ROOT / "nothos.py"),
            "ask",
            query,
        ]

    env = os.environ.copy()
    env["NOTHOS_NO_BANNER"] = "1"
    env["NO_COLOR"] = "1"

    result = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=600,
    )

    if result.returncode:
        raise RuntimeError(
            result.stderr.strip()
            or result.stdout.strip()
            or f"Research process exited with code {result.returncode}"
        )

    return {
        "query": query,
        "engine": engine,
        "ai": True,
        "results": [],
        "report": result.stdout,
    }
