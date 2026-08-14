# arlo: decisions

The record a fresh session should read before touching anything. Decisions made, and
the ones still open. (This project depends on none of its authors' internal tooling;
this file is where continuity lives, not an issue tracker.)

## Made

- **arlo is petard, extracted.** petard is the no-frontier operational fallback
  operator from the `hoistable` project. It was good enough to stand alone, so it was
  pulled out into this repo. Lineage and the full design: [`design.md`](design.md).

- **The name is arlo: A Real, Local Operator.** "petard" only worked inside hoist (the
  "hoist by your own petard" pun) and reads badly on its own. "Real" carries the
  invariant: arlo hands back a *real* command, never an invented one. Tagline:
  lights-out ops, arlo is who is on shift when the frontier goes dark.

- **hoist keeps its operator named petard.** The pun stays where it lands. hoist's
  `petard` operator becomes "hoist consuming the arlo skill" under the hood. arlo does
  not know or care that hoist exists.

- **Trademark: a known, accepted, minor risk.** Arlo is also a consumer-camera brand
  (Arlo Technologies). Trademark is scoped by class and likelihood of confusion, so a
  developer ops-skill vs IoT hardware is a weak collision (the Apple Records / Apple
  Computer split). Residual risk is discoverability/SEO, not legal. Accepted as
  non-blocking; revisit only if arlo goes broadly public as a product.

- **The invariant is sacred and narrow.** arlo never invents a command that is not real
  ground truth. It may surface the *wrong real* command (and shows confidence +
  alternatives so the operator can tell); it may never hand back a command that does
  not exist. Every capability is built to preserve this, structurally where possible.

- **Design center: a grounded LOM on a labeled trust gradient, not "lookup only".**
  The local model does the hardest thing it can while still pointing at ground truth,
  and every answer is labeled with the trust it earned. Rungs 0 (retrieval) and 1
  (slot-fill) are built and tested; rungs 2–6 are designed. Full table in
  [`design.md`](design.md).

- **License: LGPL-3.0-or-later.** A user can add arlo to any project, including
  proprietary ones, while modifications to arlo itself stay open, the right fit for a
  drop-in operator. GPLv3 is in `COPYING`, the LGPLv3 additional permissions in
  `COPYING.LESSER`. Copyright is recorded as "the arlo authors"; change it if a specific
  entity should hold it.

## Open (decide with evidence, do not guess)

- **How hoist reacquires arlo: vendor-with-pin vs reference.** Recommendation on the
  table: arlo is source-of-truth here, and hoist acquires it through hoist's own
  emit/package mechanism (it packages arlo, then consumes the skill it built) so there
  is no drift and no new dependency type. Not yet wired. This is a hoist-side decision;
  arlo does nothing to accommodate it.

- **Provision a real local LOM (gguf via llama.cpp) and grade rungs 1+ against it.**
  Today `provision.sh` pulls a rank-only sentence-transformer (enough for rung 0), and
  the binder runs deterministically with no model. Rungs 1–5 want a small instruct/coder
  model, a different model class. The *quality* of a live model's ranking and
  slot-binding is ungraded until this lands. Honest yardstick to adopt: InterCode-ALFA.

- **Build the DANGER/CAUTION denylist over the assembled command.** arlo has no general
  safety layer today because ground truth *was* its safety. `binder.py` enforces only a
  minimum floor (a slot value may not carry shell metacharacters). A real denylist
  (recursive deletes, raw device writes, fork bombs, credential exfil) is needed before
  any generative rung (rung 6) or once model-controlled slot values are common. Harvest
  the pattern from `ThorOdinson246/whatisit-nl2sh`.

- **Rungs 2–6.** reason-rank/disambiguate (2), explain/dry-run narrate (3), compose real
  cards (4), synthesize a card from source (5), free NL→shell generation for the genuine
  no-card tail (6, labeled unverified). Designed, not built. See [`design.md`](design.md).

## What is built and tested right now

- Card generation from ground truth (`arlo/cards.py`, `arlo/build_corpus.py`).
- Rung 0 retrieval (`arlo/translate.py`): select a card, return its command verbatim,
  say "no confident match" below a floor rather than guess.
- Rung 1 slot-fill (`arlo/binder.py`): bind a real template's hole from intent; the
  binder returns slot *values* only and `fill()` assembles from the real template, so
  the command skeleton cannot drift; a value carrying shell metacharacters is refused.
- 12 hermetic tests (`tests/test_grounding.py`, `tests/test_host_translate.py`),
  graded on real host ground truth (a script `Usage:` line and `ls --help`), no model
  download. Run: `python3 tests/test_grounding.py && python3 tests/test_host_translate.py`.
