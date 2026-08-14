#!/usr/bin/env python3
"""arlo lights-out runbook: the durable, agent-free artifact.

The paradox arlo has to resolve: it installs as a skill in an agent, but the moment it
is actually needed — the frontier is down — that agent is down too, because the agent
IS the frontier. So the prep step (`/arlo:start`, run while the lights are on) writes
this runbook to disk. When everything is dark and there is no agent, the operator opens
one file and has every real command, plus two ways to find the right one with no network
and no frontier: search the file, or query it by intent with the local core.

Every command in it was harvested from the system's own ground truth (arlo.cards); none
was written by hand or by a model. Standard library only, deterministic.
"""

import argparse
import json
import os
import sys


def render(cards, project=None, cards_path=".arlo/cards.json"):
    """Render harvested cards to a lights-out runbook (Markdown). Commands are grouped
    by the source they were harvested from, each with its ground-truth purpose."""
    title = f"arlo lights-out runbook{f' — {project}' if project else ''}"
    out = [
        f"# {title}",
        "",
        "**The frontier is down and you still have to operate. You do not need it.**",
        "Every command below is real — harvested from this system's own ground truth,",
        "never invented. Find what you need and run it.",
        "",
        "## Find a command with no agent and no network",
        "",
        "- **Search this file** for what you want to do (a service name, \"restart\", \"logs\").",
        "- **Ask by intent** with the local core (no frontier):",
        "",
        f"      python3 -m arlo.translate {cards_path} \"bounce the deriver\"",
        "",
        "  It returns the closest real command, its confidence, and the alternatives, or",
        "  says \"no confident match\" rather than guess. (Ranking uses a small local model",
        "  if one is provisioned; otherwise search the list below.)",
        "",
        "## Every real command, by source",
        "",
    ]
    by_source = {}
    for c in cards:
        # group by the source FILE, not per-verb: 'scripts/mainframe.sh:boot)' -> file
        src = (c.get("source", "?") or "?").split(":", 1)[0]
        by_source.setdefault(src, []).append(c)
    for src in sorted(by_source):
        out.append(f"### {src}")
        out.append("")
        for c in sorted(by_source[src], key=lambda x: x.get("command", "")):
            purpose = (c.get("purpose") or "").strip().replace("\n", " ")
            if len(purpose) > 100:
                purpose = purpose[:97] + "..."
            out.append(f"- `{c.get('command','')}`" + (f" — {purpose}" if purpose else ""))
        out.append("")
    out += [
        "---",
        f"Regenerate after the system changes: re-run `/arlo:start`, or the auto-refresh",
        "hook keeps this current. This file is safe to read when nothing else works.",
        "",
    ]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="render arlo's lights-out runbook from cards")
    ap.add_argument("cards", help="a cards.json from arlo.cards")
    ap.add_argument("--out", help="write here (e.g. .arlo/LIGHTS-OUT.md); default stdout")
    ap.add_argument("--project", default=None)
    args = ap.parse_args(argv)
    with open(args.cards) as f:
        cards = json.load(f)
    md = render(cards, project=args.project, cards_path=args.cards)
    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w") as f:
            f.write(md)
        print(f"wrote lights-out runbook ({len(cards)} commands) -> {args.out}")
    else:
        sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
