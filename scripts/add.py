#!/usr/bin/env python3
"""Write a new entry file from one or two links.

python3 scripts/add.py LINK [LINK] --type plugin --category color
python3 scripts/add.py --issue-body FILE     (used by the submission form)

LINK is a GitHub repo, a Krita Artists topic, or one of each.
Prints the new file's path and the entry's name, separated by a tab.
"""
import argparse
import re
import sys
from pathlib import Path

import build

NO_ANSWER = "_No response_"


def parse_issue(body):
    """Read the answers from a GitHub issue form ("### Question" followed by the answer)."""
    answers = {}
    for m in re.finditer(r"^### (.+?)\s*\n(.*?)(?=^### |\Z)", body, re.S | re.M):
        value = m[2].strip()
        answers[m[1].strip()] = "" if value == NO_ANSWER else value
    return {
        "links": [answers.get("GitHub repo", ""), answers.get("Krita Artists topic", "")],
        "type": answers.get("Type", "").lower(),
        "category": answers.get("Category", "").lower(),
    }


def make_entry(links, type_, category):
    entry = {"type": type_, "category": category}
    for link in filter(None, (l.strip() for l in links)):
        if build.REPO_RE.match(link):
            entry["repo"] = link.rstrip("/")
        elif build.FORUM_RE.match(link):
            entry["forum"] = link.rstrip("/")
        else:
            raise SystemExit(f"Not a GitHub repo or Krita Artists topic link: {link}")
    return entry


def file_name(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def to_toml(entry):
    order = ["repo", "forum", "type", "category"]
    return "".join(f'{k} = "{entry[k]}"\n' for k in order if k in entry)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("links", nargs="*")
    p.add_argument("--type", default="plugin")
    p.add_argument("--category", default="other")
    p.add_argument("--issue-body")
    args = p.parse_args()

    if args.issue_body:
        answers = parse_issue(Path(args.issue_body).read_text(encoding="utf-8"))
        entry = make_entry(answers["links"], answers["type"], answers["category"])
    else:
        entry = make_entry(args.links, args.type, args.category)

    stem = "new-entry"
    errors = build.validate(entry, stem)
    if errors:
        raise SystemExit("\n".join(errors))

    entries, _ = build.load_entries()
    dup = [msg for stem, msg in build.find_duplicates(entries | {"~new": entry}) if stem == "~new"]
    if dup:
        raise SystemExit("Already listed: " + dup[0].removeprefix("same link as "))

    info = build.fetch(entry)
    stem = file_name(info["name"])
    path = build.ENTRIES / f"{stem}.toml"
    if path.exists():
        raise SystemExit(f"{path.relative_to(build.ROOT)} already exists. Rename it or pick another name.")
    path.write_text(to_toml(entry), encoding="utf-8")
    print(f"{path.relative_to(build.ROOT)}\t{info['name']}")


if __name__ == "__main__":
    sys.exit(main())
