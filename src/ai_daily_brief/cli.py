"""Command-line entry point for AI Daily Brief."""

from __future__ import annotations

import argparse
from pathlib import Path

from .config import Settings
from .digest import render_html, render_text
from .email_sender import send_report
from .logging_config import configure_logging
from .pipeline import build_daily_report, run_pipeline, run_stage


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ai-brief")
    parser.add_argument(
        "command", choices=("fetch", "process", "digest", "preview", "send", "run"),
        help="pipeline stage to execute",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    args = build_parser().parse_args(argv)
    settings = Settings.from_env()
    if args.command == "run":
        run_pipeline(settings)
    elif args.command in {"preview", "send"}:
        report = build_daily_report(settings)
        if args.command == "preview":
            output_dir = Path("data")
            output_dir.mkdir(exist_ok=True)
            (output_dir / "latest_digest.html").write_text(render_html(report), encoding="utf-8")
            (output_dir / "latest_digest.txt").write_text(render_text(report), encoding="utf-8")
            print(f"Preview written to {output_dir / 'latest_digest.html'}")
        else:
            recipient = send_report(report, settings.recipient)
            print(f"Digest sent to {recipient}")
    else:
        run_stage(args.command, settings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
