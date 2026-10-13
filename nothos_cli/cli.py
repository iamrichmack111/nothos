"""Unified NOTHOS command-line interface."""

import argparse
import sys

from .doctor import doctor
from .engine import run_research
from .exporters import export, render
from .terminal import show_banner


def main():
    # NOTHOS_V15_ETYMOLOGY_DISPATCH
    # NOTHOS_V18_OFFLINE_ROUTING: route related concordance before main argparse.
    # Regular research, etymology, and source-free LSJ commands are unchanged.
    # NOTHOS_V18_2_NATIVE_TEMPLE_RENDER
    # Related-word research must use Temple's native terminal renderer.
    # Do not send it through engine.run_research -> generic render().
    import sys as _v182_sys
    if (len(_v182_sys.argv) >= 3
            and _v182_sys.argv[1] == 'research'
            and '--related' in _v182_sys.argv[2:]):
        from .temple_bridge import run as _v182_temple_run
        return _v182_temple_run(_v182_sys.argv[2:])
    import sys as _n18_sys
    if (len(_n18_sys.argv) > 2
            and _n18_sys.argv[1] == 'research'
            and '--related' in _n18_sys.argv[2:]):
        from .temple_bridge import run as _n18_temple_run
        return _n18_temple_run(_n18_sys.argv[2:])
    import sys as _v15_sys
    if len(_v15_sys.argv) > 1 and _v15_sys.argv[1] in ("etymology", "morphology", "roots"):
        from .etymology import main as _v15_etymology_main
        return _v15_etymology_main(_v15_sys.argv[2:])
    # NOTHOS_TEMPLE_BRIDGE_V1
    import sys as _temple_sys
    _temple_argv = _temple_sys.argv[1:]

    if (
        _temple_argv
        and _temple_argv[0] == "research"
        and "--sources" in _temple_argv
    ):
        from .temple_bridge import run as _temple_run
        return _temple_run(_temple_argv[1:])

    # NOTHOS_PRIMARY_V1: opt-in primary text mode; leave existing LSJ route untouched.
    import sys as _nothos_sys
    _nothos_args = _nothos_sys.argv[1:]
    if (_nothos_args and _nothos_args[0] == "research" and
        ("--engine" in _nothos_args and
         _nothos_args[_nothos_args.index("--engine") + 1:_nothos_args.index("--engine") + 2] == ["primary"])):
        from .primary_sources import run as _nothos_primary_run
        return _nothos_primary_run([a for i, a in enumerate(_nothos_args[1:])
                                    if i not in ( _nothos_args[1:].index("--engine"),
                                                  _nothos_args[1:].index("--engine") + 1)])
    parser = argparse.ArgumentParser(
        prog="nothos",
        description=(
            "NOTHOS — Ancient Greek philology, mythology, "
            "semantic search and evidence-aware research"
        ),
    )

    sub = parser.add_subparsers(dest="command", required=True)

    research = sub.add_parser(
        "research",
        help="Research Ancient Greek vocabulary or mythology",
    )
    research.add_argument("query", help="Greek word or research question")
    research.add_argument("--top-k", type=int, default=8)
    research.add_argument(
        "--engine",
        choices=("lsj", "mythology"),
        default="lsj",
    )
    research.add_argument(
        "--no-ai",
        action="store_true",
        help="Return LSJ evidence without generating an AI response",
    )
    research.add_argument(
        "--format",
        choices=("text", "json", "markdown", "html"),
        default="text",
    )
    research.add_argument(
        "-o",
        "--output",
        help="Write report to a file",
    )
    research.add_argument(
        "--banner",
        choices=("auto", "full", "compact", "ascii", "none"),
        default="auto",
    )
    research.add_argument(
        "--full",
        action="store_true",
        help="Show complete LSJ definitions instead of compact results",
    )

    banner = sub.add_parser(
        "banner",
        help="Display the Medusa banner",
    )
    banner.add_argument(
        "--style",
        choices=("auto", "full", "compact", "ascii", "none"),
        default="auto",
    )

    # NOTHOS_V17_6_ETYMOLOGY_HELP
    sub.add_parser(
        "etymology",
        help="Analyze Greek roots, morphology, variants, and LSJ evidence",
        add_help=False,
    )

    sub.add_parser("doctor", help="Diagnose the NOTHOS installation")

    serve = sub.add_parser("serve", help="Start the REST API")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8790)

    args = parser.parse_args()

    if args.command == "doctor":
        doctor()
        return

    if args.command == "banner":
        show_banner(args.style)
        return

    if args.command == "serve":
        import uvicorn

        uvicorn.run(
            "nothos_cli.api:app",
            host=args.host,
            port=args.port,
        )
        return

    if args.command == "research":
        # NOTHOS_FULL_RAG_ROUTE_V1
        if (
            args.engine == "lsj"
            and args.format == "text"
            and not args.output
            and not args.no_ai
            and not args.full
        ):
            import subprocess
            import sys
            from pathlib import Path

            root = Path(__file__).resolve().parent.parent
            script = root / "tools" / "lsj_rag.py"

            command = [
                sys.executable,
                str(script),
                args.query,
                "--top-k",
                str(args.top_k),
            ]

            result = subprocess.run(command, cwd=str(root))
            return result.returncode

        try:
            data = run_research(
                args.query,
                top_k=args.top_k,
                ai=not args.no_ai,
                engine=args.engine,
            )

            if args.output:
                path = export(data, args.format, args.output)
                print(f"Saved: {path}")
            else:
                if args.format == "text":
                    show_banner(args.banner)
                    if (
                        args.engine == "lsj"
                        and args.no_ai
                        and not args.full
                    ):
                        try:
                            from .compact import render_compact
                        except ModuleNotFoundError as exc:
                            if exc.name != "nothos_cli.compact":
                                raise
                            from .temple_bridge import highlight as _v9_hl
                            import sys as _v9_sys
                            _v9_text = render(data, args.format)
                            _v9_color = _v9_sys.stdout.isatty()
                            print(_v9_hl(_v9_text, args.query, _v9_color))
                        else:
                            print(render_compact(data))
                    else:
                        print(_nothos_v181_color_report(render(data, args.format)))
                else:
                    print(render(data, args.format))

        except (ValueError, RuntimeError) as exc:
            parser.exit(1, f"NOTHOS error: {exc}\n")




