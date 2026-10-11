"""Unified NOTHOS command-line interface."""

import argparse
import sys

from .doctor import doctor
from .engine import run_research
from .exporters import export, render
from .terminal import show_banner


def main():
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
                print(render(data, args.format))

        except (ValueError, RuntimeError) as exc:
            parser.exit(1, f"NOTHOS error: {exc}\n")


if __name__ == "__main__":
    main()
