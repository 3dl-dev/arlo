---
name: remove
description: "Cleanly remove arlo from this project: take the `arlo` command off the PATH and delete the project's `.arlo/`. Asks before deleting the shared local-model runtime, which other projects may still use. Never touches the project's own ground truth."
---

# arlo:remove — take arlo back out cleanly

arlo owns nothing but its **projection** of this project's ground truth (the cards, the
config, the runbook) and the `arlo` command that reads it. Removing arlo deletes that
projection; it never touches the project's real scripts, Makefiles, or commands — those were
never arlo's. Everything removed here is regenerable by **/arlo:start**.

## Steps

1. **Unwire the command.** Remove the `arlo` PATH entry that `/arlo:start` added (the
   launcher line / symlink pointing at arlo's home). Confirm `arlo` no longer resolves.

2. **Delete this project's `.arlo/`.** Remove `.arlo/cards.json`, `.arlo/config.json`,
   `.arlo/LIGHTS-OUT.md`, and any runbook. This is a cache and a projection — safe to delete,
   fully rebuilt by a later `/arlo:start`.

3. **Ask before removing the shared model runtime.** The local model provisioned at setup
   (e.g. under `~/.local/share/arlo`, wherever the operator put it) is **shared across every
   project that uses arlo** — deleting it breaks the others. Default to leaving it; remove it
   only if the operator confirms this was the last project using arlo.

4. **Report what was removed vs left.** Say plainly: the PATH entry and `.arlo/` are gone;
   the shared runtime was left (or removed, if confirmed); the project's own ground truth is
   untouched. Uninstalling the plugin from the agent, if wanted, is a separate agent action.
