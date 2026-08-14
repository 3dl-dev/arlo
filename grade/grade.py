#!/usr/bin/env python3
"""arlo STEP-3 grader — scores what an AGENT produced by running the skill.

Read this before you touch it: this file deliberately does **not** import arlo. It
grades the *product* — the answers an agent hands back after running `SKILL.md` in a
target project — not arlo's shipped functions. If you find yourself adding
`from arlo import ...` here to "grade retrieval," stop: that is the build-it-here mode
failure (see CLAUDE.md, the altitude invariant). The whole point of STEP 3 is that the
skill is executed by an agent in a project's context, with the agent's model as the LOM,
and this only compares its answers to a held-out set. No model, no arlo code, no floor.

Inputs (both are just data):
  - a held-out set:  jsonl rows {id, intent, expected_command, expected_key, card_expected}
  - an answers file: json {id: command-string}, where "NO_MATCH" means the agent abstained,
                     produced by an agent that ran the skill (see PROTOCOL.md).

Usage:
    python3 grade/grade.py <held_out.jsonl> <answers.json>
"""

import json
import sys


def load_held_out(path):
    return [json.loads(l) for l in open(path).read().splitlines() if l.strip()]


def grade(held_out, answers):
    ret_t = ret_ok = abs_t = abs_ok = 0
    fails = []
    for r in held_out:
        a = (answers.get(r["id"]) or "").strip()
        if r.get("card_expected"):
            ret_t += 1
            key = r.get("expected_key") or r.get("expected_command") or ""
            # lenient, honest match: exact expected, or the grounded key appears in the
            # agent's command (handles slot-fill and command-form variation).
            ok = a and a != "NO_MATCH" and (a == r.get("expected_command") or key in a)
            if ok:
                ret_ok += 1
            else:
                fails.append((r["id"], r["intent"], a or "(none)", r.get("expected_command")))
        else:  # a no-command intent: abstaining is correct
            abs_t += 1
            if a == "NO_MATCH":
                abs_ok += 1
            else:
                fails.append((r["id"], r["intent"], a or "(none)", "ABSTAIN"))
    return ret_t, ret_ok, abs_t, abs_ok, fails


def main(argv=None):
    argv = argv or sys.argv[1:]
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[-1])
        return 2
    held_out = load_held_out(argv[0])
    answers = json.load(open(argv[1]))
    ret_t, ret_ok, abs_t, abs_ok, fails = grade(held_out, answers)

    print(f"=== STEP-3 grade: {argv[0]}  (agent output, real LOM) ===")
    if ret_t:
        print(f"retrieval:  {ret_ok}/{ret_t}")
    if abs_t:
        print(f"abstention: {abs_ok}/{abs_t}")
    if fails:
        print("\nmisses (the gradients — each names where the skill, run in context, fell short):")
        for i, intent, got, want in fails:
            print(f"  {i}: '{intent}'  -> {got}   (want {want})")
    else:
        print("\nclean: every grounded intent got the right real command; every abstention correct.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
