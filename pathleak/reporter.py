"""pathleak reporter: format findings as text or JSON."""

import json


def format_text(findings):
    if not findings:
        return "No hardcoded paths found.\n"
    lines = []
    lines.append(f"Found {len(findings)} hardcoded path(s):\n")
    current = None
    for f in findings:
        key = f["file"]
        if key != current:
            current = key
            lines.append(f"\n{key}")
        lines.append(f"  {f['line']}: [{f['kind']}] {f['match']}")
        lines.append(f"      {f['snippet'].strip()}")
    lines.append("")
    return "\n".join(lines)


def format_json(findings):
    return json.dumps(findings, indent=2) + "\n"


def format_summary(findings):
    files = {f["file"] for f in findings}
    kinds = {}
    for f in findings:
        kinds[f["kind"]] = kinds.get(f["kind"], 0) + 1
    parts = [f"{len(findings)} finding(s) in {len(files)} file(s)"]
    if kinds:
        parts.append("by kind: " + ", ".join(f"{k}={v}" for k, v in sorted(kinds.items())))
    return " | ".join(parts) + "\n"