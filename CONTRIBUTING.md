# Contributing

The easiest way is the [submission form](https://github.com/emarpiee/awesome-krita/issues/new?template=submit.yml). It only asks for a link.

## By pull request

Add one file to `entries/`. Name it after the entry, in lowercase with hyphens: `shortcut-composer.toml`.

```toml
repo = "https://github.com/wojtryb/Shortcut-Composer"
forum = "https://krita-artists.org/t/shortcut-composer/12345"
type = "plugin"
category = ["workflow"]
krita = ["5.3", "6"]
os = ["Windows", "Linux"]
```

You need `type`, `category`, `krita`, `os`, and at least one of `repo` or `forum`. Everything else is read from those links.

**Keys**

| Key | Needed | What to put |
|---|---|---|
| `repo` | `repo` or `forum` | A GitHub repo link |
| `forum` | `repo` or `forum` | A Krita Artists topic link |
| `type` | Yes | `plugin`, `theme`, `brushes`, `tool` or `resource` |
| `category` | Yes | One or more, from the list for its type (see below) |
| `name` | No | Use when the repo name doesn't read well |
| `description` | No | One sentence, 160 characters at most. Use when the repo description is missing or unclear |
| `author` | No | Use when the repo owner isn't the person who made it |
| `download` | No | Use when the download isn't on GitHub or in the forum post |
| `image` | No | A picture link, when the README's first picture isn't a good preview |
| `krita` | Yes, for new entries | Krita versions it was tested in. Any of `"6"`, `"5.3"`, `"5.2"`, `"5.1 or older"` |
| `os` | Yes, for new entries | Systems it was tested on. Any of `"Windows"`, `"macOS"`, `"Linux"`, `"Android"` |

`category`, `krita` and `os` are lists, like `krita = ["5.3", "6"]`. Everything else is text in quotes.

Only list what was actually tried. "Tested on Linux" with a working plugin is more useful than "Windows, macOS, Linux" that nobody checked.

**Categories**

Each type has its own categories. Pick every one that fits, like `category = ["color", "workflow"]`.

| Type | Categories |
|---|---|
| `plugin`, `tool`, `resource` | `color`, `workflow`, `layers`, `reference`, `animation`, `export`, `effects`, `other` |
| `theme` | `dark`, `light` |
| `brushes` | `sketching`, `painting`, `inking`, `texture`, `pixel-art` |

A new category needs three changes: `CATEGORIES` in `scripts/build.py`, an option in `.github/ISSUE_TEMPLATE/submit.yml`, and a color in `site/style.css`. The tests fail until all three match.

**Writing descriptions**

- Say what it does, not how good it is. "Pie menus and other complex shortcuts", not "The best shortcut plugin".
- Start with a verb or a noun. Leave out "A Krita plugin that".

## Checks

Every pull request runs these. A ❌ on the pull request means one failed. Click *Details* to see which file and why.

| Check | What it catches |
|---|---|
| File name | Capital letters, spaces or underscores in the name |
| Keys | Missing `type` or `category`, unknown keys, a category that doesn't belong to the type, a Krita version or system that isn't on the list |
| Links | A `repo` that isn't a GitHub repo, a `forum` that isn't a Krita Artists topic, a download link that doesn't work |
| Duplicates | Something that's already listed, by repo or by forum topic |
| Description | Longer than 160 characters |

To run them on your computer:

```
python3 -m unittest discover -s tests
python3 scripts/build.py
```

After the checks pass, the entry is tried in Krita and reviewed by hand before it's merged.
