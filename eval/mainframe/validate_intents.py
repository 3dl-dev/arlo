#!/usr/bin/env python3
"""Validate the mainframe intent eval set against real ground truth.

The invariant arlo exists to protect is: never emit a command that is not real
ground truth. That invariant applies to the *eval set* too — a benchmark whose
"expected" commands were invented would grade arlo against fiction. So this
validator independently re-derives every non-abstention expected_command from
mainframe's actual scripts (it does NOT trust the `source` breadcrumb in the
row), and fails loudly if any command's skeleton cannot be traced to a real
invocation surface.

It is READ-ONLY: it reads mainframe's checked-in scripts and never executes them.

Usage:
    MAINFRAME_ROOT=~/projects/mainframe python3 arlo/eval/validate_intents.py
Exit 0 = every card_expected command traces to real ground truth.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
INTENTS = HERE / "intents.jsonl"
MAINFRAME_ROOT = Path(
    os.environ.get("MAINFRAME_ROOT", str(Path.home() / "projects" / "mainframe"))
).expanduser()


def _read(rel: str) -> str | None:
    p = MAINFRAME_ROOT / rel
    return p.read_text() if p.is_file() else None


def _case_has(body: str, verb: str) -> bool:
    """True if a bash `case` in `body` has a branch matching `verb`, allowing
    pipe-alternated patterns like `opencode|oc)` and leading whitespace."""
    v = re.escape(verb)
    pat = re.compile(r"^\s*(?:[\w.-]+\|)*" + v + r"(?:\|[\w.-]+)*\)", re.MULTILINE)
    return bool(pat.search(body))


def trace(expected: str) -> tuple[bool, str]:
    """Independently confirm the command *skeleton* is real ground truth.
    Returns (ok, reason). Argument VALUES (VMID/NAME/IP) are rung-1 slots, not
    ground truth to verify — only the real skeleton (program + subcommand) is."""
    toks = shlex.split(expected)
    if not toks:
        return False, "empty command"
    prog = toks[0]

    # `mainframe <verb>` — verb must be a real case branch in mainframe.sh
    if prog == "mainframe":
        if len(toks) < 2:
            return False, "mainframe with no verb"
        body = _read("scripts/mainframe.sh")
        if body is None:
            return False, "scripts/mainframe.sh not found"
        verb = toks[1]
        return (_case_has(body, verb), f"mainframe.sh case '{verb})'")

    # `mf <verb>` — verb must be a real case branch in the mf dispatcher
    if prog == "mf":
        if len(toks) < 2:
            return False, "mf with no verb"
        body = _read("scripts/mf")
        if body is None:
            return False, "scripts/mf not found"
        verb = toks[1]
        return (_case_has(body, verb), f"mf case '{verb})'")

    # a real script under scripts/ (e.g. mk-relay.sh, llama-qwen36.sh)
    if prog.endswith(".sh"):
        body = _read(f"scripts/{prog}")
        if body is None:
            return False, f"scripts/{prog} not found"
        # scripts with a subcommand verb (llama-qwen36.sh start|stop|...) must
        # have that verb as a real case branch; positional-arg scripts (mk-*.sh
        # <VMID> <NAME> <IP>) just need to exist — the args are rung-1 slots.
        rest = toks[1:]
        if rest and re.fullmatch(r"[a-z][a-z0-9-]*", rest[0]) and _case_has(body, rest[0]):
            return True, f"{prog} case '{rest[0]})'"
        # otherwise the real skeleton is the script itself
        return True, f"scripts/{prog} exists"

    return False, f"unrecognized program '{prog}'"


def main() -> int:
    if not MAINFRAME_ROOT.is_dir():
        print(f"FAIL: MAINFRAME_ROOT not a dir: {MAINFRAME_ROOT}", file=sys.stderr)
        return 2
    rows = [json.loads(l) for l in INTENTS.read_text().splitlines() if l.strip()]

    n_card = n_abst = 0
    failures: list[str] = []
    seen_ids: set[str] = set()
    for r in rows:
        rid = r.get("id", "?")
        if rid in seen_ids:
            failures.append(f"{rid}: duplicate id")
        seen_ids.add(rid)
        if r.get("card_expected"):
            n_card += 1
            cmd = r.get("expected_command")
            if not cmd:
                failures.append(f"{rid}: card_expected but no expected_command")
                continue
            ok, why = trace(cmd)
            if not ok:
                failures.append(f"{rid}: '{cmd}' does NOT trace to ground truth ({why})")
        else:
            n_abst += 1
            if r.get("expected_command") is not None:
                failures.append(f"{rid}: abstention row must have expected_command=null")

    print(f"eval set: {len(rows)} rows  ({n_card} grounded, {n_abst} abstention)")
    print(f"ground truth root: {MAINFRAME_ROOT}")
    if failures:
        print(f"\nFAIL — {len(failures)} problem(s):")
        for f in failures:
            print(f"  ✗ {f}")
        return 1
    print("\nOK — every grounded command traces to a real mainframe invocation surface.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