# NOTHOS_V18_1_PRESENTATION — terminal-only format; no color in file exports.
def _nothos_v181_color_report(report):
    import os, sys, re
    if (not sys.stdout.isatty() or os.environ.get('NO_COLOR') is not None
            or os.environ.get('TERM') == 'dumb'):
        return report
    gold='\033[1;33m'; purple='\033[1;35m'; cyan='\033[1;36m'
    green='\033[1;32m'; reset='\033[0m'
    # Preserve any existing ANSI sequences rather than double-coloring a report.
    if '\033[' in report:
        return report
    out=[]
    for line in report.splitlines(keepends=True):
        lead=line.lstrip()
        if lead.startswith(('🏛️', '🔎 RELATED-WORD OCCURRENCE', '📖 SHARED-PREFIX', '🧠')):
            out.append(purple+line.rstrip('\n')+reset+('\n' if line.endswith('\n') else ''))
        elif lead.startswith(('🔎 QUERY:', '📍 REFERENCE:', '📚 SOURCE:', '📚 Sources:')):
            out.append(cyan+line.rstrip('\n')+reset+('\n' if line.endswith('\n') else ''))
        elif lead.startswith(('⚠', '🛡️')):
            out.append(gold+line.rstrip('\n')+reset+('\n' if line.endswith('\n') else ''))
        elif lead.startswith(('📚 LSJ', '   📚')):
            out.append(green+line.rstrip('\n')+reset+('\n' if line.endswith('\n') else ''))
        elif lead.startswith(('🇬🇷', '🏺 LEMMA:')):
            out.append(gold+line.rstrip('\n')+reset+('\n' if line.endswith('\n') else ''))
        elif lead.startswith(('━','═','─')):
            out.append(purple+line.rstrip('\n')+reset+('\n' if line.endswith('\n') else ''))
        else:
            # Highlight Greek tokens within passage lines, without modifying text content.
            out.append(re.sub(r'[\u0370-\u03ff\u1f00-\u1fff]+(?:[\u0370-\u03ff\u1f00-\u1fff\u0300-\u036f]*)',
                              lambda m: gold+m.group()+reset, line))
    return ''.join(out)

if __name__ == "__main__":
    main()
