"""Tests for the entry checks. No internet needed.

python3 -m unittest discover -s tests
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import add  # noqa: E402
import build  # noqa: E402

GOOD = {"repo": "https://github.com/wojtryb/Shortcut-Composer", "type": "plugin", "category": "workflow"}


class Validate(unittest.TestCase):
    def check(self, entry, stem="shortcut-composer"):
        return build.validate(entry, stem)

    def test_good_entry(self):
        self.assertEqual(self.check(GOOD), [])

    def test_forum_only(self):
        entry = {"forum": "https://krita-artists.org/t/color-mixer-docker/173261/1", "type": "plugin", "category": "color"}
        self.assertEqual(self.check(entry), [])

    def test_needs_a_link(self):
        self.assertIn("needs a `repo` link", self.check({"type": "plugin", "category": "color"})[0])

    def test_wrong_type_and_category(self):
        errors = self.check(GOOD | {"type": "plugins", "category": "colour"})
        self.assertEqual(len(errors), 2)

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
        self.assertEqual((answers["type"], answers["category"]), ("plugin", "workflow"))
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


class RealEntries(unittest.TestCase):
    def test_all_entries_pass(self):
        _, errors = build.load_entries()
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
