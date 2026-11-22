"""Tests for the entry checks. No internet needed.

python3 -m unittest discover -s tests
"""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import add  # noqa: E402
import build  # noqa: E402
import edit  # noqa: E402
import scan  # noqa: E402

GOOD = {"repo": "https://github.com/wojtryb/Shortcut-Composer", "type": "plugin", "category": ["workflow"]}


class Validate(unittest.TestCase):
    def check(self, entry, stem="shortcut-composer"):
        return build.validate(entry, stem)

    def test_good_entry(self):
        self.assertEqual(self.check(GOOD), [])

    def test_forum_only(self):
        entry = {"forum": "https://krita-artists.org/t/color-mixer-docker/173261/1", "type": "plugin", "category": ["color"]}
        self.assertEqual(self.check(entry), [])

    def test_needs_a_link(self):
        self.assertIn("needs a `repo` link", self.check({"type": "plugin", "category": ["color"]})[0])

    def test_wrong_type(self):
        self.assertIn("`type` must be", self.check(GOOD | {"type": "plugins"})[0])

    def test_category(self):
        self.assertIn("must be a list", self.check(GOOD | {"category": "color"})[0])
        self.assertIn("must be a list", self.check(GOOD | {"category": ["colour"]})[0])
        self.assertIn("must be a list", self.check(GOOD | {"category": []})[0])
        self.assertEqual(self.check(GOOD | {"category": ["color", "workflow"]}), [])

    def test_category_fits_type(self):
        self.assertEqual(self.check(GOOD | {"type": "theme", "category": ["dark"]}), [])
        self.assertIn("not for a theme", self.check(GOOD | {"type": "theme", "category": ["color"]})[0])
        self.assertIn("not for a plugin", self.check(GOOD | {"category": ["inking"]})[0])

    def test_missing_category(self):
        entry = dict(GOOD); del entry["category"]
        self.assertIn("missing `category`", self.check(entry)[0])

    def test_repo_must_be_a_repo(self):
        for bad in ["https://github.com/wojtryb", "https://gitlab.com/a/b", "http://github.com/a/b",
                    "https://github.com/a/b/releases"]:
            with self.subTest(bad):
                self.assertTrue(self.check(GOOD | {"repo": bad}))

    def test_forum_link_forms(self):
        for good in ["https://krita-artists.org/t/layer-kit-organize-your-layers-faster/157281",
                     "https://krita-artists.org/t/color-mixer-docker/173261/1", "https://krita-artists.org/t/173261"]:
            with self.subTest(good):
                self.assertTrue(build.FORUM_RE.match(good))
        self.assertTrue(self.check(GOOD | {"forum": "https://krita-artists.org/c/plugins/12"}))

    def test_file_name(self):
        for bad in ["Shortcut-Composer", "shortcut_composer", "shortcut composer", "-x"]:
            with self.subTest(bad):
                self.assertTrue(self.check(GOOD, bad))

    def test_unknown_key(self):
        self.assertIn("unknown keys: stars", self.check(GOOD | {"stars": "5"})[0])

    def test_values_must_be_text(self):
        self.assertIn("must be text", self.check(GOOD | {"name": 5.2})[0])

    def test_tested_lists(self):
        self.assertEqual(self.check(GOOD | {"krita": ["5.3", "6"], "os": ["Linux", "Windows"]}), [])
        for bad in [{"krita": "5.3"}, {"krita": []}, {"krita": ["5.4"]}, {"os": ["linux"]}, {"os": ["Windows", 10]}]:
            with self.subTest(bad):
                self.assertIn("must be a list", self.check(GOOD | bad)[0])

    def test_description_length(self):
        self.assertTrue(self.check(GOOD | {"description": "x" * 161}))
        self.assertFalse(self.check(GOOD | {"description": "x" * 160}))

    def test_download_must_be_https(self):
        self.assertTrue(self.check(GOOD | {"download": "http://example.com/a.zip"}))


class Duplicates(unittest.TestCase):
    def test_same_repo_any_case(self):
        other = GOOD | {"repo": "https://github.com/WOJTRYB/shortcut-composer/"}
        self.assertEqual(len(build.find_duplicates({"a": GOOD, "b": other})), 1)

    def test_same_forum_topic(self):
        a = {"forum": "https://krita-artists.org/t/x/173261"}
        b = {"forum": "https://krita-artists.org/t/173261/4"}
        self.assertEqual(len(build.find_duplicates({"a": a, "b": b})), 1)

    def test_different(self):
        b = GOOD | {"repo": "https://github.com/wojtryb/Subwindow-Organizer"}
        self.assertEqual(build.find_duplicates({"a": GOOD, "b": b}), [])


