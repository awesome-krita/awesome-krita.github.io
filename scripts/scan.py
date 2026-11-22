#!/usr/bin/env python3
"""Look inside each entry's download and report what a reviewer should check by hand.

python3 scripts/scan.py [ID ...]     entries to scan (all if none), after scripts/build.py

Writes a Markdown report, also to the GitHub job summary when it runs in Actions.
It never fails the check: many good plugins run programs or use the internet. It points a reviewer
at those places, a person decides.
"""
import hashlib
import io
import json
import os
import re
import sys
import tokenize
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "site" / "data.json"
MAX_BYTES = 50 * 1024 * 1024
MAX_PLACES = 3  # places listed per finding

PROGRAMS = {".exe", ".dll", ".so", ".dylib", ".pyd", ".bat", ".cmd", ".ps1", ".sh", ".msi", ".jar",
            ".scr", ".com", ".vbs", ".bin", ".app"}
# What a reviewer should read. (?<![.\w]) keeps Qt's dialog.exec() and similar method calls out.
PATTERNS = [
    ("Runs other programs", re.compile(r"\bsubprocess\b|\bos\.(system|popen|exec\w*|spawn\w*)\b|\bQProcess\b")),
    ("Runs code made from text", re.compile(r"(?<![.\w])(eval|exec|compile)\s*\(|__import__\s*\(")),
    ("Unpacks hidden data", re.compile(r"base64\.b(64|32|85)decode|\bmarshal\.loads|\bzlib\.decompress")),
    ("Uses the internet", re.compile(r"\burllib\b|\brequests\b|\bhttp\.client\b|\bsocket\b|QNetworkAccessManager")),
    ("Loads native code", re.compile(r"\bctypes\b|\bcffi\b")),
    ("Reads pickled data", re.compile(r"\bpickle\.loads?\b")),
]
LONG_LINE = 1000  # characters; packed or minified code hides what it does


# Token types that are text, not code. FSTRING_MIDDLE is the text part of an f-string (Python 3.12+).
TEXT_TOKENS = {tokenize.STRING, tokenize.COMMENT, getattr(tokenize, "FSTRING_MIDDLE", tokenize.STRING)}


def code_only(text):
    """The lines of a Python file with strings and comments blanked out, so a docstring that mentions
    exec() isn't flagged. Falls back to cutting comments if the file doesn't parse."""
    lines = text.splitlines()
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, SyntaxError):
        return [line.split("#", 1)[0] for line in lines]
    rows = [list(line) for line in lines]
    for tok in tokens:
        if tok.type not in TEXT_TOKENS:
            continue
        (first, start), (last, end) = tok.start, tok.end
        for r in range(first, min(last, len(rows)) + 1):
            row = rows[r - 1]
            for i in range(start if r == first else 0, end if r == last else len(row)):
                if i < len(row):
                    row[i] = " "
    return ["".join(row) for row in rows]


def inspect(data, kind="plugin"):
    """Findings for a zip file's bytes: [(what, where), ...]."""
    findings = []
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = [n for n in z.namelist() if not n.endswith("/")]
        for name in names:
            if Path(name).suffix.lower() in PROGRAMS:
                findings.append(("Contains a program or library", name))
        for name in names:
            if not name.endswith(".py"):
                continue
            text = z.read(name).decode("utf-8", "replace")
            for number, (line, code) in enumerate(zip(text.splitlines(), code_only(text)), 1):
                for what, pattern in PATTERNS:
                    if pattern.search(code):
                        findings.append((what, f"{name}:{number}"))
                if len(line) > LONG_LINE:
                    findings.append(("Very long line, maybe packed code", f"{name}:{number}"))
        if kind == "plugin":
            desktops = [n for n in names if n.endswith(".desktop")]
            if not any("Krita/PythonPlugin" in z.read(n).decode("utf-8", "replace") for n in desktops):
                findings.append(("No Krita plugin description (.desktop) found", "whole zip"))
    return findings


def summarize(findings):
    """{what: [first places], ...} plus how many more, in the order first seen."""
    grouped = {}
    for what, where in findings:
        grouped.setdefault(what, []).append(where)
    return {what: (places[:MAX_PLACES], len(places) - MAX_PLACES) for what, places in grouped.items()}


def download(url):
    req = urllib.request.Request(url, headers={"User-Agent": "awesome-krita"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read(MAX_BYTES + 1)
        return data, r.headers.get_content_type(), r.url


def report(entry):
    lines = [f"### {entry['name']}", ""]
    url = entry["download"]
    try:
        data, content_type, _ = download(url)
    except (urllib.error.URLError, ValueError) as e:
        return lines + [f"Could not download {url} ({e}). Check it by hand.", ""]
    if len(data) > MAX_BYTES:
        return lines + [f"The download is larger than {MAX_BYTES // 2**20} MB. Check it by hand.", ""]
    if not zipfile.is_zipfile(io.BytesIO(data)):
        return lines + [f"The download is not a zip file ({content_type}): {url}. Check it by hand.", ""]

    sha = hashlib.sha256(data).hexdigest()
    name = url.split("?")[0].rsplit("/", 1)[-1] or "download"  # the link's name, not the storage server's
    lines += [f"`{name}`, {len(data) // 1024} KB, sha256 `{sha}` "
              f"([look it up on VirusTotal](https://www.virustotal.com/gui/file/{sha}))", ""]
    findings = summarize(inspect(data, entry.get("type", "plugin")))
    if not findings:
        return lines + ["Nothing stood out.", ""]
    lines += ["| Read this | Where |", "|---|---|"]
    for what, (places, more) in findings.items():
        where = ", ".join(f"`{p}`" for p in places) + (f" and {more} more" if more > 0 else "")
        lines.append(f"| {what} | {where} |")
    return lines + [""]


def main():
    entries = {e["id"]: e for e in json.loads(DATA.read_text())["entries"]}
    ids = sys.argv[1:] or list(entries)
    out = ["## What's inside the downloads", "",
           "Nothing here is a verdict. Read the places listed and decide if they make sense for what the plugin does.", ""]
    for i in ids:
        out += report(entries[i]) if i in entries else [f"### {i}", "", "Not in the built list.", ""]
    text = "\n".join(out)
    print(text)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(text + "\n")


if __name__ == "__main__":
    main()
