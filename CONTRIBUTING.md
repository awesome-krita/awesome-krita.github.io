# Contributing

The easiest way is the [submission form](https://github.com/emarpiee/awesome-krita/issues/new?template=submit.yml). It only asks for a link.

## By pull request

Add one file to `entries/`. Name it after the entry, in lowercase with hyphens: `shortcut-composer.toml`.

```toml
repo = "https://github.com/wojtryb/Shortcut-Composer"
forum = "https://krita-artists.org/t/shortcut-composer/12345"
type = "plugin"
category = "workflow"
```

You need `type`, `category`, and at least one of `repo` or `forum`. Everything else is read from those links.

**Keys**

| Key | Needed | What to put |
|---|---|---|
| `repo` | `repo` or `forum` | A GitHub repo link |
| `forum` | `repo` or `forum` | A Krita Artists topic link |
| `type` | Yes | `plugin`, `theme`, `brushes`, `tool` or `resource` |
| `category` | Yes | `color`, `workflow`, `layers`, `reference`, `animation`, `export`, `effects` or `other` |
| `name` | No | Use when the repo name doesn't read well |
| `description` | No | One sentence, 160 characters at most. Use when the repo description is missing or unclear |
| `author` | No | Use when the repo owner isn't the person who made it |
| `download` | No | Use when the download isn't on GitHub or in the forum post |
| `image` | No | A picture link, when the README's first picture isn't a good preview |
| `krita` | No | Which Krita versions it works on, like `"5.2+"` |

All values are text in quotes.

**Writing descriptions**

- Say what it does, not how good it is. "Pie menus and other complex shortcuts", not "The best shortcut plugin".
- Start with a verb or a noun. Leave out "A Krita plugin that".

## Checks

Every pull request runs these. A ❌ on the pull request means one failed. Click *Details* to see which file and why.

| Check | What it catches |
|---|---|
| File name | Capital letters, spaces or underscores in the name |
| Keys | Missing `type` or `category`, unknown keys, a type or category that isn't on the list |
| Links | A `repo` that isn't a GitHub repo, a `forum` that isn't a Krita Artists topic, a download link that doesn't work |
| Duplicates | Something that's already listed, by repo or by forum topic |
| Description | Longer than 160 characters |

To run them on your computer:

```
python3 -m unittest discover -s tests
python3 scripts/build.py
```

After the checks pass, the entry is tried in Krita and reviewed by hand before it's merged.
