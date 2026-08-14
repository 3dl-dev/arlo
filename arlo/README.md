# arlo/ — the neutral core (subordinate to the skill)

This is **not** where arlo's capabilities live. The product is [`../SKILL.md`](../SKILL.md),
executed by an agent. Code lives here **only when a guarantee must hold by construction** —
when prose asking a model nicely cannot enforce the invariant. Everything else is skill
prose the agent performs, not a module here.

The rule, before you add or grow a `.py` here (this is the altitude invariant from
[`../CLAUDE.md`](../CLAUDE.md), applied locally):

> A rung / capability is **SKILL.md prose** the agent executes, **unless** it needs a
> structural guard — a mechanism that keeps a model from emitting a non-ground-truth
> command by construction. Only then does it earn code here.

What earns its place (each is a structural guarantee, not intelligence):

- `cards.py`, `build_corpus.py` — harvest ground truth; a card can only be *generated* from
  a real source, never hand-written, so it cannot drift.
- `translate.py` — `rank()` selects among real cards; every returned command is a card's,
  verbatim.
- `binder.py` — `fill()` assembles from the real template; the binder returns slot *values*
  only, so the skeleton cannot drift (`skeleton_intact`).
- `ground.py` — the rung 2–6 structural seams: `select` (id → real command, refuse a
  non-candidate), `compose` (real cards only), `card_grounded`, `cited_flags_grounded`,
  `unverified` (rung 6 can never wear a grounded rung's confidence).
- `cli.py` — the lights-out `arlo <words>` entry; `runbook.py` — the durable fallback.

The *reasoning* of rungs 2–6 (reason-rank, explain, compose, propose, generate) is **not
here** — it is `SKILL.md`, done by whatever model runs the skill. A first pass built those
rungs as five parallel Python modules (~730 lines); that was the mode failure, corrected to
this one small core. Do not re-grow it. If a new capability tempts a module, it is almost
certainly skill prose.
