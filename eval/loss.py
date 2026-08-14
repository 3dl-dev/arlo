#!/usr/bin/env python3
"""arlo STEP 3: the multi-project acceptance test as a loss function.

Not a one-shot grade. This runs hoisted arlo's harvest+answer path against EACH
pointed-at project's real ground truth (read-only), computes a loss decomposed by
failure type, and attributes each component to the upstream artifact that must change
to reduce it — the skill toolset (STEP 1) or the distribution (STEP 2). Fix upstream,
re-run, watch the loss fall. That attribution is the "backprop": a loss component names
its own gradient.

This module computes the MODEL-FREE components (no rail, no LOM):
  - harvestability: a real command the project exposes has no card at all.
  - invariant: any card whose command is not traceable to ground truth (a hard,
    absolute failure; cards are generated from source, so this should be 0 — it is the
    sentinel that proves the harvest never fabricated a command).
Retrieval / binding / reason-rank QUALITY needs the LOM and is the rail phase; this
harness prints those as an explicit boundary rather than faking a number.

Read-only: it harvests each project's checked-in ground truth and never runs a
mutating command against it. Standard library only.
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from arlo import cards, binder, translate  # noqa: E402

_CHOICE_RE = re.compile(r"[<\[]([^<>\[\]]*\|[^<>\[\]]*)[>\]]")


def _reference_commands(path):
    """The real commands a project exposes (the target surface). Accepts an intents
    file (rows with expected_command / card_expected) or a plain reference file (rows
    with command). Abstention rows (card_expected false) are not part of harvestability."""
    cmds = []
    for line in open(os.path.join(HERE, "..", path)).read().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if "expected_command" in r or "card_expected" in r:
            if r.get("card_expected") and r.get("expected_command"):
                cmds.append(r["expected_command"])
        elif r.get("command"):
            cmds.append(r["command"])
    return cmds


def cardable(command, card_cmds):
    """Is `command` covered by some card? Exact match, a choice card (`mk-inference.sh
    <a|b>` covers `mk-inference.sh a`), or a slot template whose fixed skeleton the
    command begins with (`mk-relay.sh <VMID> <NAME> <IP>` covers `mk-relay.sh 220 x ip`)."""
    if command in card_cmds:
        return True
    prog = command.split()[0] if command.split() else ""
    for cc in card_cmds:
        if not cc or cc.split()[0:1] != [prog]:
            continue
        m = _CHOICE_RE.search(cc)
        if m:
            prefix = cc[:m.start()].strip()
            if command in {f"{prefix} {ch.strip()}".strip() for ch in m.group(1).split("|")}:
                return True
        if binder.slots(cc):
            lits = [s.strip() for s in binder.literals(cc) if s.strip()]
            if lits and command.startswith(lits[0]):
                return True
    return False


def _intent_rows(path):
    """Full rows when the reference is an intents file (natural intent + expected command
    + card_expected). Empty for a command-only reference (retrieval can't be graded there
    without authored intents)."""
    rows = []
    for line in open(os.path.join(HERE, "..", path)).read().splitlines():
        if line.strip():
            r = json.loads(line)
            if "intent" in r and ("expected_command" in r or "card_expected" in r):
                rows.append(r)
    return rows


def _retrieval_and_abstention(cs, intent_rows, floor=0.15):
    """Grade the CLI's model-free path: does rank() select the card whose command matches
    the expected one (retrieval), and does it correctly decline when no card should match
    (abstention)? Uses the same bag-of-words embedder arlo falls back to with no model."""
    vocab = translate.vocabulary([c["purpose"] + " " + c["command"] for c in cs])
    embed = translate.bag_of_words_embedder(vocab)
    card_cmds = [c["command"] for c in cs]
    ret_total = ret_miss = abs_total = abs_wrong = 0
    ret_fails = []
    for r in intent_rows:
        hits = translate.rank(embed, cs, r["intent"], top=1)
        top = hits[0] if hits else None
        if r.get("card_expected"):
            ret_total += 1
            got = top["command"] if top and top["score"] >= floor else None
            if not (got and cardable(r["expected_command"], [got])):
                ret_miss += 1
                ret_fails.append((r["intent"], r["expected_command"], got or "(abstained)"))
        else:  # should abstain
            abs_total += 1
            if top and top["score"] >= floor:
                abs_wrong += 1
    return {
        "ret_total": ret_total, "ret_miss": ret_miss, "ret_fails": ret_fails,
        "abs_total": abs_total, "abs_wrong": abs_wrong,
    }


def score_project(p):
    cs = cards.build_cards(p["spec"], root=p["root"])
    card_cmds = [c["command"] for c in cs]
    ref = _reference_commands(p["reference"])
    misses = [c for c in ref if not cardable(c, card_cmds)]
    fabricated = [c for c in cs if not c.get("command") or not c.get("source")]
    harvest_loss = len(misses) / len(ref) if ref else 0.0
    rq = _retrieval_and_abstention(cs, _intent_rows(p["reference"]))
    return {
        "name": p["name"], "cards": len(cs), "reference": len(ref),
        "covered": len(ref) - len(misses), "harvest_loss": harvest_loss,
        "misses": misses, "invariant_violations": len(fabricated), **rq,
    }


# each loss component -> the upstream artifact whose change reduces it (the gradient)
ATTRIBUTION = {
    "harvestability": "skill toolset: arlo/cards.py (harvesting) — a real command has no card",
    "invariant": "skill toolset CORE: cards.py/ground.py — a fabricated command (hard fail)",
    "retrieval/binding/reason-rank": "skill toolset rungs + the LOM (rail phase) — quality, ungraded here",
    "transfer": "the distribution: config.json — arlo failed to deploy/accept on a clean target",
}


def main():
    projects = json.load(open(os.path.join(HERE, "projects.json")))
    results = [score_project(p) for p in projects]

    print("=== arlo STEP-3 loss (model-free components; read-only harvest) ===\n")
    tot_ref = tot_cov = tot_inv = 0
    tot_rt = tot_rm = tot_at = tot_aw = 0
    for r in results:
        tot_ref += r["reference"]; tot_cov += r["covered"]; tot_inv += r["invariant_violations"]
        tot_rt += r["ret_total"]; tot_rm += r["ret_miss"]; tot_at += r["abs_total"]; tot_aw += r["abs_wrong"]
        rl = f"  retrieval={r['ret_total']-r['ret_miss']}/{r['ret_total']}" if r["ret_total"] else ""
        al = f"  abstain={r['abs_total']-r['abs_wrong']}/{r['abs_total']}" if r["abs_total"] else ""
        print(f"[{r['name']:<10}] cards={r['cards']:<3} coverage={r['covered']}/{r['reference']}"
              f"  harvest_loss={r['harvest_loss']:.2f}{rl}{al}  inv={r['invariant_violations']}")
        for m in r["misses"]:
            print(f"              gradient (harvestability): no card for  '{m}'")
        for intent, exp, got in r["ret_fails"]:
            print(f"              gradient (retrieval): '{intent}' -> got {got}, want `{exp}`")
    agg = 1 - (tot_cov / tot_ref) if tot_ref else 0.0
    ret_loss = tot_rm / tot_rt if tot_rt else 0.0
    abs_loss = tot_aw / tot_at if tot_at else 0.0
    print(f"\nAGGREGATE harvestability loss: {tot_ref - tot_cov}/{tot_ref} = {agg:.2f}"
          f"   |   invariant violations: {tot_inv} (must be 0)")
    print(f"AGGREGATE retrieval loss (model-free floor): {tot_rm}/{tot_rt} = {ret_loss:.2f}"
          f"   |   abstention loss: {tot_aw}/{tot_at} = {abs_loss:.2f}")
    print("\nbackprop (each gradient -> the upstream artifact to change):")
    for k, v in ATTRIBUTION.items():
        print(f"  {k:<28} -> {v}")
    print("\nboundary: retrieval/binding/reason-rank QUALITY needs the LOM (rail phase); "
          "not scored here.")
    return 1 if tot_inv else 0


if __name__ == "__main__":
    raise SystemExit(main())
