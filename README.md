# awesome-krita

A list of plugins, themes and tools for Krita. Every entry is checked by hand before it goes in.

**Browse the list: https://emarpiee.github.io/awesome-krita/**

> **Note:** This is a small, hand-kept list. It is not a full index of everything made for Krita.

## Add something

You only need a link.

1. Open a [new submission](https://github.com/emarpiee/awesome-krita/issues/new?template=submit.yml).
2. Paste the GitHub repo, the Krita Artists topic, or both. Pick a type, one or more categories, and the Krita versions and systems it was tested on. Optionally give a display name and drop in a screenshot, GIF or short video.
3. A pull request is opened for you. If a link doesn't work, a comment on your issue says what to fix.

You can also open a pull request yourself. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Fix or report something

Every entry on the site has a flag button next to its name.

- **Suggest an edit** opens a form with the entry filled in. Fill in only what should change. A pull request is opened for you. If you own the plugin's repo, it's marked `author` and reviewed first.
- **Report a problem** is for broken downloads, wrong details or things that don't belong here. Nothing is removed only because of a report.
- **If something may harm people's computers or files**, use [private reporting](https://github.com/emarpiee/awesome-krita/security/advisories/new), not a public issue.

## What gets in

- It says which Krita versions and systems (Windows, macOS, Linux, Android) it was tested on.
- The download is free and needs no account.
- It has a GitHub repo or a Krita Artists topic. Repos without releases are fine.
- It's not already listed.

## How it works

Each entry is one small file in `entries/`, with a link, a type and its categories:

```toml
repo = "https://github.com/wojtryb/Shortcut-Composer"
type = "plugin"
category = ["workflow"]
```

The rest is read from GitHub and Krita Artists when the site is built:

| Detail | From GitHub | From Krita Artists |
|---|---|---|
| Name | Repo name | Topic title |
| Author | Repo owner | Topic author |
| Description | Repo description | First paragraph of the post |
| Picture | The preview from the form if given, else the first picture in the README | Same, else the first picture in the post |
| Download | The link from the form if given, else the zip in the latest release, else a zip of the main branch | Same, else the first download link in the post |
| Stars, license, version, last update | Yes | Last update only |

The site rebuilds after every merge and every Monday, so stars, versions and download links stay current. If a link stops working, the weekly build fails and the list keeps its last good version until it's fixed.

## For maintainers

| Path | What it does |
|---|---|
| `entries/` | One `.toml` file per entry |
| `scripts/build.py` | Checks the entries, reads the details, writes `site/data.json` |
| `scripts/add.py` | Makes a new entry file from a link |
| `scripts/edit.py` | Changes an entry from an edit request |
| `scripts/icons.py` | Copies the icons the site uses into `site/app.js` |
| `site/` | The web page |
| `tests/` | Tests for the checks |
| `.github/workflows/check.yml` | Runs the tests and the build on every pull request |
| `.github/workflows/site.yml` | Builds and publishes the site |
| `.github/workflows/submission.yml` | Turns a submission or edit issue into a pull request, and starts its checks |

```
python3 -m unittest discover -s tests                                     # checks, no internet needed
python3 scripts/add.py https://github.com/owner/name --category color     # add an entry from a link
GITHUB_TOKEN=$(gh auth token) python3 scripts/build.py                    # build site/data.json
python3 -m http.server -d site                                            # preview at http://localhost:8000
```

- Python 3.11 or newer. Nothing to install.
- Without `GITHUB_TOKEN`, GitHub allows about 60 requests an hour. That runs out at around 20 entries.

**One-time GitHub setup**

- *Settings > Pages*: set the source to *GitHub Actions*.
- *Settings > Actions > General*: allow GitHub Actions to create pull requests (for the submission form).
- *Settings > Rules > Rulesets*: a ruleset on the default branch that restricts deletions, blocks force pushes and requires the `check` status check. Add *Repository admin* to the bypass list (*Always allow*), or direct pushes to `main` get rejected.
- Pull requests opened by the forms don't start workflows by themselves, so the *Submission* workflow starts *Check* on them.
- *Settings > Security*: turn on private vulnerability reporting, for reports about harmful entries.
