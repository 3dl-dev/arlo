---
name: start
description: "Set up arlo for this project while the frontier is up: harvest the project's real ground truth into capability cards, resolve the local-model tier, and wire the `arlo` command so lights-out ops work when the frontier is down. Run once per project. Also invocable as /arlo:setup."
---

# arlo:start — set arlo up for this project

Run this **once per project, while the frontier is up**, so arlo can answer when it is
down. Setup harvests this project's own ground truth, resolves the model that will run the
skill, and leaves an `arlo` command on the PATH. Nothing here is arlo-specific to invent —
every command arlo will later hand back is harvested from *this project's* real sources.

`REFERENCE.md` (bundled beside this file) is the full arlo document — the trust gradient
(rungs 0–6), the complete harvest rules (§2), and the lights-out use surface (§3–§4). Read
it for depth; this skill is the setup procedure that stands on it.

## Steps

1. **Resolve the model tier (REFERENCE.md §1).** The model that runs arlo is the operator's
   choice along a resource gradient — the agent's own model, a small local one, or none.
   Record the choice in `.arlo/config.json`. If a local model was chosen, provision it now
   with the bundled `provision.sh` (it runs on an independent path, so it works when the
   frontier is gone). A trivial tier (use the harness model, or none) just records the choice.

2. **Harvest the ground truth (REFERENCE.md §2).** Point a small card spec at *this
   project's* real sources — its scripts, Makefiles, verb-dispatched CLIs, and the `--help`
   of the infra commands actually run here — and generate `.arlo/cards.json`:

       python3 -m arlo.cards <spec.json> --root . --out .arlo/cards.json

   Card the **canonical surface completely** — undocumented Makefile targets, every real verb
   of a dispatcher, `--help` subcommands even under a nonzero exit — per §2's rules. Cards are
   *generated, never authored*, so they cannot drift from the tool. Stamp the cache with the
   git SHA / mtime it was harvested at.

3. **Write the lights-out fallback.** Generate `.arlo/LIGHTS-OUT.md` (a dated last-resort
   snapshot) and any project runbook from the harvested cards.

4. **Wire the command.** Put `arlo` on the PATH (the bundled `bin/arlo` launcher resolves
   arlo's home and walks up from any cwd to find `.arlo/`). After this, `arlo <your words>`
   answers from a shell with no agent and no frontier.

5. **Verify against real ground truth.** Run two or three real intents through `arlo <words>`
   and confirm each answer is a real command from the harvested surface, labeled with its
   rung, and that a nonsense intent yields "no confident match" rather than a guess.

## After setup

Cards are a **regenerated projection of live ground truth, never stored truth** — the ground
shifts (a flag renamed, a script added, a verb removed) and arlo itself improves. So this is
not one-and-done: run **/arlo:update** periodically and after the project's commands change,
to re-harvest and surface drift. Uninstall cleanly with **/arlo:remove**.