class Helpers(unittest.TestCase):
    def test_pretty_name(self):
        self.assertEqual(build.pretty_name("Shortcut-Composer"), "Shortcut Composer")
        self.assertEqual(build.pretty_name("PaletteGenerator"), "Palette Generator")
        self.assertEqual(build.pretty_name("krita-batch-exporter"), "Krita Batch Exporter")
        self.assertEqual(build.pretty_name("Pigment.O"), "Pigment.O")

    def test_first_image_skips_badges(self):
        md = "![ci](https://img.shields.io/x.svg)\n![shot](images/shot.png)"
        self.assertEqual(build.first_image(md, "https://raw.githubusercontent.com/a/b/main/"),
                         "https://raw.githubusercontent.com/a/b/main/images/shot.png")

    def test_first_image_html_and_blob(self):
        md = '<img width="300" src="https://github.com/a/b/blob/main/s.png">'
        self.assertEqual(build.first_image(md, "x"), "https://github.com/a/b/raw/main/s.png")

    def test_first_image_none(self):
        self.assertIsNone(build.first_image("no pictures", "x"))

    def test_short_text(self):
        self.assertEqual(build.short_text("<p>Hello &amp; <b>bye</b></p><p>more</p>"), "Hello & bye")
        self.assertTrue(build.short_text("<p>" + "word " * 100 + "</p>").endswith("..."))


class IssueForm(unittest.TestCase):
    BODY = """### GitHub repo

https://github.com/wojtryb/Shortcut-Composer

### Krita Artists topic

_No response_

### Type

Plugin

### Category

Workflow

### Tested in Krita

5.3, 6

### Tested on

Windows, Linux

### Anything else?

hi
"""

    def test_parse(self):
        answers = add.parse_issue(self.BODY)
        self.assertEqual(answers["links"], ["https://github.com/wojtryb/Shortcut-Composer", ""])
        self.assertEqual((answers["type"], answers["category"]), ("plugin", ["workflow"]))
        self.assertEqual((answers["krita"], answers["os"]), (["5.3", "6"], ["Windows", "Linux"]))

    def test_make_entry(self):
        a = add.parse_issue(self.BODY)
        entry = add.make_entry(a["links"], a["type"], a["category"], a["krita"], a["os"])
        self.assertEqual(entry, GOOD | {"krita": ["5.3", "6"], "os": ["Windows", "Linux"]})
        self.assertEqual(build.validate(entry, "x"), [])

    def test_toml_round_trip(self):
        entry = GOOD | {"krita": ["5.3", "6"], "os": ["Linux"]}
        self.assertEqual(build.tomllib.loads(add.to_toml(entry)), entry)

    def test_bad_link(self):
        with self.assertRaises(SystemExit):
            add.make_entry(["https://example.com"], "plugin", "other")

    def test_file_name(self):
        self.assertEqual(add.file_name("Layer Kit: organize your layers!"), "layer-kit-organize-your-layers")


