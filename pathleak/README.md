# pathleak

Find hardcoded filesystem paths in your source code before they break portability.

## Description

`pathleak` scans a codebase for hardcoded absolute paths — `/Users/...`, `/home/...`, `C:\...`,
`~/...`, `/tmp/...` — that make code non-portable across machines, containers, and CI runners.
Drop it into CI or a pre-commit hook to catch environment-specific paths before they ship.

## Features

- Multi-language, extension-based file discovery.
- Detects Unix absolute paths, Windows drive paths, and tilde home paths.
- Respects common ignore dirs (`node_modules`, `vendor`, `.git`, ...).
- Suppression via `pathleak:allow` comment.
- Text, JSON, and summary output formats.
- Exit code `1` when matches are found (CI-friendly).

## Install

```sh
git clone https://github.com/yourname/pathleak.git
cd pathleak
python3 pathleak.py --help
```

## Usage

```sh
# Scan current directory
pathleak .

# Scan a path
pathleak src/

# JSON output
pathleak . --format json

# Summary
pathleak . --format summary

# Exclude directories
pathleak . --exclude node_modules,dist

# Allow a line
# path = "/Users/alice/x"  # pathleak:allow
```

## License

MIT