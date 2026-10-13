"""Unified NOTHOS command-line interface."""

import argparse
import sys

from .doctor import doctor
from .engine import run_research
from .exporters import export, render
from .terminal import show_banner


def main():
    # NOTHOS_V15_ETYMOLOGY_DISPATCH
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
                        print(render(data, args.format))
                else:
                    print(render(data, args.format))

        except (ValueError, RuntimeError) as exc:
            parser.exit(1, f"NOTHOS error: {exc}\n")


if __name__ == "__main__":
    main()