class RealSubmission(unittest.TestCase):
    """A full form answer as GitHub sends it, for krita-gmic-studio, down to the entry file."""
    BODY = """### GitHub repo

https://github.com/emarpiee/krita-gmic-studio

### Krita Artists topic

_No response_

### Type

Plugin

### Category

Effects

### Tested in Krita

6

### Tested on

Linux

### Anything else?

_No response_

### Before you send

- [X] The download is free and needs no account.
"""

    def test_to_entry_file(self):
        a = add.parse_issue(self.BODY)
        entry = add.make_entry(a["links"], a["type"], a["category"], a["krita"], a["os"])
        self.assertEqual(build.validate(entry, "krita-gmic-studio"), [])
        self.assertEqual(add.to_toml(entry), (
            'repo = "https://github.com/emarpiee/krita-gmic-studio"\n'
            'type = "plugin"\n'
            'category = ["effects"]\n'
            'krita = ["6"]\n'
            'os = ["Linux"]\n'
        ))

    def test_display_name_and_preview(self):
        body = self.BODY.replace("### Type", """### Display name

G'MIC Studio

### Preview

<img width="800" alt="shot" src="https://github.com/user-attachments/assets/abc-123" />

### Type""")
        a = add.parse_issue(body)
        self.assertEqual(a["name"], "G'MIC Studio")
        self.assertEqual(a["image"], "https://github.com/user-attachments/assets/abc-123")
        entry = add.make_entry(a["links"], a["type"], a["category"], a["krita"], a["os"], a["name"], a["image"])
        self.assertEqual(build.validate(entry, "gmic-studio"), [])
        self.assertEqual(build.tomllib.loads(add.to_toml(entry)), entry)
        self.assertEqual(add.file_name(a["name"]), "gmic-studio")

    def test_own_download_link(self):
        body = self.BODY.replace("### Type", "### Download link\n\nhttps://example.com/gmic-studio.zip\n\n### Type")
        a = add.parse_issue(body)
        entry = add.make_entry(a["links"], a["type"], a["category"], a["krita"], a["os"], download=a["download"])
        self.assertEqual(entry["download"], "https://example.com/gmic-studio.zip")
        self.assertEqual(build.validate(entry, "gmic-studio"), [])
        self.assertIn("https://", build.validate(entry | {"download": "ftp://x/a.zip"}, "x")[0])

    def test_preview_forms(self):
        for text, link in [
            ("![demo](https://github.com/user-attachments/assets/1)", "https://github.com/user-attachments/assets/1"),
            ("https://github.com/user-attachments/assets/video-2", "https://github.com/user-attachments/assets/video-2"),
            ("", ""),
            ("no link here", ""),
        ]:
            with self.subTest(text):
                self.assertEqual(add.first_link(text), link)

    def test_names_with_quotes_stay_valid_toml(self):
        entry = GOOD | {"name": 'The "Best" \\ Tool'}
        self.assertEqual(build.tomllib.loads(add.to_toml(entry)), entry)

    def test_windows_line_endings(self):
        a = add.parse_issue(self.BODY.replace("\n", "\r\n"))
        self.assertEqual(a["links"][0], "https://github.com/emarpiee/krita-gmic-studio")
        self.assertEqual((a["krita"], a["os"]), (["6"], ["Linux"]))


class EditForm(unittest.TestCase):
    ENTRY = GOOD | {"description": "Old text.", "krita": ["5.2"], "os": ["Linux"]}

    def body(self, **answers):
        return "\n".join(f"### {q}\n\n{a}\n" for q, a in answers.items())

    def test_only_filled_fields_change(self):
        answers = add.read_answers(self.body(**{"Entry": "shortcut-composer", "Display name": "_No response_",
                                               "Description": "Pie menus\nand shortcuts.", "Tested on": "Linux, Windows"}))
        self.assertEqual(edit.changes_from(answers), {"description": "Pie menus and shortcuts.", "os": ["Linux", "Windows"]})

    def test_category_labels_and_preview(self):
        answers = add.read_answers(self.body(**{"Category": "Dark (theme)", "Type": "Theme",
                                               "Preview": "![x](https://github.com/user-attachments/assets/9)"}))
        self.assertEqual(edit.changes_from(answers), {"type": "theme", "category": ["dark"],
                                                      "image": "https://github.com/user-attachments/assets/9"})

    def test_edited_entry_keeps_every_key(self):
        edited = self.ENTRY | {"name": "Shortcut Composer", "download": "https://example.com/a.zip"}
        self.assertEqual(build.tomllib.loads(add.to_toml(edited)), edited)

    def test_type_change_needs_matching_category(self):
        self.assertIn("not for a theme", build.validate(self.ENTRY | {"type": "theme"}, "shortcut-composer")[0])

    def test_is_author(self):
        self.assertTrue(edit.is_author(GOOD, "wojtryb"))
        self.assertTrue(edit.is_author(GOOD, "WojTryb"))
        self.assertFalse(edit.is_author(GOOD, "someone"))
        self.assertFalse(edit.is_author({"forum": "https://krita-artists.org/t/x/1"}, "wojtryb"))
        self.assertFalse(edit.is_author(GOOD, ""))


class FormCategories(unittest.TestCase):
    def test_theme_and_brush_labels(self):
        body = IssueForm.BODY.replace("Plugin", "Theme").replace("\nWorkflow\n", "\nDark (theme), Light (theme)\n")
        self.assertEqual(add.parse_issue(body)["category"], ["dark", "light"])


