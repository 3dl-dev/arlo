#!/usr/bin/env python3
"""arlo's grounding invariant. Hermetic, stdlib only.

Locks the two halves of the invariant: the corpus is generated from a command (not
authored), and answers are retrieval-grounded (every returned line exists in the
corpus). Carried from the operator's self-test; the invariant is the product.
"""

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from arlo import build_corpus, cards, runbook  # noqa: E402

# A fixture verb-dispatched script: a header (with a Usage line naming the invocation
# and a mode list documenting two verbs) and a real bash `case` dispatch.
DISPATCH_FIXTURE = """#!/usr/bin/env bash
# widget — operational mode manager
#
# Modes:
#   up    — bring the widget online
#   down  — take the widget offline
#
# Usage:
#   widget up
#   widget status
set -euo pipefail
case "$1" in
    up)      do_up ;;
    down)    do_down ;;
    status)  do_status ;;
    -h|--help) usage ;;
    *)       usage 1 ;;
esac
"""

# A stand-in for a real `--help`: a command whose output is the ground truth.
FAKE_HELP = "printf '%s\\n' '--parent-id ID  attach to a parent' '--json  machine output'"


class Grounding(unittest.TestCase):

    def test_corpus_is_generated_with_provenance(self):
        corpus = build_corpus.build_corpus([{"name": "rd-help", "cmd": FAKE_HELP}])
        self.assertEqual(len(corpus), 1)
        entry = corpus[0]
        self.assertEqual(entry["source_cmd"], FAKE_HELP)  # provenance is the command
        self.assertIn("--parent-id", entry["text"])
        self.assertEqual(entry["rc"], 0)

    def test_answer_is_retrieval_grounded(self):
        corpus = build_corpus.build_corpus([{"name": "rd-help", "cmd": FAKE_HELP}])
        hits = build_corpus.answer(corpus, "parent-id")
        self.assertTrue(hits)
        self.assertIn("--parent-id", hits[0]["line"])
        self.assertEqual(hits[0]["from"], FAKE_HELP)
        corpus_text = "\n".join(e["text"] for e in corpus)
        for h in hits:  # every returned line is actually in the corpus, never synthesized
            self.assertIn(h["line"], corpus_text)

    def test_no_grounded_match_returns_nothing(self):
        corpus = build_corpus.build_corpus([{"name": "rd-help", "cmd": FAKE_HELP}])
        self.assertEqual(build_corpus.answer(corpus, "wombat-flag-xyz"), [])

    def test_asking_the_stale_name_surfaces_the_real_flag(self):
        # the --parent / --parent-id drift: ask the stale name, arlo hands back the
        # real one from the fresh corpus (a maintained doc would lie instead).
        corpus = build_corpus.build_corpus([{"name": "rd-help", "cmd": FAKE_HELP}])
        hits = build_corpus.answer(corpus, "--parent")
        self.assertTrue(any("--parent-id" in h["line"] for h in hits))


class DispatchCards(unittest.TestCase):
    """Verb-aware harvesting: a dispatcher becomes one card PER real verb, grounded in
    its `case` statement, never a verb the script does not have."""

    def _cards(self):
        with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as f:
            f.write(DISPATCH_FIXTURE)
            path = f.name
        try:
            return cards.extract_dispatch_cards(path)
        finally:
            os.unlink(path)

    def test_one_card_per_real_verb(self):
        cmds = {c["command"] for c in self._cards()}
        # prog name comes from the header (`widget up`), not the temp filename
        self.assertEqual(cmds, {"widget up", "widget down", "widget status"})

    def test_default_and_help_branches_are_not_verbs(self):
        cmds = {c["command"] for c in self._cards()}
        self.assertNotIn("widget *", cmds)
        self.assertFalse(any("help" in c or "-h" in c for c in cmds))

    def test_a_nonexistent_verb_is_never_carded(self):
        # the invariant: only verbs the script actually dispatches become commands
        cmds = {c["command"] for c in self._cards()}
        self.assertNotIn("widget destroy", cmds)   # not a case branch -> not ground truth

    def test_verb_purpose_from_the_mode_list(self):
        by_cmd = {c["command"]: c["purpose"] for c in self._cards()}
        self.assertEqual(by_cmd["widget up"], "bring the widget online")
        # a verb the header does not describe falls back to the command, never invented
        self.assertEqual(by_cmd["widget status"], "widget status")


