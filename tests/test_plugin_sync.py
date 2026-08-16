#!/usr/bin/env python3
"""The plugin bundle must never drift from its sources — a card-rot guard turned on arlo
itself. arlo ships a lifecycle of skills (start, setup, update, remove) under
plugins/arlo/skills/, each a self-contained copy that must be committed so
`/plugin marketplace add` installs a complete plugin. A committed copy can rot; this test
makes drift a failing test, not a silent bug. Regenerate with `scripts/regen-plugin.sh`.
Hermetic, stdlib only.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
SKILLS_SRC = os.path.join(ROOT, "skills")
SKILLS_DST = os.path.join(ROOT, "plugins", "arlo", "skills")

# The lifecycle. Skills that RUN the core bundle it plus REFERENCE.md (the repo-root SKILL.md).
LIFECYCLE = ["start", "setup", "update", "upgrade", "remove"]
NEEDS_CORE = {"start", "update"}
REGEN = "run scripts/regen-plugin.sh"


def _read(path, mode="r"):
    with open(path, mode) as f:
        return f.read()


class PluginSync(unittest.TestCase):
    def test_exactly_the_lifecycle_skills_are_shipped(self):
        shipped = sorted(d for d in os.listdir(SKILLS_DST)
                         if os.path.isdir(os.path.join(SKILLS_DST, d)))
        self.assertEqual(shipped, sorted(LIFECYCLE),
                         f"shipped skills != lifecycle — {REGEN}")

    def test_each_skill_body_matches_source(self):
        for name in LIFECYCLE:
            src = os.path.join(SKILLS_SRC, name, "SKILL.md")
            dst = os.path.join(SKILLS_DST, name, "SKILL.md")
            self.assertTrue(os.path.isfile(src), f"missing source skill {name}")
            self.assertTrue(os.path.isfile(dst), f"plugin missing skill {name} — {REGEN}")
            self.assertEqual(_read(src), _read(dst),
                             f"plugin skill {name} drifted from source — {REGEN}")

    def test_frontmatter_name_equals_dir(self):
        # Invocation is /arlo:<dir>; the frontmatter name must match, or the command is wrong.
        for name in LIFECYCLE:
            body = _read(os.path.join(SKILLS_DST, name, "SKILL.md"))
            self.assertIn(f"\nname: {name}\n", "\n" + body,
                          f"skill {name} frontmatter name != dir — {REGEN}")

    def test_core_is_byte_identical_where_bundled(self):
        src = os.path.join(ROOT, "arlo")
        names = sorted(f for f in os.listdir(src) if f.endswith(".py"))
        self.assertTrue(names, "no core modules found")
        for name in NEEDS_CORE:
            dst = os.path.join(SKILLS_DST, name, "arlo")
            for n in names:
                p = os.path.join(dst, n)
                self.assertTrue(os.path.isfile(p),
                                f"skill {name} missing core {n} — {REGEN}")
                self.assertEqual(_read(os.path.join(src, n), "rb"), _read(p, "rb"),
                                 f"skill {name} core {n} drifted — {REGEN}")

    def test_reference_matches_root_skill(self):
        # REFERENCE.md is the canonical arlo document (repo-root SKILL.md), bundled verbatim.
        root = _read(os.path.join(ROOT, "SKILL.md"))
        for name in NEEDS_CORE:
            ref = os.path.join(SKILLS_DST, name, "REFERENCE.md")
            self.assertTrue(os.path.isfile(ref),
                            f"skill {name} missing REFERENCE.md — {REGEN}")
            self.assertEqual(root, _read(ref),
                             f"skill {name} REFERENCE.md drifted from root SKILL.md — {REGEN}")

    def test_start_bundles_launcher_and_provisioner(self):
        # start wires `arlo` onto the PATH and provisions the model, so it bundles both.
        for rel in ("bin/arlo", "provision.sh"):
            got = os.path.join(SKILLS_DST, "start", rel)
            self.assertTrue(os.path.isfile(got), f"start missing {rel} — {REGEN}")
            self.assertEqual(_read(os.path.join(ROOT, rel), "rb"), _read(got, "rb"),
                             f"start {rel} drifted from source — {REGEN}")

    def test_setup_is_an_alias_of_start(self):
        body = _read(os.path.join(SKILLS_DST, "setup", "SKILL.md"))
        self.assertIn("/arlo:start", body, "setup must point at /arlo:start (it is an alias)")
        # An alias carries no core of its own.
        self.assertFalse(os.path.isdir(os.path.join(SKILLS_DST, "setup", "arlo")),
                         "setup is an alias; it should not bundle the core")

    def test_upgrade_reconciles_via_update(self):
        # upgrade pulls the latest arlo, then defers to /arlo:update to reconcile projects;
        # it is orchestration prose, so it bundles no core of its own.
        body = _read(os.path.join(SKILLS_DST, "upgrade", "SKILL.md"))
        self.assertIn("/arlo:update", body, "upgrade must reconcile via /arlo:update")
        self.assertFalse(os.path.isdir(os.path.join(SKILLS_DST, "upgrade", "arlo")),
                         "upgrade is orchestration; it should not bundle the core")


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=0).result
    if result.wasSuccessful():
        print(f"PASS test_plugin_sync ({result.testsRun} cases)")
        sys.exit(0)
    print("FAIL test_plugin_sync")
    sys.exit(1)
