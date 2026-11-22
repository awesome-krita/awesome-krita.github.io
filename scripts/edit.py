#!/usr/bin/env python3
"""Change an existing entry file from a "Suggest an edit" form answer.

python3 scripts/edit.py --issue-body FILE --author GITHUB_LOGIN

Prints the entry's path, its name, and "author" if the person asking owns the entry's repo,
separated by tabs.
"""
import argparse
import tomllib
from pathlib import Path

import add
import build


def changes_from(answers):
    """The keys the form asks to change. Unanswered questions change nothing."""
    get = lambda q: answers.get(q, "").strip()
    changes = {
        "name": get("Display name"),
        "description": " ".join(get("Description").split()),
        "type": get("Type").lower(),
        "category": add.categories(get("Category")),
        "krita": add.split(get("Tested in Krita")),
        "os": add.split(get("Tested on")),
        "image": add.first_link(get("Preview")),
        "download": get("Download link"),
    }
    return {k: v for k, v in changes.items() if v}


def is_author(entry, login):
    """True if `login` owns the GitHub repo of the entry."""
    m = build.REPO_RE.match(entry.get("repo", ""))
    return bool(m and login and m[1].lower() == login.lower())


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--issue-body", required=True)
    p.add_argument("--author", default="")
    args = p.parse_args()

    answers = add.read_answers(Path(args.issue_body).read_text(encoding="utf-8"))
    stem = answers.get("Entry", "").strip()
    path = build.ENTRIES / f"{stem}.toml"
    if not build.FILE_RE.match(stem) or not path.exists():
        raise SystemExit(f'No entry called "{stem}". Use the edit button on the site, it fills this in.')

    changes = changes_from(answers)
    if not changes:
        raise SystemExit("Nothing to change. Fill in at least one field.")

    entry = tomllib.loads(path.read_text(encoding="utf-8"))
    edited = entry | changes
    errors = build.validate(edited, stem)
    if errors:
        raise SystemExit("\n".join(errors))
    if edited == entry:
        raise SystemExit("These values are already in the entry. Nothing to change.")

    path.write_text(add.to_toml(edited), encoding="utf-8")
    name = edited.get("name") or build.fetch(edited)["name"]
    print(f"{path.relative_to(build.ROOT)}\t{name}\t{'author' if is_author(entry, args.author) else ''}")


if __name__ == "__main__":
    main()