MULTILINE_USAGE = """#!/bin/bash
# ONE command: clean-install and boot the thing
#
# Usage:
#   ./boot.sh                 # build if needed, install + boot
#   ./boot.sh --clean         # force a fresh disk
#
set -euo pipefail
"""

EMPTY_USAGE = """#!/bin/bash
# a script whose Usage line has no synopsis at all
# Usage:
echo hi
"""


class ScriptCardEdges(unittest.TestCase):
    """Regressions surfaced by the STEP-3 multi-project loss (vms): a `Usage:` whose
    synopsis is on the next line must still yield a real command, and a header that
    yields no usable invocation must NOT be carded as a blank (an invariant violation)."""

    def _card(self, text):
        with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as f:
            f.write(text); path = f.name
        try:
            return cards.extract_script_card(path)
        finally:
            os.unlink(path)

    def test_multiline_usage_takes_the_synopsis_line(self):
        c = self._card(MULTILINE_USAGE)
        self.assertEqual(c["command"], "./boot.sh")          # not empty
        self.assertIn("clean-install", c["purpose"])

    def test_empty_usage_is_not_carded_as_a_blank(self):
        self.assertIsNone(self._card(EMPTY_USAGE))           # no fabricated empty card


# A --help with a real subcommand section (cobra/git/kubectl style) and, separately, a
# bare catch-all synopsis.
HELP_WITH_SUBCOMMANDS = (
    "mytool — does things\n\n"
    "Usage: mytool [command]\n\n"
    "Available Commands:\n"
    "  build       compile the project\n"
    "  deploy      ship it to prod\n"
    "  help        Help about any command\n\n"
    "Flags:\n  -h  help\n"
)
HELP_CATCHALL_ONLY = "mytool — does things\n\nUsage:\n  mytool [command]\n"


class HelpCards(unittest.TestCase):
    """Regressions surfaced by the STEP-3 loss (ready): a CLI that lists subcommands is
    harvested one card PER subcommand; a CLI whose synopsis is only a catch-all
    placeholder is refused (carding `mytool [command]` would let arlo emit an ungrounded
    subcommand — an invariant risk)."""

    def _run(self, text):
        return lambda cmd, timeout=30: (0, text)

    def test_subcommand_section_becomes_one_card_per_verb(self):
        cs = cards.extract_help_cards("mytool --help", run=self._run(HELP_WITH_SUBCOMMANDS))
        cmds = {c["command"] for c in cs}
        self.assertEqual(cmds, {"mytool build", "mytool deploy"})   # help/completion dropped
        self.assertEqual(next(c["purpose"] for c in cs if c["command"] == "mytool build"),
                         "compile the project")

    def test_catchall_synopsis_is_refused(self):
        cs = cards.extract_help_cards("mytool --help", run=self._run(HELP_CATCHALL_ONLY))
        self.assertEqual(cs, [])          # no card beats an ungroundable `mytool [command]`

    def test_absent_command_yields_no_card(self):
        cs = cards.extract_help_cards("nope --help", run=lambda c, timeout=30: (127, "not found"))
        self.assertEqual(cs, [])


class Runbook(unittest.TestCase):
    """The lights-out artifact: every real command lands in it, grouped by source file,
    with an offline way to query it — the durable thing the operator uses with no agent."""

    CARDS = [
        {"command": "mainframe rail", "purpose": "GPUs to the k3s worker", "source": "scripts/mainframe.sh:rail)"},
        {"command": "mainframe off", "purpose": "release the GPUs", "source": "scripts/mainframe.sh:off)"},
        {"command": "mk-relay.sh <VMID> <NAME> <IP>", "purpose": "make a relay VM", "source": "scripts/mk-relay.sh"},
    ]

    def test_every_command_is_in_the_runbook(self):
        md = runbook.render(self.CARDS, project="mainframe")
        for c in self.CARDS:
            self.assertIn(c["command"], md)

    def test_grouped_by_source_file_not_per_verb(self):
        md = runbook.render(self.CARDS)
        self.assertEqual(md.count("### scripts/mainframe.sh"), 1)  # both verbs, one heading
        self.assertNotIn("mainframe.sh:rail)", md)                 # the :verb) suffix is stripped

    def test_carries_an_offline_query_path(self):
        md = runbook.render(self.CARDS)
        self.assertIn("python3 -m arlo.translate", md)   # find a command with no frontier
        self.assertIn("no confident match", md)          # it declines rather than guess


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=0).result
    if result.wasSuccessful():
        print(f"PASS test_grounding ({result.testsRun} cases)")
        sys.exit(0)
    print("FAIL test_grounding")
    sys.exit(1)
