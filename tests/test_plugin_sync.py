#!/usr/bin/env python3
"""The plugin bundle must never drift from the source — a card-rot guard turned on arlo
itself. The Claude Code plugin ships a self-contained copy of the core under
plugins/arlo/skills/start/ (it must be committed so `/plugin marketplace add` installs a
complete plugin). A committed copy can rot; this test makes drift a failing test, not a
silent bug. Regenerate with `scripts/regen-plugin.sh`. Hermetic, stdlib only.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
PLUGIN = os.path.join(ROOT, "plugins", "arlo", "skills", "start")


class PluginSync(unittest.TestCase):
    def test_core_is_byte_identical(self):
        src = os.path.join(ROOT, "arlo")
        dst = os.path.join(PLUGIN, "arlo")
        names = sorted(f for f in os.listdir(src) if f.endswith(".py"))
        self.assertTrue(names, "no core modules found")
        for n in names:
            with open(os.path.join(src, n), "rb") as f:
                a = f.read()
            p = os.path.join(dst, n)
            self.assertTrue(os.path.isfile(p), f"plugin missing {n} — run scripts/regen-plugin.sh")
            with open(p, "rb") as f:
                b = f.read()
            self.assertEqual(a, b, f"plugin core {n} drifted from source — run scripts/regen-plugin.sh")

    def test_skill_matches_source_modulo_name(self):
        # regen renames the skill frontmatter `name: arlo` -> `name: start`; everything else
        # must be identical, so the shipped skill and the source skill never diverge.
        with open(os.path.join(ROOT, "SKILL.md")) as f:
            root = f.read().replace("name: arlo", "name: start", 1)
        with open(os.path.join(PLUGIN, "SKILL.md")) as f:
            plug = f.read()
        self.assertEqual(root, plug, "plugin SKILL.md drifted from source — run scripts/regen-plugin.sh")


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=0).result
    if result.wasSuccessful():
        print(f"PASS test_plugin_sync ({result.testsRun} cases)")
        sys.exit(0)
    print("FAIL test_plugin_sync")
    sys.exit(1)
