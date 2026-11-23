# Maintaining

How to look after the list. For adding entries, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Roles

| Role | Can do |
|---|---|
| Owners | Settings, secrets, adding maintainers. Keep at least two, so the project never gets locked. |
| Maintainers | Review and merge pull requests, label and close issues |
| Everyone | Submit, suggest edits and report problems through the forms |

Every pull request needs one approving review from a maintainer before it's merged. The `check` workflow must pass too.

## Reviewing a new entry

The checks only prove that the file is valid and the links work. A person checks the rest.

- [ ] Open the repo or forum post. It's made for Krita and does what the description says.
- [ ] The download is the real thing: from the author's own repo or post, not a mirror or a file host nobody can trace.
- [ ] Read the **What's inside the downloads** report: open the `check` run on the pull request, then its *Summary*. It lists places in the code worth reading, like running programs, using the internet or `eval`. These are often fine (G'MIC Studio runs `gmic` on purpose), but each should make sense for what the plugin does.
- [ ] Open the report's VirusTotal link. If VirusTotal doesn't know the file, you can upload it there yourself.
- [ ] Be careful with anything that downloads code, runs programs nobody mentioned, or asks for an account or a key.
- [ ] If you can, install it in Krita. Say in your review which version and system you tried.
- [ ] The description says what it does, in one plain sentence. No "best", no "A Krita plugin that".
- [ ] The categories fit and the tested versions and systems look honest.

If something is wrong, ask for a change in the pull request. Small fixes (a typo, a category) you can make yourself in the pull request.

## Edit requests

- `author` on the issue means the person owns the entry's repo. Their changes to name, description and preview can usually be trusted.
- From anyone else, check the change against the repo or forum post before approving.

## Reports

Nothing is removed only because of a report.

| Report | What to do |
|---|---|
| The download doesn't work | The daily build also catches this. Fix the link, or ask the author. |
| It doesn't work in Krita | Try it. If it's confirmed, update the tested versions or ask the author. |
| The details are wrong | Fix them through an edit, like any other change |
| It's no longer maintained | If the repo is archived, the site already shows it. Remove only when it no longer works. |
| It's not made for Krita | Check, then remove the entry file if it's true |
| Harmful | Comes in through private reporting, not issues. Remove the entry right away, then look into it. |

To remove an entry, delete its file in `entries/` in a pull request. In the same pull request, add it to `removed.toml` with the reason and the date, so it can't be added again by accident:

```toml
[[removed]]
repo = "https://github.com/owner/name"
reason = "Download replaced by a different program."
date = "2026-11-23"
```

To bring one back, delete its block in `removed.toml` in the pull request that adds it again.

Removing an entry only because it's old or unmaintained doesn't need a `removed.toml` block. That's for entries that shouldn't come back.

## When the daily build fails

The site build runs every day and fails when a link has died. The site keeps its last good version until it's fixed.

1. Open the failed run in the *Actions* tab. The log names the entry and the link.
2. If the entry has a `download` line, it was typed in by hand: remove it to use the automatic link, or replace it. Otherwise ask the author, or remove the entry if the project is gone.

## Labels

| Label | Meaning |
|---|---|
| `submission` | New entry from the form. The pull request is opened automatically. |
| `edit` | Change to an entry. The pull request is opened automatically. |
| `report` | Problem with an entry. Nothing runs, a maintainer looks at it. |
| `author` | Opened by the owner of the entry's repo |
