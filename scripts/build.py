#!/usr/bin/env python3
"""Check every file in entries/, fill in the details from GitHub and Krita Artists, write site/data.json.

python3 scripts/build.py           check, fetch and write
python3 scripts/build.py --check   only check the entry files (no internet)

Set GITHUB_TOKEN to avoid GitHub's rate limit (60 requests an hour without it).
"""
import json
import os
import re
import sys
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRIES = ROOT / "entries"
OUT = ROOT / "site" / "data.json"

TYPES = {"plugin": "Plugins", "theme": "Themes", "brushes": "Brushes", "tool": "Tools", "resource": "Resources"}
WHAT_IT_DOES = {
    "color": "Color",
    "workflow": "Workflow",
    "layers": "Layers",
    "reference": "Reference",
    "animation": "Animation",
    "export": "Export",
    "effects": "Effects",
    "other": "Other",
}
# Each type has its own categories. A new category also needs a color in site/style.css
# and an option in .github/ISSUE_TEMPLATE/submit.yml (the tests check both).
CATEGORIES = {
    "plugin": WHAT_IT_DOES,
    "tool": WHAT_IT_DOES,
    "resource": WHAT_IT_DOES,
    "theme": {"dark": "Dark", "light": "Light"},
    "brushes": {"sketching": "Sketching", "painting": "Painting", "inking": "Inking", "texture": "Texture", "pixel-art": "Pixel art"},
}
ALL_CATEGORIES = {k: v for cats in CATEGORIES.values() for k, v in cats.items()}
# How categories read in the submission form: "Color", "Dark (theme)", "Inking (brushes)".
FORM_CATEGORIES = {}
for _type, _cats in CATEGORIES.items():
    for _key, _label in _cats.items():
        FORM_CATEGORIES.setdefault(_label if _cats is WHAT_IT_DOES else f"{_label} ({_type})", _key)
KRITA = ["6", "5.3", "5.2", "5.1 or older"]
SYSTEMS = ["Windows", "macOS", "Linux", "Android"]
LISTS = {"category": ALL_CATEGORIES, "krita": KRITA, "os": SYSTEMS}  # keys that hold a list of choices
KEYS = {"repo", "forum", "type", "name", "description", "author", "download", "image", *LISTS}
MAX_DESCRIPTION = 160

REPO_RE = re.compile(r"^https://github\.com/([\w.-]+)/([\w.-]+?)(?:\.git)?/?$")
# The topic name is optional and never all digits, so /t/173261/4 is topic 173261, post 4.
FORUM_RE = re.compile(r"^https://krita-artists\.org/t/(?:(?!\d+/)[^/]+/)?(\d+)(?:/\d+)?/?$")
FILE_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
BADGE_RE = re.compile(r"shields\.io|badge|/actions/workflows/|ko-fi\.com/img|buymeacoffee", re.I)


# --- checking --------------------------------------------------------------

def validate(entry, stem):
    """Return a list of problems with one entry. Empty means it's fine."""
    errors = []
    if not FILE_RE.match(stem):
        errors.append("file name must be lowercase words joined by hyphens, like shortcut-composer.toml")
    unknown = sorted(set(entry) - KEYS)
    if unknown:
        errors.append(f"unknown keys: {', '.join(unknown)}. Allowed: {', '.join(sorted(KEYS))}")
    for key, value in entry.items():
        if key in LISTS:
            allowed = LISTS[key]
            if not isinstance(value, list) or not value or any(v not in allowed for v in value):
                choices = ", ".join(f'"{v}"' for v in allowed)
                errors.append(f"`{key}` must be a list with some of: {choices}. Example: {key} = [{choices.split(', ')[0]}]")
        elif not isinstance(value, str):
            errors.append(f"`{key}` must be text in quotes")
    if errors:
        return errors

    if entry.get("type") not in TYPES:
        errors.append(f"`type` must be one of: {', '.join(TYPES)}")
    elif "category" not in entry:
        errors.append("missing `category`")
    else:
        allowed = CATEGORIES[entry["type"]]
        wrong = [c for c in entry["category"] if c not in allowed]
        if wrong:
            choices = ", ".join(f'"{c}"' for c in allowed)
            errors.append(f"category {', '.join(wrong)} is not for a {entry['type']}. Pick from: {choices}")
    if "repo" not in entry and "forum" not in entry:
        errors.append("needs a `repo` link, a `forum` link, or both")
    if "repo" in entry and not REPO_RE.match(entry["repo"]):
        errors.append("`repo` must be a GitHub repo link, like https://github.com/owner/name")
    if "forum" in entry and not FORUM_RE.match(entry["forum"]):
        errors.append("`forum` must be a Krita Artists topic link, like https://krita-artists.org/t/name/12345")
    for key in ("download", "image"):
        if key in entry and not entry[key].startswith("https://"):
            errors.append(f"`{key}` must start with https://")
    if len(entry.get("description", "")) > MAX_DESCRIPTION:
        errors.append(f"`description` is longer than {MAX_DESCRIPTION} characters")
    return errors


