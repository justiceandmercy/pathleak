"""pathleak scanner: find hardcoded filesystem paths in source code."""

import os
import re

DEFAULT_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java",
    ".rb", ".php", ".c", ".cpp", ".h", ".cs", ".sh", ".yml",
    ".yaml", ".json", ".toml", ".ini", ".cfg", ".env", ".md",
}

DEFAULT_IGNORE_DIRS = {
    ".git", "node_modules", "vendor", "venv", ".venv", "__pycache__",
    "dist", "build", "target", ".next", ".cache",
}

# Patterns that suggest a hardcoded filesystem path.
PATTERNS = [
    # Unix absolute paths with at least one more segment.
    (re.compile(r"(?<![A-Za-z0-9_])/(?:home|Users|tmp|var|opt|etc|usr|root|mnt|Volumes)/[^\s\"'`<>)]+"), "unix-absolute"),
    # Generic multi-segment absolute path that ends in a file extension.
    (re.compile(r"(?<![A-Za-z0-9_])/[a-zA-Z0-9_.-]+(?:/[a-zA-Z0-9_.-]+)+\.[a-zA-Z0-9]{1,8}"), "unix-file"),
    # Windows drive paths.
    (re.compile(r"[A-Za-z]:\\[^\s\"'`<>)]+"), "windows-path"),
    # Home shorthand.
    (re.compile(r"(?<![A-Za-z0-9_])~/(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+"), "home-tilde"),
]

# Things that look like paths but are usually fine/URLs.
URL_RE = re.compile(r"https?://", re.IGNORECASE)


def _is_ignored_dir(name):
    return name in DEFAULT_IGNORE_DIRS or name.startswith(".")


def iter_files(root, extensions=None, extra_ignore=None):
    extensions = extensions or DEFAULT_EXTENSIONS
    ignore = set(DEFAULT_IGNORE_DIRS)
    if extra_ignore:
        ignore |= set(extra_ignore)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ignore and not d.startswith(".")]
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext in extensions:
                yield os.path.join(dirpath, fn)


def scan_line(line, path_patterns=None):
    """Return list of (pattern_name, matched_text) for a single line."""
    patterns = path_patterns or PATTERNS
    results = []
    if URL_RE.search(line):
        # Strip URL substrings before matching to avoid false positives.
        line = URL_RE.sub("", line)
    for regex, name in patterns:
        for m in regex.finditer(line):
            text = m.group(0).rstrip(".,;:")
            if len(text) < 4:
                continue
            results.append((name, text, m.start(), m.end()))
    # Dedup by position: keep first pattern's match for overlapping spans.
    results.sort(key=lambda r: (r[2], r[3]))
    kept = []
    for name, text, s, e in results:
        overlap = False
        for _, _, ks, ke in kept:
            if not (e <= ks or s >= ke):  # overlaps
                overlap = True
                break
        if overlap:
            continue
        kept.append((name, text, s, e))
    return [(n, t) for n, t, _, _ in kept]


def scan_file(filepath):
    findings = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f, 1):
                stripped = line.strip()
                # Allow suppression comment.
                if "pathleak:allow" in line:
                    continue
                if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("*"):
                    # Still scan comments? Skip pure comment lines to reduce noise.
                    pass
                matches = scan_line(line)
                for name, text in matches:
                    findings.append({
                        "file": filepath,
                        "line": i,
                        "kind": name,
                        "match": text,
                        "snippet": line.rstrip("\n")[:200],
                    })
    except (OSError, IOError):
        return findings
    return findings


def scan_directory(root, extensions=None, extra_ignore=None):
    findings = []
    for filepath in iter_files(root, extensions=extensions, extra_ignore=extra_ignore):
        findings.extend(scan_file(filepath))
    return findings