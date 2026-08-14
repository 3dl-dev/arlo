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

- **License: LGPL-2.1-or-later.** The balance point. MIT/Apache are permissive but let
  an owner rug-pull a later version closed; GPL stays open but *contaminates* every
  consumer (they must go GPL too). LGPL keeps arlo's *own* changes open while letting any
  consumer, proprietary included, link it freely. Chosen at **2.1, not 3.0**,
  deliberately: LGPLv3 folds in GPLv3's anti-tivoization, patent, and anti-DRM
  expansions, more restrictive than the plain LGPL bargain we want. Full text in
  `COPYING` (LGPL-2.1 is a self-contained license, no GPL companion file needed).
  Copyright is "the arlo authors"; change it if a specific entity should hold it.

- **How hoist reacquires arlo: hoistable's builder produces the artifact hoist imports.**
  arlo is source-of-truth and iterates independently; hoistable's builder (the same one
  that packages any app) emits an arlo artifact, and hoist imports *that*. hoist upgrades
  to a newer artifact **at its own pace/demand**, so arlo's cadence never forces hoist's.
  No new dependency type, no drift: the builder is the seam. arlo does nothing to
  accommodate hoist; it just stays buildable by the standard mechanism. Not yet wired on
  the hoist side, but the acquisition model is now decided (was: vendor-pin vs reference).

- **The LOM is a resource gradient the operator resolves, not a model arlo ships.**
  "Local model" spans whatever the operator has or chooses to make available in a
  lights-out situation: a RunPod fallback with 8×H200, an RTX 3060 mobile, or a bare CPU
  (a 486-SX2 if that is truly all there is). arlo does not pick a point on that gradient
  and does not name one. arlo is the **recipe for integrating this capability into a
  project**: the *project's* requirements and the *operator's* cost/resource decision
  choose how the LOM is realized; arlo glues it together, integrates it into the project,
  and makes sure that project keeps arlo accurate and ready for LOM. This is invariants
  #4 (resolve, don't hardcode) and #6 (independence) applied to the model tier itself —
  the LOM is as resolved-not-hardcoded as the command surface is.