def link_key(entry):
    """What makes two entries the same thing."""
    keys = []
    if m := REPO_RE.match(entry.get("repo", "")):
        keys.append(f"{m[1]}/{m[2]}".lower())
    if m := FORUM_RE.match(entry.get("forum", "")):
        keys.append(f"forum {m[1]}")
    return keys


def find_duplicates(entries):
    """entries: {stem: entry}. Returns problems for links listed twice."""
    seen, errors = {}, []
    for stem, entry in sorted(entries.items()):
        for key in link_key(entry):
            if key in seen:
                errors.append((stem, f"same link as entries/{seen[key]}.toml"))
            else:
                seen[key] = stem
    return errors


def load_entries():
    entries, errors = {}, []
    for path in sorted(ENTRIES.glob("*")):
        if path.name == "LICENSE":
            continue
        if path.suffix != ".toml":
            errors.append((path.stem, f"{path.name} is not a .toml file"))
            continue
        try:
            entry = tomllib.loads(path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as e:
            errors.append((path.stem, f"not valid TOML: {e}"))
            continue
        errors += [(path.stem, msg) for msg in validate(entry, path.stem)]
        entries[path.stem] = entry
    errors += find_duplicates(entries)
    return entries, errors


# --- fetching --------------------------------------------------------------

def get(url, accept="application/json"):
    headers = {"User-Agent": "awesome-krita", "Accept": accept}
    token = os.environ.get("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
        return r.read()


def get_json(url):
    return json.loads(get(url))


def link_works(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "awesome-krita"}), timeout=30):
            return True
    except urllib.error.HTTPError as e:
        return e.code < 400
    except urllib.error.URLError:
        return False


def media_kind(url):
    """"video" or "image", from what the server says it sends. None if the link doesn't work."""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "awesome-krita"}), timeout=30) as r:
            return "video" if r.headers.get_content_type().startswith("video/") else "image"
    except (urllib.error.URLError, ValueError):
        return None


def pretty_name(repo_name):
    """Shortcut-Composer -> Shortcut Composer, PaletteGenerator -> Palette Generator."""
    name = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", repo_name)
    name = re.sub(r"[-_]+", " ", name).strip()
    return name.title() if name.islower() else name


def first_image(markdown, base):
    """The first picture in a README that isn't a badge, as a full URL."""
    pattern = r'!\[[^\]]*\]\(\s*<?([^)\s>]+)|<img[^>]+src=["\']([^"\']+)'
    for m in re.finditer(pattern, markdown, re.I):
        src = m[1] or m[2]
        if BADGE_RE.search(src):
            continue
        url = urllib.parse.urljoin(base, src)
        if re.match(r"^https://github\.com/[^/]+/[^/]+/blob/", url):
            url = url.replace("/blob/", "/raw/", 1)
        return url
    return None


def short_text(html, limit=MAX_DESCRIPTION):
    """The first paragraph of a forum post, cut at a word."""
    paragraph = re.search(r"<p>(.*?)</p>", html, re.S)
    text = unescape(re.sub(r"<[^>]+>", "", paragraph[1] if paragraph else html)).strip()
    text = re.sub(r"\s+", " ", text)
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(",.;:") + "..."


