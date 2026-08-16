---
name: upgrade
description: "Pull the latest arlo from upstream (new rungs, sharper harvest rules, fixes), then reconcile each project with /arlo:update. This is how arlo-the-tool moves forward; /arlo:update only re-reads your project against the arlo you already have."
---

# arlo:upgrade — get the latest arlo, then reconcile

Two things drift, and they need different verbs. Your **project's** commands change — that
is **/arlo:update**, which re-harvests your ground truth against the arlo you already have.
**arlo itself** also improves — new rungs, sharper harvest rules, a fix to how it ranks. To
get *that* you must pull the latest arlo from where you installed it. That is this skill.

Think `apt update` vs `apt upgrade`: `update` refreshes arlo's index of *your project*;
`upgrade` installs a newer *arlo*. Run upgrade while the frontier is up — it reaches upstream,
so it is a get-ahead-of-the-disaster action, like setup.

## Steps

1. **Pull the latest arlo from upstream.** Use your agent's own plugin-update mechanism —
   arlo names nothing about your harness, and each agent (opencode, pi, hermes, …) has its
   own way to refresh an installed plugin. In **Claude Code**:

       /plugin marketplace update          # refresh the marketplace metadata
       /plugin update arlo@arlo            # upgrade the installed plugin in place

   (then `/reload-plugins` to apply). Use `/plugin update` — re-running `/plugin install`
   does *not* upgrade. This refreshes the *installed* plugin: its `SKILL.md`, the lifecycle
   skills, and the neutral core.

2. **Note the version delta.** Report the arlo version you moved from → to (the plugin's
   `version`) and, briefly, what changed that matters for grounding — a new rung, a new
   harvest rule, a ranking fix. If nothing moved, say "already on the latest" and stop.

3. **Reconcile every project with /arlo:update.** A newer arlo can harvest and rank
   differently, so each project's `.arlo/` must be re-reconciled against it: run
   **/arlo:update** in each project that uses arlo. That step syncs the project's bundled
   core to the freshly-installed arlo, re-harvests its ground truth, and reports any drift.
   arlo does not track which projects those are — you point it at them.

Upgrade is a **frontier-up** action: it pulls from upstream, so it cannot help once the
lights are out. Do it ahead of time, so the arlo waiting for you in the dark is the current
one. Nothing here touches any project's own ground truth — only which arlo reads it.