class InSync(unittest.TestCase):
    """The form and the site's colors must offer the same choices as build.py."""
    ROOT = Path(__file__).resolve().parent.parent

    def form_options(self, field_id, form="submit.yml"):
        form = (self.ROOT / ".github/ISSUE_TEMPLATE" / form).read_text()
        block = re.search(rf"id: {field_id}\n(.*?)(?=\n  - type:|\Z)", form, re.S)[1]
        line = re.search(r"options: \[(.*)\]", block)[1]
        return [o.strip().strip('"') for o in line.split(",")]

    def test_form_types(self):
        self.assertEqual([o.lower() for o in self.form_options("type")], list(build.TYPES))

    def test_form_categories(self):
        self.assertEqual(self.form_options("category"), list(build.FORM_CATEGORIES))

    def test_form_krita_and_os(self):
        self.assertEqual(self.form_options("krita"), build.KRITA)
        self.assertEqual(self.form_options("os"), build.SYSTEMS)

    def test_edit_form_matches(self):
        for field in ("type", "category", "krita", "os"):
            with self.subTest(field):
                self.assertEqual(self.form_options(field, "edit.yml"), self.form_options(field))

    def test_forms_ask_for_a_download_link(self):
        for form in ("submit.yml", "edit.yml"):
            with self.subTest(form):
                self.assertIn("label: Download link", (self.ROOT / ".github/ISSUE_TEMPLATE" / form).read_text())

    def test_site_buttons_fill_the_entry_field(self):
        for form in ("edit.yml", "report.yml"):
            with self.subTest(form):
                self.assertIn("id: entry", (self.ROOT / ".github/ISSUE_TEMPLATE" / form).read_text())
        self.assertIn('"edit.yml"', (self.ROOT / "site/app.js").read_text())
        self.assertIn('"report.yml"', (self.ROOT / "site/app.js").read_text())

    def test_every_category_has_a_color(self):
        css = (self.ROOT / "site/style.css").read_text()
        light, dark = css.split("prefers-color-scheme: dark", 1)
        for key in build.ALL_CATEGORIES:
            with self.subTest(key):
                self.assertIn(f"--{key}:", light)
                self.assertIn(f"--{key}:", dark)


def make_zip(files):
    import io, zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, text in files.items():
            z.writestr(name, text)
    return buf.getvalue()


class Scan(unittest.TestCase):
    DESKTOP = {"tool.desktop": "[Desktop Entry]\nServiceTypes=Krita/PythonPlugin\n"}

    def found(self, files, kind="plugin"):
        return {what for what, _ in scan.inspect(make_zip(self.DESKTOP | files), kind)}

    def test_clean_plugin(self):
        self.assertEqual(self.found({"tool/__init__.py": "from krita import *\ndialog.exec()\nwin.exec_()\n"}), set())

    def test_flags_what_to_read(self):
        found = self.found({"tool/a.py": "import subprocess\nx = eval(text)\nimport urllib.request\n",
                            "tool/b.py": "data = base64.b64decode(s)\n", "tool/helper.dll": "MZ"})
        self.assertEqual(found, {"Runs other programs", "Runs code made from text", "Uses the internet",
                                 "Unpacks hidden data", "Contains a program or library"})

    def test_comments_are_ignored(self):
        self.assertEqual(self.found({"tool/a.py": "# we never eval(anything) or use subprocess\n"}), set())

    def test_text_is_ignored(self):
        source = 'def run(d):\n    """Run with exec(), or subprocess if needed."""\n    msg = "eval(x)"\n    return f"{msg} exec("\n'
        self.assertEqual(self.found({"tool/a.py": source}), set())

    def test_code_after_text_still_counts(self):
        self.assertIn("Runs code made from text", self.found({"tool/a.py": 'x = "1+1"; y = eval(x)\n'}))

    def test_broken_file_still_scanned(self):
        self.assertIn("Runs other programs", self.found({"tool/a.py": "def (:\nimport subprocess\n"}))

    def test_packed_code(self):
        self.assertIn("Very long line, maybe packed code", self.found({"tool/a.py": "x = '" + "a" * 1200 + "'\n"}))

    def test_missing_plugin_description(self):
        data = make_zip({"tool/__init__.py": "pass\n"})
        self.assertIn("No Krita plugin description (.desktop) found", {w for w, _ in scan.inspect(data, "plugin")})
        self.assertEqual(scan.inspect(data, "theme"), [])

    def test_summary_keeps_first_places(self):
        s = scan.summarize([("Uses the internet", f"a.py:{n}") for n in range(1, 6)])
        self.assertEqual(s["Uses the internet"], (["a.py:1", "a.py:2", "a.py:3"], 2))


class RealEntries(unittest.TestCase):
    def test_all_entries_pass(self):
        _, errors = build.load_entries()
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
