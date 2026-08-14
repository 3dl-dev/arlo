#!/usr/bin/env python3
"""arlo — the lights-out CLI: `arlo restart the deriver`.

This is the interface for the moment arlo exists for: the frontier is down, the agent
is gone (it WAS the frontier), and you are at a shell in your project. You type your own
words and arlo prints the real command, grounded in this project's own ground truth.

Everything expensive was resolved at setup (`/arlo:start`, run by your agent while the
lights were on): the ground truth was harvested into `.arlo/cards.json`, and the model
tier you chose — a big local model, a small one, a self-hosted endpoint, or none at all —
was written to `.arlo/config.json`. This command just uses what is already there. If the
configured model is unreachable, it falls back to a model-free lexical match over the
same real cards rather than fail: a weaker answer, honestly labeled, beats no answer.

Standard library only. The model, if any, is reached through the config; arlo names none.
"""

import argparse
import json
import os
import sys

from . import translate, binder, ground


def find_arlo_dir(start=None):
    """Walk up from cwd for the `.arlo/` a setup wrote. This is why `arlo <words>` works
    from anywhere in the project: it finds the harvested ground truth on its own."""
    d = os.path.abspath(start or os.getcwd())
    while True:
        cand = os.path.join(d, ".arlo")
        if os.path.isfile(os.path.join(cand, "cards.json")):
            return cand
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def _embedder(cards, config):
    """The embedder resolved at setup, or an honest model-free fallback. A configured
    local model is used when reachable; otherwise a deterministic bag-of-words over the
    cards' own vocabulary — no dependency, always available, weaker and labeled so."""
    model = (config or {}).get("embedder")
    if model:
        try:
            return translate.sentence_transformer_embedder(model), True
        except Exception:  # noqa: BLE001 — model absent/unreachable: fall back, do not fail
            pass
    vocab = sorted({w for c in cards for w in translate._stems(c["purpose"] + " " + c["command"])})
    return translate.bag_of_words_embedder(vocab), False


def answer(intent, arlo_dir, top=3, floor=0.15):
    cards = json.load(open(os.path.join(arlo_dir, "cards.json")))
    config = {}
    cfg_path = os.path.join(arlo_dir, "config.json")
    if os.path.isfile(cfg_path):
        config = json.load(open(cfg_path))
    embed, live_model = _embedder(cards, config)
    hits = translate.rank(embed, cards, intent, top)
    return hits, live_model, config


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="arlo",
        description="Type your own words; get the real command to run. Grounded in this "
                    "project's ground truth, never invented.")
    ap.add_argument("intent", nargs="*", help="what you want to do, in your own words")
    ap.add_argument("--top", type=int, default=3)
    args = ap.parse_args(argv)

    if not args.intent:
        ap.print_help()
        return 0
    intent = " ".join(args.intent)

    arlo_dir = find_arlo_dir()
    if not arlo_dir:
        print("arlo: this project has no harvested ground truth yet.", file=sys.stderr)
        print("      Run `/arlo:start` in your agent (while the frontier is up) to set it up.",
              file=sys.stderr)
        return 3

    hits, live_model, _ = answer(intent, arlo_dir, args.top)
    if not hits or hits[0]["score"] < 0.15:
        print("no confident match — arlo will not guess.")
        if hits:
            print(f"  (closest was `{hits[0]['command']}` at {hits[0]['score']})")
        print(f"  or read {os.path.relpath(os.path.join(arlo_dir, 'LIGHTS-OUT.md'))}")
        return 1

    best = hits[0]
    # rung 1: if the chosen command is a template with a hole, bind it from the words
    res = binder.slot_fill(binder.residual_binder, best, intent)
    command = res["command"]
    grounded_note = "" if res["skeleton_preserved"] else "  [skeleton drift — refusing]"
    if not res["skeleton_preserved"]:
        print("arlo: refusing — the command skeleton did not stay ground truth.", file=sys.stderr)
        return 2

    tier = "local model" if live_model else "lexical match, no model"
    print(command)
    print(f"  ↳ {best['purpose'][:88]}")
    print(f"  ↳ source: {best['source']}   confidence {best['score']}   [{tier}]")
    if res["unbound"]:
        print(f"  ↳ fill in: {', '.join(res['unbound'])}")
    if len(hits) > 1:
        print("  also real:")
        for h in hits[1:]:
            print(f"    - {h['command']}   ({h['score']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
