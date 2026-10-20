#!/usr/bin/env python3
"""pathleak: find hardcoded filesystem paths in source code."""

import argparse
import os
import sys

from scanner import scan_directory, scan_file
from reporter import format_text, format_json, format_summary


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="pathleak",
        description="Find hardcoded filesystem paths in source code.",
    )
    parser.add_argument("path", nargs="?", default=".", help="directory or file to scan")
    parser.add_argument("--format", choices=["text", "json", "summary"], default="text")
    parser.add_argument("--exclude", default="", help="comma-separated dirs to exclude")
    parser.add_argument("--ext", default="", help="comma-separated extensions to include (with dot)")
    parser.add_argument("--min-length", type=int, default=4, help="minimum match length")
    args = parser.parse_args(argv)

    root = args.path
    if not os.path.exists(root):
        print(f"error: path not found: {root}", file=sys.stderr)
        return 2

    extra_ignore = [x.strip() for x in args.exclude.split(",") if x.strip()]
    extensions = None
    if args.ext:
        extensions = set(x.strip() for x in args.ext.split(",") if x.strip())

    if os.path.isfile(root):
        findings = scan_file(root)
    else:
        findings = scan_directory(root, extensions=extensions, extra_ignore=extra_ignore)

    # Apply min-length filter.
    if args.min_length and args.min_length > 0:
        findings = [f for f in findings if len(f["match"]) >= args.min_length]

    if args.format == "json":
        sys.stdout.write(format_json(findings))
    elif args.format == "summary":
        sys.stdout.write(format_summary(findings))
    else:
        sys.stdout.write(format_text(findings))

    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())