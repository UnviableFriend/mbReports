#!/usr/bin/env python3
"""
MusicBrainz Reports framework entry point.

Usage:
    python reports.py
    python reports.py --list
    python reports.py --report duplicate_isrcs
    python reports.py --category recordings
"""

import argparse
import importlib.util
import sys
from pathlib import Path

from framework.config import load_config
from framework.runner import ReportRunner


def discover_reports(report_dir: Path):
    """Discover Python report modules in the configured reports directory."""
    reports = []

    for path in sorted(report_dir.glob("*.py")):
        if path.name.startswith("_"):
            continue

        module_name = f"report_plugin_{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            print(f"Warning: unable to load {path}", file=sys.stderr)
            continue

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        report_class = getattr(module, "Report", None)
        if report_class is None:
            print(f"Warning: {path} has no Report class", file=sys.stderr)
            continue

        report = report_class()
        reports.append(report)

    return reports


def main():
    parser = argparse.ArgumentParser(description="Generate MusicBrainz reports.")
    parser.add_argument("--list", action="store_true", help="List available reports and exit.")
    parser.add_argument("--report", action="append", help="Run only the named report. May be repeated.")
    parser.add_argument("--category", help="Run only reports in this category.")
    args = parser.parse_args()

    config = load_config("config.yaml")
    report_dir = Path(config["reports"]["directory"])
    if not report_dir.is_absolute():
        report_dir = Path.cwd() / report_dir

    reports = discover_reports(report_dir)

    if args.list:
        for report in reports:
            print(f"{report.id:35} {report.title}")
        return

    runner = ReportRunner(config, reports)
    runner.run(report_ids=args.report, category=args.category)


if __name__ == "__main__":
    main()