- **The harness's higher-order model is the LOM engine, oracle, and judge — grading uses
  it, not a separately-provisioned benchmark model.** arlo ships as a hoisted skill, so it
  *necessarily* runs inside a harness that already has a more capable model than the rung-0
  embedder. That model is what drives rungs 1+ and also what grades them (oracle and judge,
  necessarily). How much inference to commit to it is an **operator budget decision**, and
  it scales: a huge-budget operator who cannot privately host a frontier model can still
  spend enough tokens to make LOM work very well; a pauper spends best-effort until the
  token limit, and not all of it (many projects compete for the same budget). So the old
  "provision a gguf and benchmark it" framing was too narrow — we do not need a fixed local
  model to grade against; we need to wire the harness oracle in as judge. A concrete small
  gguf (whatisit's envelope) and InterCode-ALFA remain a *cheap reference floor* for a
  hermetic, harness-free grade, not the definition of the LOM. Residual open work: actually
  wire the oracle-as-judge grading loop; see the Open section.

- **No general DANGER/CAUTION denylist — safety responsibility stays with the operator.**
  Rejected as first-class. The reasoning: a reliable oracle for *what not to run* is
  isomorphic to a better oracle for *what to run* — if we had it, we would make it
  first-class and use it for the primary job instead. There is no good general answer, so
  the responsibility sits where it always has: with the operator, on their own system.
  This follows from what LOM actually is — **not an "alternative SOTA model," but a way to
  save the operator from reading all the documentation by cutting straight to the answer in
  project/config context.** arlo surfaces the real, grounded command; the operator decides
  to run it. The structural floor in `binder.py` (a slot value may not carry shell
  metacharacters, so a hole cannot chain a second command) stays, because it is cheap,
  real, and enforced by construction — not a semantic safety judgment. (was: "build the
  DANGER/CAUTION denylist"; the metacharacter guard is the only safety arlo commits to.)

- **Build the full trust gradient — all the way through rung 6. Rung 6 ships; it is not a
  permanent documented boundary.** The scope question is settled: 2 (reason-rank /
  disambiguate), 3 (explain / dry-run narrate), 4 (compose real cards), 5 (synthesize a
  card from source), and 6 (free NL→shell for the genuine no-card tail) are all in scope.
  Rung 6 breaks grounding, so it ships **labeled ungrounded / unverified** — the invariant
  holds because a rung-6 answer is never presented with a grounded rung's confidence, not
  because rung 6 is withheld. Order by invariant-preservation and value: 2→3 keep the
  invariant fully intact and are cheap and high-value, then 4→5 (progressively less
  grounded, labeled), then 6 last. Q2's ruling makes 6 shippable without a denylist: it
  carries its label, the structural metacharacter floor, and operator responsibility.

  **Why all the way (the reason the project exists).** AI is atrophying operational
  capability — the operator included. When the session/token limit hits, the operator can
  barely touch their own products; when a model gets yanked (cf. Gene Kim's account of
  Fable being pulled and Opus unable to figure things out), the frontier-dependent operator
  is up a creek. arlo solves for that by **intentionally distilling operational aspects
  downstream** — grounding the operational surface locally so operational capability does
  not evaporate when the frontier goes dark. A gradient that stops short of the no-card tail
  leaves the operator stranded exactly where they most need the fallback. Hence: all the way.

- **Heavy on skill, light on code — the distribution shape is a design constraint.** arlo
  ships as a *hoisted skill*, dropped into other people's repos. Nobody wants to run a pile
  of untrusted code, and a skill (an inspectable natural-language procedure the harness
  model executes) is far more trust-acceptable than a binary blob. So the intelligence lives
  in `SKILL.md`, executed by the harness oracle (Q1); the Python stays a **small, neutral,
  verifiable core** — only the primitives that must be enforced *by construction* (card
  harvest from ground truth, `rank`, `fill()`'s skeleton assembly, the metacharacter guard).
  This directly shapes rungs 2–6: reason-rank, disambiguate, explain, compose, synthesize
  are **skill instructions the harness model performs against the grounded primitives, not
  new Python modules.** Add code only where a guarantee must be structural (a property that
  cannot be trusted to prose — e.g. the skeleton-can't-drift property of `fill()`);
  everything else is skill. Less code is also less attack surface and less to audit before
  an operator will run it. This sharpens CLAUDE.md's standing "agent-first, the Python is the
  neutral core the skill calls" into a build directive: **when a rung could be skill or code,
  it is skill unless it needs code to hold the invariant.**

  **What arlo preseeds vs. what the operator resolves (the line that keeps this honest).**
  The tradeoff is: preseed enough that the skill has value beyond a one-off prompt, while
  staying generic enough to be future-proof as models advance and customized to what the
  operator has. arlo resolves it by shipping only the *model-agnostic* half: the structural
  grounding primitives (the invariant by construction — `arlo/ground.py`, `binder.fill`,
  the harvest/card machinery) plus the SKILL.md rung *procedures* (how to reason). Those
  are the reusable value and they do not change when the model does. The *model* and its
  *driving* (provisioning, prompts) are **not** shipped — they live in the operator's
  context, resolved along the LOM gradient (the model that runs the skill is the harness's,
  or a local one the operator wires up). `binder.py` stays as the single reference for how a
  standalone local model plugs into the seam; arlo does not carry a driver per rung.

  **Correction applied 2026-08-14.** A first pass built rungs 2-6 as five parallel Python
  modules (~730 lines) each mirroring `binder.py`'s deterministic + `llm_*` + CLI shape.
  That was too much code for a skill: the `llm_*` wrappers reimplement "prompt a model" —
  redundant with the harness model that already runs the skill — and the reasoning belongs
  in SKILL.md, not Python. Consolidated to `arlo/ground.py` (~120 lines: the ~5 structural
  primitives only); the rung reasoning moved fully into SKILL.md § "Rungs 2-6". Every
  structural guarantee and every rung kept; ~730 → ~120 lines of shipped code.

## Open (decide with evidence, do not guess)

- **Wire the oracle-as-judge grading loop for rungs 1+.** The judge is decided (the harness
  model, above); what is unbuilt is the loop that runs rung 1's binder against real intents
  and has the oracle grade the bound values. A concrete small gguf + InterCode-ALFA is the
  cheap hermetic reference floor to stand this up with. Until it lands, rung-1 *quality*
  (as opposed to rung-1 *mechanics*, which are tested) is ungraded and labeled as the
  boundary.

- **Build rungs 2–6, as skill first** (scope and order decided above; designed in
  [`design.md`](design.md), not yet built). Each rung is authored in `SKILL.md` for the
  harness model to execute against the grounded Python primitives — add code only where a
  guarantee must be structural (per "heavy on skill, light on code" above). A rung is not
  done until it is graded against ground truth per the ground-source testing invariant, and
  labeled with the trust it earns.

- **The build workflow is three steps, and arlo is the meta-tool — build the builder, not
  the instance.** arlo is "meta's meta": it builds the thing (a hoisted LOM operator) that
  works for the example projects; it is not built by hand-authoring an operator per project.
  The workflow is: **(1) write arlo as a skill toolset** — `SKILL.md` rungs plus the neutral
  core (harvest / rank / `fill()` / guard), generic over *any* target project; **(2) build
  it into a distribution with hoist** — hoistable's builder emits the arlo artifact (the
  acquisition decision above); **(3) use that distribution to LOM-manage the target
  projects** — hoist arlo onto mainframe / ready / etc., and the *hoisted* instance harvests
  that project's own ground truth and operates it. The corollary that keeps altitude honest:
  a mainframe-specific card set, eval set, or grader is an **output of step 3 applied to
  mainframe**, never part of arlo itself. If a piece of work names a specific target, it
  belongs to the testbed layer, not the shipped skill. (Course-correction, 2026-08-14: an
  early pass hand-built a mainframe intent set + Python grader inside `arlo/` — wrong layer
  and wrong sequence; relocated to the testbed layer as step-3 acceptance data.)

- **The interface: `arlo <your words>` at a shell, set up once by the agent.** Two
  surfaces, one product, and this resolves the paradox that arlo installs into an agent
  but is needed when that agent (the frontier) is gone:
  - **Setup — the agent, while the frontier is up (`/arlo:start`).** Harvest this
    project's ground truth into `.arlo/cards.json`, resolve the model tier the operator
    chose (the LOM gradient: a big local model, a small one, a self-hosted RunPod
    endpoint, or none — decided and provisioned **once, here**) into `.arlo/config.json`,
    write the lights-out runbook, and drop an `arlo` command on the PATH wired to all of
    it. A big setup happens here; a trivial one (small/local/none) just works after.
  - **Use — the shell, when the lights are out (`arlo <your words>`).** In the project
    folder where you'd normally run `claude`, you run `arlo restart the deriver` and it
    prints the real command. No agent, no frontier. `arlo` (see `arlo/cli.py`, launcher
    `bin/arlo`) walks up to find `.arlo/`, uses the configured model if reachable, and
    falls back to a model-free lexical match over the same real cards if not — a weaker
    answer, labeled `[no model]`, beats no answer. Below a confidence floor it says "no
    confident match" and points at `.arlo/LIGHTS-OUT.md`.
  This is the honest answer to "nobody runs the python": they run `arlo`, a clean CLI
  that hides the core. The quality of the answer tracks the resolved model tier; the
  model-free floor mis-picks on hard intents (labeled, low-confidence) — which is the
  whole reason the tier is an operator decision, not a shipped default.

## Build plan (decomposition of the two Open items)

Decomposed with swarm-plan discipline (outcome-scoped, ground-source done-conditions,
explicit order, pre-registered pass bar). **The executable work tree lives in rd** (project
`arlo`; the `.ready/` dir is gitignored, so it is local build-tracking only and never ships
with the standalone product — the product's independence is intact, and this file stays the
*design*-continuity record). Roots: `arlo-ed9` (Deliverable 1) and `arlo-a6a` (Deliverable 2);
`rd dep tree arlo-ed9`. All GPU work is ephemeral, low-priority pods via
`gpu submit -submitter arlo`; read logs not status; snapshot before cancel; version-bump
immutable env names; never re-submit a live name. `mainframe` is harvested **read-only** —
never run a mutating command against live infra.

**Pre-registered pass bar (set before any grading run — do not weaken to pass).** On the
held-out mainframe intent set: (a) the invariant is absolute — **zero** emitted commands
that don't resolve to real ground truth is a hard gate; any nonzero fails the run outright,
regardless of everything below. (b) rung-1 exact match (skeleton + bound slot) ≥ 70%.
(c) judge-graded "operationally correct" (would achieve the stated intent) ≥ 85%.
(d) abstention: on intents with no matching card, arlo says "no confident match" rather than
binding a wrong card ≥ 90% of the time.

### STEP 3 is an optimization loop, not a one-shot grade (reframe 2026-08-14)

STEP 3 is a **test that produces a loss function, back-propagated through the two upstream
artifacts — the hoist distribution (STEP 2) and the skill toolset (STEP 1) — to optimize
them**, and it runs across **all the pointed-at projects** (`mainframe`, `ready`, `vms`,
`enterprise_ai_framework`), not mainframe alone. The pass bar above is the per-project
acceptance target; the *loss* is how far each project is from it.

- **Test.** For each project: hoisted arlo harvests that project's real ground truth, answers
  a held-out intent set, graded against the project's own commands. Read-only harvest, never
  a mutating command against live infra.
- **Loss, decomposed by failure type** (each a separate gradient): (i) **harvestability** —
  a real command has no card at all; (ii) **retrieval** — the right card exists but is not
  selected; (iii) **binding** — right card, wrong slot fill; (iv) **abstention** — guessed
  when it should have declined, or declined when it should have answered; (v) **invariant**
  — emitted a command that is not ground truth (a hard, absolute failure). Aggregated across
  projects into one loss.
- **Backprop = attribution.** Each loss component names the upstream cause to fix:
  harvestability → `cards.py` / harvesting (skill toolset); retrieval/binding/reason-rank →
  the rungs + LOM (skill toolset); abstention → the confidence floor (skill toolset);
  invariant → a structural bug in `ground.py`/`binder.py` (skill toolset core); a project that
  fails to deploy/accept on a clean target → `config.json` (the distribution). Fix upstream,
  re-run, watch the loss fall. **The verb-aware-harvesting fix was the first gradient step:**
  the mainframe test showed a harvestability loss (verb-dispatched commands uncardable), which
  back-propagated into `cards.py` and drove `extract_dispatch_cards`.
- **Model-free vs LOM-graded loss.** Harvestability, abstention, and invariant components are
  **model-free** (computed now, across all projects, no rail); retrieval/binding/reason-rank
  quality needs the LOM (the rail phase). The loop starts with the model-free gradients and
  adds the LOM-graded ones when a model is on the rail.

The Deliverable-1 items below are the *rail-phase* (LOM-graded) slice of this loop; the
multi-project model-free slice runs first and is where the next gradients come from.

**Correction 2026-08-14 — the loss must grade the SKILL EXECUTED IN CONTEXT, not the code
we ship.** A repeating mode failure: `eval/loss.py` graded arlo's *shipped functions*
(`cards.build_cards`, `translate.rank`) called directly on specs authored in this repo, with
the model-free embedder. That is a hermetic unit test of the core — it caught a real dead-
embedder bug (offline-floor retrieval 0.75→0.39) — but it is **not** the STEP-3 loss. arlo's
product is what an *agent* produces when it runs the skill (`/arlo:start`, `arlo <intent>`)
in a project it has never seen, with the agent's own model as the LOM. So the STEP-3 loss is
**agent-driven**: spawn an agent per target project, have it follow `SKILL.md` to discover +
harvest + answer held-out intents, and grade its answers. Measured that way on mainframe:
**retrieval 28/28, abstention 6/6, loss 0.00** — the grounding core keeps every answer a real
card, the LOM closes the retrieval gap the offline floor could not, and the invariant held
end to end. `eval/loss.py` is relabeled the *offline-floor / core-mechanics* grade; improving
that floor is not improving the product, which runs with a real LOM. (A repeatable agent-
driven harness — a workflow fanning an agent across all projects — is the proper STEP-3
tool; the mainframe run above was done by hand to prove the method.)

**Deliverable 1 — arlo grades rung-1 binding against real ground truth on the rail.**
1. *Model weights reachable from rail jobs.* A small instruct/coder LOM (e.g.
   Qwen2.5-Coder-7B/14B) and a stronger judge (e.g. Qwen3-32B) are cached to a rail-visible
   volume so jobs don't re-pull per run. Done: a pod can load both from the cache. Prereq
   for 3. (Open sub-question: which shared models volume — resolve by inspecting the rail,
   not by standing up new infra.)
2. *arlo eval-job env image on the rail.* A `forge`/torch-base env `arlo-eval-vN` with
   python3, arlo's stdlib core, and a model runtime, pushed to the registry, **verified by a
   check run inside the container** (import + a real one-token generate), not host grep.
   Prereq for 3. Independent of 1.
3. *Held-out intent→command eval set, harvested read-only from mainframe.*
   `arlo/eval/mainframe_intents.jsonl`, N≥30 (natural-intent, expected-real-command,
   source-ref) tuples, where a validator asserts every expected command traces to a real
   mainframe source (a script `Usage:`, a Makefile target, a `--help`). Done: file exists +
   validator green. Independent of 1/2.
4. *Oracle-as-judge grading harness as one gpu batch job.* `arlo/eval/grade.py` (grading
   infra, not shipped skill code): in one pod, loads the LOM, runs the real rung-1 binder
   over each intent, assembles via `fill()`, has the judge model score each bound command vs
   the expected ground-truth command, writes `/outputs/scorecard.json` + summary. Done:
   `gpu artifacts arlo-grade` yields a scorecard whose entries show **real** generated
   commands and **real** judge rationales (mocking the model cannot satisfy this) and an
   explicit invariant-violation count. Depends on 1,2,3.
5. *Rung-1 quality graded and labeled.* Run 4, record the scorecard against the pass bar in
   this file, and move rung-1's status from "mechanics tested" to "graded: <numbers> vs
   bar." Below bar → file the gap as a new outcome; never weaken the bar. Depends on 4.

**Deliverable 2 — arlo climbs the trust gradient, rungs 2–6, skill-first.** Each rung is
authored in `SKILL.md` (harness model executes it against the grounded primitives; code only
where a guarantee must be structural), graded via the harness (extended), and labeled with
earned trust. Sequential by the invariant-preservation order.
6. *Rung 2 — reason-rank / disambiguate with an explainable why*; invariant fully intact;
   graded on ambiguous-retrieval intents. Depends on Deliverable 1.
7. *Rung 3 — explain / dry-run narrate the chosen real command*; graded for faithfulness
   against the command's own `--help`/man. Depends on 6.
8. *Rung 4 — compose real cards*; per-atom real, composition inferred → labeled less
   trusted; graded that every atom is ground truth and the composition is flagged inferred.
   Depends on 7.
9. *Rung 5 — synthesize a card from source (human reviews)*; labeled "summarizes real
   source, review-required"; graded for faithfulness to source + review gating. Depends on 8.
10. *Rung 6 — free NL→shell for the no-card tail*; emitted with the ungrounded/unverified
    label, the structural metacharacter floor, and operator responsibility (no denylist, per
    Q2); graded for **label integrity** (never shown with a grounded rung's confidence).
    Depends on 9.

Frontier at start: items 1, 2, 3 (independent). Critical path: 1/2/3 → 4 → 5 → 6 → 7 → 8 →
9 → 10 (~8 deep; rungs are genuinely sequential by the invariant order).

## What is built and tested right now

- Card generation from ground truth (`arlo/cards.py`, `arlo/build_corpus.py`), including
  **verb-aware harvesting** (`extract_dispatch_cards`, spec key `dispatchers`): a
  verb-dispatched script (`mainframe rail`, `mf status`, `git commit`) yields one card per
  verb, verbs read from the real bash `case` dispatch, a verb it does not have never carded.
  Surfaced by STEP-3 grading on mainframe — took eval-set coverage from ~8 to full. Generic
  over any dispatcher.
- Rung 0 retrieval (`arlo/translate.py`): select a card, return its command verbatim,
  say "no confident match" below a floor rather than guess.
- Rung 1 slot-fill (`arlo/binder.py`): bind a real template's hole from intent; the
  binder returns slot *values* only and `fill()` assembles from the real template, so
  the command skeleton cannot drift; a value carrying shell metacharacters is refused.
- Rungs 2-6, the structural grounding core (`arlo/ground.py`, ~120 lines): the small,
  model-agnostic seam the SKILL.md rung procedures call so what arlo emits stays ground
  truth. `select(candidates, id)` (rung 2) resolves a chosen id to its verbatim command and
  refuses a non-candidate. `cited_flags_grounded(narration, help)` (rung 3) requires every
  flag an explanation cites to be a whole token in the command's own harvested `--help`, so
  a renamed flag (`--parent` after it became `--parent-id`) is caught — the exact lie arlo
  prevents. `compose(cards, ids)` (rung 4) emits an ordered runbook of real cards and drops
  non-cards. `card_grounded(command, source)` (rung 5, reusing `binder.literals`) requires a
  proposed command's skeleton to appear verbatim in the source read. `unverified(command)`
  (rung 6) stamps the permanent UNVERIFIED label — `grounded=False`, no path to a grounded
  rung's confidence; per Q2 no danger/denylist. The *reasoning* of each rung lives in
  SKILL.md (§ "Rungs 2-6"), carried out by whatever model runs the skill.
- 28 hermetic tests across three files (`tests/test_{grounding,host_translate,ground}.py`),
  graded on real host ground truth (a script `Usage:` line and `ls --help`) and structural
  invariant checks, no model download. Full command in `CLAUDE.md`. **STEP 1 (the skill
  toolset) is complete through rung 6.**
