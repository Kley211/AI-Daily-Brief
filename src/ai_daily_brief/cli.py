"""Command-line entry point for AI Daily Brief."""

from __future__ import annotations

import argparse

from .config import Settings
from .logging_config import configure_logging
from .pipeline import run_pipeline, run_stage


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ai-brief")
    parser.add_argument(
        "command", choices=("fetch", "process", "digest", "run"),
        help="pipeline stage to execute",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    args = build_parser().parse_args(argv)
    settings = Settings.from_env()
    if args.command == "run":
        run_pipeline(settings)
    else:
        run_stage(args.command, settings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
