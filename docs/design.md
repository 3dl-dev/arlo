# arlo: a real, local operator (extracting petard as a standalone product)

**arlo** is petard pulled out of hoist to stand on its own, so a user can add it to
**any** repo, independent of hoist, and so hoistable can package it the same way it
packages any app. Decisions made and still open live in [`decisions.md`](decisions.md).

The name matters: "petard" only ever worked *inside* hoist (the "hoist by your own
petard" pun) and reads badly on its own. The standalone product is **arlo, A Real,
Local Operator**, lights-out ops. "Real" is the invariant: it hands you a real
command, never an invented one. hoist keeps its operator named **petard** (the pun
stays home); hoist's petard operator becomes "hoist consuming the arlo skill."

## What arlo is

The no-frontier operational fallback: when the frontier model is down and credits are
out (the lights are out), you type your own words ("bounce the deriver", "reset a
password") and arlo hands back the exact command to run, grounded in the system's own
ground truth. It runs on an independent path (local model, no frontier network).

**Why the fallback matters.** AI is quietly atrophying operational capability — the
operator included. When the session/token limit hits, the frontier-dependent operator
can barely touch their own products; when a model gets yanked (cf. Gene Kim's account of
Fable being pulled and Opus unable to pick up the slack), they are up a creek. arlo
solves for that by **intentionally distilling operational aspects downstream** —
grounding the operational surface locally so operational capability does not evaporate
when the frontier goes dark. That is why the trust gradient is built *all the way* to the
no-card tail: stopping short strands the operator exactly where the fallback is most
needed.

The invariant is narrow and sacred:

> **arlo never invents a command that is not real ground truth.** The worst it can do
> is surface the wrong *real* command, and it shows its confidence and the
> alternatives so the operator can tell.

The failure it exists to prevent: a hand-maintained flag table documented `--parent`
for four months after the real flag became `--parent-id`, and everyone who trusted it
created orphans. arlo answers from the live command surface.

## Why the extraction is cheap (the seams already existed)

- The core (`cards.py`, `translate.py`, `build_corpus.py`) is **stdlib only**, zero
  hoist imports.
- Dependency direction was already correct: hoist's `sysop` called *into* petard;
  petard called nothing of hoist's.
- The one coupling, "run a command in this environment", was already
  dependency-injected. The host runner (`_host_run`) runs on the host; an injected
  `environment_runner` runs wherever the system actually lives. arlo names nothing
  about your environment; you inject how to reach it.
- The embedder is pluggable (`rank(embed, ...)`), so grounding is testable with a
  deterministic model-free embedder.

So the real extraction is a **move**, not a rewrite, and hoist reacquires arlo through
its own emit/package mechanism (it packages arlo, then consumes the skill it built):
no drift, no new dependency type. The repo is now cut (this one); how hoist reacquires
arlo (vendor-with-pin vs reference) is still open, see [`decisions.md`](decisions.md).

## The design center: a grounded LOM on a labeled trust gradient

petard's original rule, *"the model selects, it never writes,"* collapsed two things:
the real invariant (**never invent a command that isn't ground truth**, sacred) and a
weak implementation of it (**only cosine-rank a fixed card list**, which leaves most
of a capable local model on the table). arlo keeps the first and drops the second: the
local model (the **LOM**) does the hardest thing it can while still pointing at ground
truth, and every answer is **labeled with the trust it earned**.

| Rung | Capability | Grounding | Status |
|---|---|---|---|
| 0 | rank-and-return a card verbatim | full | **built + tested** |
| 1 | **slot-fill a real card template** (bind args into a verbatim skeleton) | skeleton real, slot inferred | **built + tested** |
| 2 | reason-rank / disambiguate with an explainable *why* | full | **built + tested** |
| 3 | explain / dry-run narrate the chosen real command | full | **built + tested** |
| 4 | compose real cards | per-atom real, composition inferred | **built + tested** |
| 5 | synthesize a card from source it reads (human reviews) | summarizes real source | **built + tested** |
| 6 | free NL→shell generation for the genuine no-card tail | none, labeled unverified | **built + tested** |

Rungs 0–3 keep the invariant fully intact. Rung 1 is the first step past lookup and
the design center: cards are real command *templates* (`docker compose restart
[service]`), and the LOM binds the argument from intent ("bounce the deriver" →
`docker compose restart deriver`). Structurally, a binder only ever returns slot
*values*; `fill()` assembles the command from the real template, so no binder,
deterministic or a large model, can alter the skeleton. A slot value carrying shell
metacharacters is refused so a hole cannot chain a second command.

## The generative parallel, reviewed and placed

`ThorOdinson246/whatisit-nl2sh` (Qwen2.5-Coder-1.5B, GGUF Q4_K_M, 941MB, ~1.6GB
resident, ~0.6s CPU, 62% InterCode-ALFA) proves a capable NL→shell model runs locally
in ~1s. It is also arlo's **inverse**: free generation, "emits commands that will
destroy data," ~11% adversarial corruption, safety a denylist "not a sandbox." So it
is **not** a drop-in engine, that breaks the invariant; its only place is rung 6,
labeled ungrounded. One thing is worth harvesting; one tempting thing is explicitly not:

- **InterCode-ALFA as an honest yardstick — harvest.** arlo has no NL→command accuracy
  benchmark; even the grounded rungs deserve one.
- **Its DANGER/CAUTION denylist — declined, not deferred.** A general "what not to run"
  denylist is *not* on arlo's roadmap. A reliable oracle for what not to run is isomorphic
  to a better oracle for what to run — if we had it we would make it first-class and use it
  for the primary job. There is no good general answer, so safety responsibility stays with
  the operator, on their own system. This is consistent with what LOM is: **not an
  alternative SOTA model, but a shortcut past reading all the docs — cutting to the real,
  grounded answer in project/config context.** arlo surfaces the command; the operator
  decides to run it. The only safety arlo commits to is the structural metacharacter guard
  in `binder.py` (enforced by construction, not a semantic judgment). See
  [`decisions.md`](decisions.md).

The point is not the NL2SH product: it is that **more local capability is leverageable
than a simple lookup**. The trust gradient is how arlo takes that capability without
paying for it in honesty.

## Runtime cost, stated honestly

Rungs 1–5 want a generative LOM (an instruct/coder model, not today's rank-only
sentence-transformer embedder). Which one is a **resource gradient the operator
resolves**, not a model arlo ships: an 8×H200 RunPod fallback, an RTX 3060 mobile, or a
bare CPU — whatever the operator has or chooses to make available when the lights are
out. arlo names no point on that gradient; the project's requirements and the operator's
cost decision do (see [`decisions.md`](decisions.md)). `provision.sh` resolves the
embedder now (rung 0). The cheap reference point — a small gguf served by `llama.cpp`,
whatisit's envelope (~1GB disk, ~1.6GB resident, sub-second CPU) — is the affordable
floor and what we grade against; the frontier-dark budget scales up from there.

## What the spike proved (`arlo/`), and what it did not

Proved, for real and hermetically (deterministic embedder/binder, no model download,
exactly as arlo's existing grounding test works):

1. **Clean carve** — `arlo/` imports nothing hoist-specific; `grep` for
   petard/substrate/contract/sysop/envelope in the code is clean; its tests run on
   their own.
2. **Host-run path** — arlo harvests a card from real ground truth on the box (a
   script's `Usage:` line and `ls --help` via `_host_run`) and translates a query into
   that card's command verbatim. No substrate, no frontier, no injected environment.
3. **Rung 1** — the binder fills a real template's hole from intent, and
   `skeleton_intact` proves the fixed scaffolding never drifts; a binder that returns
   a whole command changes nothing, and a slot value smuggling `; rm -rf /` is refused.

All seven rungs (0-6) are now built with structural, model-free tests: 24 hermetic
cases across `tests/test_{grounding,host_translate,ground}.py`. Rungs 2-6 are SKILL.md
procedures backed by a small model-agnostic core (`arlo/ground.py`, ~120 lines); each
rung's structural guarantee is proven without a model download. See
[`decisions.md`](decisions.md) "What is built and tested right now".

Not done, stated plainly:

- No live LOM provisioned or graded. The *quality* of a real model's ranking,
  slot-binding, reason-ranking, composition, and proposal is ungraded until the
  oracle-as-judge loop runs on a target (STEP 3); the rungs grade the grounding
  **mechanics** hermetically and label live-model inference as the boundary.
- The DANGER/CAUTION denylist is **declined**, not pending (decision Q2): safety is the
  operator's; the only structural safety arlo commits to is the rung-1 metacharacter
  floor on slot values.
- The build workflow is STEP 1 (skill toolset — now complete through rung 6) → STEP 2
  (hoist distribution) → STEP 3 (hoist onto a target and grade). STEP 2 and STEP 3 are
  not yet built; see [`decisions.md`](decisions.md).
