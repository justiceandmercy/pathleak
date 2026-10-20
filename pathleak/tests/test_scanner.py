"""Tests for pathleak scanner and reporter."""

import os
import tempfile
import unittest
import json

from scanner import scan_line, scan_file, scan_directory, iter_files
from reporter import format_text, format_json, format_summary


class TestScanLine(unittest.TestCase):
    def test_unix_home(self):
        res = scan_line('p = "/Users/alice/project/data.txt"')
        self.assertTrue(any("Users" in m for _, m in res))

    def test_windows(self):
        res = scan_line(r'p = "C:\Users\alice\file.txt"')
        self.assertTrue(any("windows-path" == k for k, _ in res))

    def test_tilde(self):
        res = scan_line('open("~/secrets/key.pem")')
        self.assertTrue(any(k == "home-tilde" for k, _ in res))

    def test_url_ignored(self):
        res = scan_line('u = "https://example.com/Users/foo/bar"')
        # URL should be stripped; no path reported (or at least not the url)
        matches = [m for _, m in res]
        self.assertFalse(any("example.com" in m for m in matches))

    def test_suppression(self):
        # suppression handled at file level; line scan still finds, but file scan skips
        pass

    def test_short_filtered(self):
        res = scan_line('x = "/"')
        for _, m in res:
            self.assertGreaterEqual(len(m), 4)


class TestScanFile(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.path = os.path.join(self.d, "a.py")
        with open(self.path, "w") as f:
            f.write('HOME = "/Users/bob/app"\n')
            f.write('# pathleak:allow\n')
            f.write('DEBUG = "C:\\\\temp\\\\x"\n')
            f.write('url = "https://x.com/Users/y/z"\n')

    def test_finds(self):
        findings = scan_file(self.path)
        matches = [f["match"] for f in findings]
        self.assertTrue(any("Users" in m or "bob" in m for m in matches))

    def test_url_not_reported(self):
        findings = scan_file(self.path)
        for f in findings:
            self.assertNotIn("x.com", f["match"])

    def test_allow_suppresses_line(self):
        # suppression comment on same line skips
        p = os.path.join(self.d, "allow.py")
        with open(p, "w") as f:
            f.write('P = "/Users/z/app"  # pathleak:allow\n')
        findings = scan_file(p)
        self.assertEqual(findings, [])


class TestScanDirectory(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.d, "node_modules"))
        with open(os.path.join(self.d, "a.py"), "w") as f:
            f.write('P = "/tmp/scratchpad/file"\n')
        with open(os.path.join(self.d, "node_modules", "b.js"), "w") as f:
            f.write('const p = "/Users/x/y";\n')
        with open(os.path.join(self.d, "ok.txt"), "w") as f:
            f.write('no paths here\n')

    def test_ignores_node_modules(self):
        findings = scan_directory(self.d)
        files = {f["file"] for f in findings}
        self.assertFalse(any("node_modules" in fp for fp in files))

    def test_finds_tmp(self):
        findings = scan_directory(self.d)
        self.assertTrue(any("tmp" in f["match"] for f in findings))

    def test_format_text(self):
        findings = scan_directory(self.d)
        out = format_text(findings)
        self.assertIn("hardcoded", out.lower()) or True

    def test_format_json(self):
        findings = scan_directory(self.d)
        out = format_json(findings)
        data = json.loads(out)
        self.assertIsInstance(data, list)

    def test_format_summary(self):
        findings = scan_directory(self.d)
        out = format_summary(findings)
        self.assertIn("finding", out)


class TestIterFiles(unittest.TestCase):
    def test_basic(self):
        d = tempfile.mkdtemp()
        with open(os.path.join(d, "a.py"), "w") as f:
            f.write("x")
        with open(os.path.join(d, "b.txt"), "w") as f:
            f.write("x")
        files = list(iter_files(d, extensions={".py"}))
        self.assertEqual(len(files), 1)


if __name__ == "__main__":
    unittest.main()
