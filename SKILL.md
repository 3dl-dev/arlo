---
name: arlo
description: "Lights-out ops. A real, local operator: when the frontier model is down and credits are out, you type your own words and arlo hands back the exact command to run, grounded in your system's own ground truth. It never invents a command."
---

# arlo, a real, local operator

arlo keeps you able to operate when the lights go out, when the frontier model is
down or rate limited and you still need to act. You type your own words ("bounce the
deriver", "reset a password", "restart"), and arlo hands back the command to run. It
runs on an independent path (local model, no network to the frontier). A pile of docs
nobody reads at 3am is not arlo; a model that makes up plausible commands is worse.

**The invariant is narrow and sacred: arlo never invents a command that is not real
ground truth.** The worst it can do is surface the wrong *real* command, and it shows
its confidence and the alternatives so you can tell. It can never hand you a command
that does not exist. The concrete failure this prevents: a hand-maintained flag table
documented `--parent` for four months after the real flag became `--parent-id`, and
everyone who trusted it created orphans. arlo answers from the live command surface.

## The trust gradient

arlo's honesty is not "it only does lookup." It is that every answer is **labeled
with the trust it earned**. The local model's job rises as far as it can while still
pointing at ground truth:

- **rung 0, retrieval** *(built)*: select a capability card and hand back its command
  verbatim. Full grounding.
- **rung 1, slot-fill** *(built)*: bind the argument of a real command *template*
  from your words ("bounce the deriver" -> `docker compose restart deriver`). The
  command skeleton is still verbatim ground truth; only the slot value is inferred,
  and it is shown so you see exactly what was bound.
- **rung 2, reason-rank / disambiguate** *(built)*: when the blind similarity score
  cannot separate two real cards, hand the shortlist to the local model to choose
  *which real card* with an explainable *why*. The model returns a card **id**, never
  a command; arlo emits that card's command verbatim. Full grounding — it only ever
  re-orders real cards.
- **rung 3, explain** *(built)*: narrate what the chosen real command does — from the
  command's *own* harvested `--help`, never from memory. Any flag the narration cites
  must be a real token in that help, so a renamed flag (`--parent` after it became
  `--parent-id`) is caught, not waved through. Still grounded.
- **rung 4, compose** *(built)*: chain several *real* cards into an ordered runbook.
  Each atom is ground truth; the *composition* (which cards, what order) is inferred,
  so this is the first rung below full grounding and is **labeled less-trusted**. The
  model returns an ordered list of card ids, never commands, and steps are shown
  discretely rather than joined into one shell line, so each stays verifiable.
- **rung 5, propose** *(built)*: when no card fits, read real source (a `--help`, a
  runbook, a script) and *propose* a new card. The proposed command's skeleton must
  appear verbatim in that source, and the proposal is **review-required** — a draft,
  never auto-adopted into the corpus. Grounded to the source it read, but not yet
  harvested ground truth.
- **rung 6, generate** *(built)*: only at the very end, when rungs 0-5 all come up
  empty, free generation for the genuine no-card tail. This one *breaks* grounding, so
  it is always labeled **UNVERIFIED** — invented, not ground truth — and can never wear
  a grounded rung's confidence. No model on the box means rung 6 is unavailable and
  arlo abstains rather than guess.

## 1. Provision the local model (while the frontier is up)

    arlo/provision.sh [runtime_dir] [model_name]

arlo cannot assume a model exists on the box, so setting one up is part of its job.
It provisions a small CPU model on an independent path. Do it while things work, so
arlo can answer when they do not.

## 2. Extract capability cards from ground truth

    python3 -m arlo.cards <spec.json> --root <checkout> --out cards.json

A card pairs a command with its ground-truth purpose and its source. Cards are
generated, never authored: a shell script's header comment is the purpose and its
`Usage:` line is the command; a **verb-dispatched** script (`mainframe rail`, `mf
status`, `git commit`) yields one card *per verb*, the verbs read from the script's
real `case` dispatch so a verb it does not have is never carded; a universal infra
command (`docker compose restart`, `kubectl rollout restart`) is harvested from its own
`--help`. There is no path to hand-write a card, so it cannot drift from the tool it
describes. The spec keys are `scripts`, `dispatchers`, `makefiles`, `helpcards`.

**Card the canonical surface, completely — a real command it drops is a real command
the operator won't get.** Two rules that ground-source testing has shown matter:

- **Makefiles: card *every* recipe-bearing target, not only the `##`-documented ones.**
  An undocumented target is real ground truth whether or not someone wrote a `##` above
  it; its purpose falls back to the target name or its first recipe line. (The
  deterministic `arlo.cards` parser keys on `##`; when you run the harvest, complete it by
  carding the undocumented targets straight from the `Makefile` — they are ground truth
  too.) Skip only build-system-generated noise (`cmake_*`, `edit_cache`, `rebuild_cache`,
  `depend`, …). When a target merely *wraps* a lower-level command, the target is the
  operator's canonical surface: return `make <target>`, not the command it wraps — both
  are real, but for a shop that drives ops through `make` the wrapped one is the *wrong
  real* command.
- **`--help` harvesting tolerates a nonzero exit.** Some tools (e.g. `go`) exit 2 on
  `--help` yet still print their real subcommands; the subcommands are ground truth
  regardless of exit code. Card them rather than forcing a higher rung to recover.

## 3. Translate intent into a grounded command (when the lights are out)

    "$runtime/venv/bin/python" -m arlo.translate cards.json "reset a password"

The local model embeds the query and the cards and picks the closest, hybrid of
semantic similarity (so "bounce" reaches "restart") and lexical overlap weighted
toward the command signature. It returns the chosen card's command verbatim, its
confidence, and the runners-up, and below a confidence floor it says it has no match
rather than guess.

## 4. Fill the blank in a real command (rung 1)

    python3 -m arlo.binder card.json "bounce the deriver"

When the chosen command is a template with a hole, arlo binds the hole from your
words. It returns slot *values* only; the command is assembled from the real
template, so the skeleton can never drift. Unbound slots are shown as blanks for you
to fill. Off the box a local model does the binding; a deterministic binder ships so
the mechanism runs and is tested with no model installed.

## Rungs 2-6: you reason, `ground.py` keeps you honest

Rungs 0-1 are commands you run (`translate`, `binder`). Rungs 2-6 are yours to *reason*:
**you are the model running this skill** — the harness's model, or a small local one the
operator wired up in their own context (arlo brings the skill and the grounding core, not
a model). This section says how to think; `arlo/ground.py` is the small seam you call so
that what arlo hands back is still ground truth, not your tokens. Climb only as far as the
answer needs, and label every answer with the rung it used. `binder.py` is the reference
for how a standalone local model plugs in.

### Rung 2 — reason-rank / disambiguate  *(full grounding)*
Get the real candidates from §3. When the top score is ambiguous (runners-up bunched, or
the intent names something the command signature does not), decide *which real card* fits
and say *why*. Return the card **id**, never a command, and call `ground.select(candidates,
id)` to emit its command verbatim — a non-candidate id is refused, so you can only ever
re-order real cards.

### Rung 3 — explain  *(full grounding)*
To explain a command before it runs, narrate from the command's *own* harvested `--help`
(§2), never from memory — narrating from memory is exactly how the `--parent` lie happens.
Call `ground.cited_flags_grounded(narration, help)`: every flag you cite must be a whole
token in the real help (`--parent` is not satisfied by `--parent-id`), or it is surfaced
as a discrepancy. This is prose, not a command — a floor on the explanation's honesty.

### Rung 4 — compose  *(atoms real, order inferred — less trusted)*
When one command is not enough, plan a short sequence out of *real* cards. Return an
ordered list of card **ids**; `ground.compose(cards, ids)` emits each command verbatim in
order and drops (and reports) any id that is not a real card. Present the steps discretely,
not joined into one `a && b` line, so each stays verifiable. **Label it less-trusted —
verify the order.**

### Rung 5 — propose  *(summarizes real source — review required)*
When no card fits, read real source (a `--help`, a runbook, a script) and draft a card.
Call `ground.card_grounded(command, source)`: the proposed command's skeleton must appear
verbatim in the source you read, or it is refused. A proposal is always a **review-required
draft**, never auto-adopted into the corpus. Label it two ways: grounded-to-the-source, and
not-yet-ground-truth-pending-review.

### Rung 6 — generate  *(no grounding — UNVERIFIED)*
Only when rungs 0-5 have all come up empty. Write a command from scratch — it is **not**
ground truth. Stamp it with `ground.unverified(command)`: `grounded=False`, a permanent
**UNVERIFIED** label, no path to a grounded rung's confidence. Deliberately no
danger/denylist (decision Q2) — safety is the operator's, on their own system. With no
model, rung 6 is unavailable; abstain rather than guess.

## Adding arlo to any project

arlo depends on nothing but the standard library. Point its card spec at your project's
real ground truth (scripts, Makefiles, the `--help` of the infra commands you actually
run) and arlo answers from that surface. The *model* is not arlo's to ship: it is
whatever runs this skill — the harness's model, or a small local one you provision in
your own context. That choice is a resource gradient you resolve (an 8×H200 fallback, an
RTX 3060, a bare CPU — whatever you have and will use); arlo names no point on it, and
the grounding core keeps whatever model you bring honest. arlo names nothing about your
environment either; if your system runs somewhere other than the host, inject how to
reach it (`build_corpus.environment_runner`) and arlo harvests from there instead.

## Why this is the invariant

An arlo that lies is worse than no arlo. Its answers are generated from the live
command surface and point at a real command rather than reciting a remembered one.
The model *selects and fills*; it never *writes* the command shape. That is the line
that keeps every rung honest.