def from_github(owner, name):
    repo = get_json(f"https://api.github.com/repos/{owner}/{name}")
    url = repo["html_url"]
    info = {
        "name": pretty_name(repo["name"]),
        "description": repo["description"] or "",
        "author": repo["owner"]["login"],
        "repo": url,
        "license": (repo.get("license") or {}).get("spdx_id"),
        "stars": repo["stargazers_count"],
        "updated": repo["pushed_at"][:10],
        "archived": repo["archived"],
    }
    if info["license"] == "NOASSERTION":
        info["license"] = None

    # Repos without releases get a zip of the main branch.
    try:
        release = get_json(f"https://api.github.com/repos/{owner}/{name}/releases/latest")
        zips = [a for a in release["assets"] if a["name"].lower().endswith(".zip")]
        # One zip: link it directly. Several (one per system) or none: link the release page.
        info["download"] = zips[0]["browser_download_url"] if len(zips) == 1 else release["html_url"]
        info["version"] = release["tag_name"]
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
        info["download"] = f"{url}/archive/refs/heads/{repo['default_branch']}.zip"

    try:
        readme = get(f"https://api.github.com/repos/{owner}/{name}/readme", "application/vnd.github.raw").decode("utf-8", "replace")
        base = f"https://raw.githubusercontent.com/{owner}/{name}/{repo['default_branch']}/"
        info["image"] = first_image(readme, base)
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
    return info


def from_forum(topic_id):
    topic = get_json(f"https://krita-artists.org/t/{topic_id}.json")
    post = topic["post_stream"]["posts"][0]
    links = [unescape(h) for h in re.findall(r'href="([^"]+)"', post["cooked"])]
    download = next(
        (h for h in links if re.search(r"\.zip($|\?)|drive\.google\.com|/releases|gitlab\.com|codeberg\.org", h)),
        None,
    )
    repo = next((h for h in links if REPO_RE.match(h.split("#")[0].split("?")[0])), None)
    return {
        "name": unescape(topic["title"]),
        "description": short_text(post["cooked"]),
        "author": post["username"],
        "forum": f"https://krita-artists.org/t/{topic['slug']}/{topic['id']}",
        "updated": (topic.get("last_posted_at") or post["created_at"])[:10],
        "image": topic.get("image_url"),
        "download": download,
        "repo_in_post": repo,
    }


def fetch(entry):
    """Everything we know about one entry. Values in the entry file win."""
    info = {}
    if m := REPO_RE.match(entry.get("repo", "")):
        info = from_github(m[1], m[2])
    if m := FORUM_RE.match(entry.get("forum", "")):
        forum = from_forum(m[1])
        info["forum"] = forum["forum"]
        if not info.get("repo"):
            info = forum | {k: v for k, v in info.items() if v}
        info["image"] = info.get("image") or forum["image"]
    info.pop("repo_in_post", None)
    info["download"] = info.get("download") or info.get("forum")
    info.update(entry)
    for key, order in LISTS.items():
        if key in info:
            info[key] = sorted(set(info[key]), key=list(order).index)
    return {k: v for k, v in info.items() if v not in (None, "")}


def main():
    entries, errors = load_entries()
    if "--check" in sys.argv[1:] or errors:
        for stem, msg in errors:
            print(f"entries/{stem}.toml: {msg}", file=sys.stderr)
        print(f"{len(entries)} entries, {len(errors)} problems")
        sys.exit(1 if errors else 0)

    out, failed = [], []
    for stem, entry in sorted(entries.items()):
        try:
            info = fetch(entry)
        except (urllib.error.URLError, KeyError, ValueError) as e:
            failed.append(f"entries/{stem}.toml: could not read its links ({e})")
            continue
        if not link_works(info["download"]):
            failed.append(f"entries/{stem}.toml: download link does not work: {info['download']}")
        if info.get("image"):
            kind = media_kind(info["image"])
            if kind is None and "image" in entry:
                failed.append(f"entries/{stem}.toml: image link does not work: {info['image']}")
            elif kind is None:
                del info["image"]  # a broken picture in someone's README shouldn't block the build
            elif kind == "video":
                info["video"] = True
        out.append({"id": stem, **info})

    if failed:
        print("\n".join(failed), file=sys.stderr)
        sys.exit(1)

    out.sort(key=lambda e: e["name"].lower())
    data = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "types": TYPES,
        "categories": ALL_CATEGORIES,
        "category_types": {t: list(cats) for t, cats in CATEGORIES.items()},
        "krita": KRITA,
        "systems": SYSTEMS,
        "entries": out,
    }
    OUT.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} with {len(out)} entries")


if __name__ == "__main__":
    main()
