# awesome-krita

A list of plugins, themes and tools for Krita. Every entry is checked by hand before it goes in.

**Browse the list: https://awesome-krita.github.io/**

> **Note:** This is a small, hand-kept list. It is not a full index of everything made for Krita.

## Add something

You only need a link.

1. Open a [new submission](../../issues/new?template=submit.yml).
2. Paste the GitHub repo, the Krita Artists topic, or both. Pick a type, one or more categories, and the Krita versions and systems it was tested on. Optionally give a display name and drop in a screenshot, GIF or short video.
3. A pull request is opened for you. If a link doesn't work, a comment on your issue says what to fix.

You can also open a pull request yourself. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Fix or report something

Every entry on the site has a flag button next to its name.

- **Suggest an edit** opens a form with the entry filled in. Fill in only what should change. A pull request is opened for you. If you own the plugin's repo, it's marked `author` and reviewed first.
- **Report a problem** is for broken downloads, wrong details or things that don't belong here. Nothing is removed only because of a report.
- **If something may harm people's computers or files**, use [private reporting](../../security/advisories/new), not a public issue.

## How entries are checked

Nobody can promise that a plugin is safe, but every entry goes through this before it's listed:

- **Automatic:** the links must work, and the download is opened and read. Programs inside it, code that runs other programs, uses the internet or unpacks hidden data are listed for the reviewer, with a [VirusTotal](https://www.virustotal.com) link to the exact file.
- **By hand:** a maintainer reads that report and the plugin's code, and checks that the download comes from the author.
- **After:** anyone can [report a problem](../../issues/new?template=report.yml). If something may be harmful, use [private reporting](../../security/advisories/new).

Krita plugins are Python files you can read. If you're unsure about one, open the zip and look, or ask on its repo or forum topic.

## What gets in

- It says which Krita versions it was tested in, and which systems (Windows, macOS, Linux, Android) when that's known.
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

## License

The list itself (`entries/`) is [CC0](entries/LICENSE): anyone can reuse it, no credit needed. The scripts and the site are [MIT](LICENSE). Taking part means following the [code of conduct](CODE_OF_CONDUCT.md).

## For maintainers

How to review entries, handle reports and fix a failed build: [MAINTAINING.md](MAINTAINING.md).


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
- The forms open pull requests as the organization's bot app. Its App ID and private key are the repository secrets `BOT_APP_ID` and `BOT_PRIVATE_KEY`. The app needs read and write access to contents, pull requests and issues, and must be installed on this repository.
- *Settings > Rules > Rulesets*: a ruleset on the default branch that restricts deletions, blocks force pushes, requires the `check` status check and one approving review from code owners (the `maintainers` team, see `.github/CODEOWNERS`). *Organization admin* is on the bypass list (*Always allow*), so owners can push small fixes straight to `main`.
- *Settings > Security*: turn on private vulnerability reporting, for reports about harmful entries.
