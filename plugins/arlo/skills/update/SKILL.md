---
name: update
description: "Re-sync arlo with reality: re-harvest this project's ground truth (cards are a regenerated projection, never stored), pick up any arlo skill improvements, and report what drifted — the guard against a card that still says `--parent` after the flag became `--parent-id`. Run periodically and whenever the project's commands change."
---

# arlo:update — re-sync arlo with the ground it stands on

arlo's whole reason to exist is that stored command knowledge rots: a hand-maintained table
said `--parent` for four months after the real flag became `--parent-id`, and everyone who
trusted it created orphans. A `.arlo/cards.json` left alone becomes exactly that table. So
cards are **a regenerated projection of live ground truth, never stored truth** — and this
skill is how you regenerate them. Run it periodically, and after anything changes the
project's commands.

Update reconciles **this project** against the arlo you already have installed. It does *not*
fetch a newer arlo — that is **/arlo:upgrade** (pull the latest arlo from upstream, then run
this to reconcile). Keep the two axes distinct: `upgrade` changes *arlo*; `update` re-reads
*your project*.

`REFERENCE.md` (bundled beside this file) carries the full harvest rules (§2) and gradient.

## Steps

1. **Sync the project's core to the installed arlo.** Copy the core the lights-out `arlo`
   CLI runs (under arlo's home) from the *currently installed* plugin, so the project runs
   the arlo you have. (If you want a *newer* arlo — new harvest rules, a new rung, a sharper
   ranking — run **/arlo:upgrade** first; it fetches the latest arlo, then runs this step.)

2. **Re-harvest from the *current* live sources.** Re-run the harvest named by the project's
   card spec against the sources as they are right now — the same generation as setup, run
   fresh — into a new cards set:

       python3 -m arlo.cards <spec.json> --root . --out .arlo/cards.json.new

   Apply §2's completeness rules again; the surface may have grown or shrunk since setup.

3. **Diff, and report the drift out loud.** Compare the new cards against the cached
   `.arlo/cards.json` and tell the operator what changed:
   - **added** — a real command that now exists and had no card,
   - **removed** — a card whose source no longer exists (a moved or deleted script/target),
   - **changed** — same intent, **different command skeleton or purpose** (a renamed flag, a
     rewritten usage). This is the `--parent → --parent-id` case; surface it explicitly, it
     is the single most important thing update finds.
   If a source named in the spec has vanished, say so — do not silently drop it.

4. **Promote and re-stamp.** Replace `.arlo/cards.json` with the new set and stamp it with
   the current git SHA / mtime. **Preserve `.arlo/config.json`** — the model tier is the
   operator's decision, not something to re-resolve unless they ask. Regenerate
   `.arlo/LIGHTS-OUT.md` from the refreshed cards.

5. **Re-verify.** Run a couple of real intents through `arlo <words>` and confirm each
   answer is still a real, grounded command.

Update is **idempotent and safe to run often** — on an unchanged project it re-harvests to
the same cards and reports "no drift." The cost of running it too often is nil; the cost of
not running it is arlo becoming the stale table it was built to replace.
