#!/usr/bin/env python3
"""arlo rungs 2-6 structural grounding primitives (arlo/ground.py). Hermetic, stdlib
only, no model download.

These lock the invariant each higher rung must keep, independently of any model: the
functions take a model's OUTPUT and must never let a non-ground-truth command through.
Whether the model REASONS well (picks the right card, writes a good explanation) is a
quality grade for a live model on a real target — a separate, labeled boundary. Here we
grade only that ground.py cannot be made to emit or bless something ungrounded.
"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from arlo import ground  # noqa: E402

CANDS = [
    {"id": "rail", "command": "mainframe rail"},
    {"id": "inference", "command": "mainframe inference"},
    {"id": "off", "command": "mainframe off"},
]
SOURCE = "deploy.sh — helper\nUsage: deploy.sh rollout <service>\nAlso: deploy.sh status\n"
HELP = "rd create -- create an item\n  --parent-id ID  attach to a parent\n  --json  output\n"


class Rung2Select(unittest.TestCase):
    def test_resolves_real_id_verbatim(self):
        self.assertEqual(ground.select(CANDS, "inference")["command"], "mainframe inference")

    def test_refuses_non_candidate(self):
        with self.assertRaises(ground.NotACandidate):
            ground.select(CANDS, "reboot-everything")


class Rung4Compose(unittest.TestCase):
    def test_orders_real_commands(self):
        steps, dropped = ground.compose(CANDS, ["inference", "off"])
        self.assertEqual([s["command"] for s in steps], ["mainframe inference", "mainframe off"])
        self.assertEqual(dropped, [])

    def test_drops_non_cards_never_emits_them(self):
        steps, dropped = ground.compose(CANDS, ["rail", "rm -rf /", "off"])
        self.assertEqual([s["command"] for s in steps], ["mainframe rail", "mainframe off"])
        self.assertEqual(dropped, ["rm -rf /"])   # reported, never a step

    def test_malformed_plan_composes_to_nothing(self):
        self.assertEqual(ground.compose(CANDS, "not-a-list"), ([], []))


class Rung3Explain(unittest.TestCase):
    def test_whole_option_tokens(self):
        toks = ground.option_tokens("use --parent-id and --json, not --parent")
        self.assertEqual(toks, {"--parent-id", "--json", "--parent"})

    def test_stale_flag_is_caught(self):
        grounded, offenders = ground.cited_flags_grounded("pass --parent to nest it", HELP)
        self.assertFalse(grounded)              # help says --parent-id, not --parent
        self.assertIn("--parent", offenders)

    def test_real_flag_passes(self):
        grounded, offenders = ground.cited_flags_grounded("use --parent-id ID", HELP)
        self.assertTrue(grounded)
        self.assertEqual(offenders, [])


class Rung5Propose(unittest.TestCase):
    def test_command_from_source_is_grounded(self):
        grounded, missing = ground.card_grounded("deploy.sh rollout <service>", SOURCE)
        self.assertTrue(grounded)               # skeleton 'deploy.sh rollout ' is in source
        self.assertEqual(missing, [])

    def test_command_not_in_source_is_refused(self):
        grounded, missing = ground.card_grounded("deploy.sh nuke --all", SOURCE)
        self.assertFalse(grounded)              # 'nuke' never appears
        self.assertTrue(missing)

    def test_whitespace_run_in_source_does_not_false_refuse(self):
        # a real command documented backslash-continued / column-aligned leaves a run of
        # whitespace (space-before-backslash -> newline -> indent) between tokens; the raw
        # substring check false-refused it. Normalization accepts the genuinely-present skeleton.
        src = "az containerapp update -g prod \\\n    --image acr/app:v1"
        grounded, missing = ground.card_grounded("az containerapp update -g prod --image <ref>", src)
        self.assertTrue(grounded)
        self.assertEqual(missing, [])

    def test_normalization_does_not_fabricate_a_missing_token(self):
        # invariant guard: collapsing whitespace must not let an absent token pass.
        grounded, missing = ground.card_grounded("deploy.sh   frobnicate", SOURCE)
        self.assertFalse(grounded)
        self.assertTrue(missing)


class Rung6Generate(unittest.TestCase):
    def test_generated_command_is_always_unverified(self):
        for cmd in ["tar czf b.tgz .", "kubectl get pods", "rm -rf /tmp/x", ""]:
            res = ground.unverified(cmd)
            self.assertFalse(res["grounded"])
            self.assertFalse(res["verified"])
            self.assertIsNone(res["source"])
            self.assertIn("UNVERIFIED", res["trust"])

    def test_label_is_the_module_constant(self):
        self.assertEqual(ground.unverified("whoami")["trust"], ground.UNVERIFIED)


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=0).result
    if result.wasSuccessful():
        print(f"PASS test_ground ({result.testsRun} cases)")
        sys.exit(0)
    print("FAIL test_ground")
    sys.exit(1)
