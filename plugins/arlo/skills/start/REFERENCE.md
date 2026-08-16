---
name: arlo
description: "Lights-out ops. A real, local operator: when the frontier model is down and credits are out, you type your own words and arlo hands back the exact command to run, grounded in your system's own ground truth. It never invents a command."
---

# arlo, a real, local operator

arlo hands you the real command to run when the frontier model is down or rate-limited. You
type your own words ("bounce the deriver", "reset a password"); arlo answers from your
system's own ground truth, on an independent local path.

**The invariant, narrow and sacred: arlo never invents a command that is not real ground
truth.** At worst it surfaces the *wrong real* command — always with its confidence and the
alternatives, so you can tell — never one that does not exist. (The failure it prevents: a
flag table said `--parent` for months after the real flag became `--parent-id`; everyone who
trusted it made orphans. arlo answers from the live surface.)

## The trust gradient

Every answer is **labeled with the trust it earned**. Climb only as far as the answer needs:

- **rung 0, retrieve**: return a card's command verbatim. Full grounding.
- **rung 1, slot-fill**: bind a real template's hole from your words (`bounce the deriver` →
  `docker compose restart deriver`); skeleton verbatim, only the slot inferred and shown.
- **rung 2, reason-rank**: when scores can't separate real cards, pick *which real card* and
  say why; return an id, never a command. Full grounding.
- **rung 3, explain**: narrate the chosen command from its *own* `--help`, never memory; every
  cited flag must be a real token in that help. Grounded.
- **rung 4, compose**: chain real cards into an ordered runbook; atoms real, order inferred →
  **less-trusted**. Return ids; show steps discretely.
- **rung 5, propose**: no card fits → read real source and draft a card whose skeleton appears
  verbatim in it. **Review-required draft** — grounded to source, not yet ground truth.
- **rung 6, generate**: only when 0–5 are empty; free generation, **UNVERIFIED**, never a
  grounded rung's confidence. No model → rung 6 unavailable; abstain.

## 1. Resolve the LOM in situ — never a fixed model

arlo names no model. The LOM is a gradient you resolve here from what this operator has and
this project needs: often the model now running this skill (ranking cards directly, no
embedder); or a local model/endpoint; or a small instruct model or CPU embedder
(`arlo/provision.sh` stands up that last option — not a default). Pinning one model is the
thumb-on-the-scale arlo exists to avoid (invariant #4, resolve don't hardcode). The grounding
core keeps whatever you bring honest.

**Resolve a ladder, not a point, and record it for runtime escalation.** "Frontier down" is
rarely binary — the *primary* API being gone doesn't mean *every* capable model is. So at
setup, while the lights are on, resolve and record an ordered escalation ladder into
`.arlo/config.json`: the cheap default (a small local model or the offline lexical floor), then
what to climb to when it isn't enough — a bigger local model on the operator's hardware, an
alternate API from a different provider, a self-hosted endpoint. At use, run the default; when a
goal is hard (a novel multi-step inference the captured flows don't cover, or a low-confidence
answer), **escalate up the recorded ladder** rather than guess or abstain, if a rung is
reachable. The operator's budget decides how far to climb; the ladder just makes the climb
possible without re-deciding it in the dark.

## 2. Harvest capability cards from ground truth

    python3 -m arlo.cards <spec.json> --root <checkout> --out cards.json

A card pairs a command with its ground-truth purpose and source. `arlo.cards` is a
**deterministic first pass, not the finished corpus** — it parses the regular cases (a script
header's `Usage:`; a verb-dispatched script's `case` → one card per verb; an infra command's
`--help`; spec keys `scripts`, `dispatchers`, `makefiles`, `helpcards`). It is partial and can
mis-parse, so **you, the LOM, verify its draft against real source and complete the harvest by
hand**, only ever carding a command that appears *verbatim as a real invocation in real
source* (`ground.card_grounded` is your check).

**Verify — this is where the invariant holds when the parser slips.** Drop any card whose
command is not a real invocation in its source, however confident. Parser artifacts to catch:
a program name guessed from a description word (reading `sync  sync ~/.claude to workshop` and
emitting `sync inference`, not a real op — the real form is `mainframe inference`), verbs from
*nested* `case` blocks, colliding ids across dispatchers. Read the real top-level dispatch +
header, keep real verbs, drop phantoms. A `prog verb` that doesn't exist is the gravest
failure — the verify pass is not optional.

**Complete — a real command the parser drops is one the operator won't get:**

- **Makefiles:** card *every* recipe-bearing target, not just `##`-documented ones (purpose =
  target name or first recipe line); the headline op (`make test`, `make up`) is often
  undocumented. Skip build-system noise (`cmake_*`, `edit_cache`, …). A target that *wraps* a
  command is the canonical surface — return `make <target>`.
- **Infra `--help` the parser can't read** (it only reads a cobra `Available Commands:`/
  `Commands:` section with ≥2 spaces): recover verbs by hand when the tool breaks that — a
  nonzero exit that still prints usage (`go`, `gpu: want submit|status|…`), a different header
  (`Subgroups:`, `The commands are:`, `Unit Commands:`), colon-aligned padding that drops the
  *longest* verb (`az group create`, `az containerapp revision deactivate`), or a catch-all
  placeholder (`kubectl [flags]`, `go <command>`). Card each real verb, never the placeholder.
- **Script synopses the parser truncates:** join **backslash-continued** `Usage:` lines; card
  **each variant** a header lists (`./boot.sh`, `--clean`, `--rebuild` are separate commands);
  split `|`-separated example forms; recognize an indented synopsis with no `Usage:` keyword
  (so the rung-1 arg template survives); strip a trailing annotation (`…  (default: 48h)`).
- **Markdown runbook recipes:** the full parameterized command (`az … -g … --image …`, `cmake
  -B build -D…`, a k3s `kubectl … && systemctl …`) often lives only in `docs/`, which
  `arlo.cards` can't read — card it from the fence, grounded with `card_grounded`. Prefer a
  **live** script/`--help` over prose when both exist; a doc goes stale (moved path, renamed
  flag) and would card the drift arlo exists to catch.
- **Scope `helpcards`** to tools the project actually drives ops through (grep the runbooks) —
  a `docker compose --help` in a repo with no compose file injects noise. For a large
  multi-subgroup CLI (`az`, `gcloud`, `kubectl`) don't helpcard the top-level `--help` at all
  (it lists un-runnable subgroups and hides ops verbs under `Subgroups:`) — harvest the
  concrete `az <group> <verb>` lines the runbooks use.
- **Preconditions — auth/config/env.** A fresh clone or cold box has the *system* but not your
  *access*: `az` unauthed, `kubectl` context-less, secrets unloaded. Harvest the real restore
  commands the project documents (`az login`, `kubectl config use-context …`, `op signin`,
  `direnv allow`, `source .envrc` — illustrations, not a menu; a project may use none of them,
  so abstain on a precondition it doesn't document rather than parrot one). Restoring a
  precondition is often the *first* need and the rung-4 prelude. arlo never invents a
  credential — surface the restore command, leave the secret to the operator.

**Reach past the repo tree — discover the project's dependencies and recurse into each one's
ground truth.** A project is operated through more than its own files. Find its dependencies
from its *own evidence*, don't wait to be told (being handed "this project uses `<tool-X>`" is a
thumb on the scale — the skill's job is to make you notice it):

- **Declared:** its docs name where it runs ("runs on <platform> — see <platform>/docs/…", a
  host/cluster, a sibling repo) — follow the reference; it is ground truth by the project's
  own declaration.
- **Ambient, from footprint:** a tool it drives ops through but never declares. Read the
  footprint — dotdirs, config/state files, the commands its scripts invoke. **The ones that
  matter are the ones you don't recognize; don't lean on a name you happen to know (at a real
  site the shared tool is one you've never seen).** Resolve by evidence: (1) read the artifact
  — its contents say *what* it is even without naming the CLI (a `.<x>/config.json` naming a
  service kind, a schema, or a resource id fixes what you're dealing with); (2) resolve the
  binary *separately* — the dir name and the CLI often differ (a `.<name>/` dir may be driven
  by a differently-named binary), so do not assume `.<name>/ ⇒ <name>`; probe PATH and,
  failing that, grep for what *writes* the files (a fixture/CI script that names the command)
  or the tool's own repo; (3) harvest its surface (`<tool> --help`, one card per verb). The
  dir→binary hop is fragile: the state files say what the tool is but rarely spell the CLI. If
  you can't resolve it to a grounded surface, **abstain** — never guess a verb. (This is the
  "only the frontier model knew how" class: real verbs of a shared tool no consuming repo
  documents — grant a teammate access to a shared resource, rotate its key.)

Reach a dependency by **either strategy, the operator's call, neither default:**

- **Recurse:** re-harvest from the dependency at use time — current, but it must be reachable
  then (a cold clone of *this* repo may not carry the sibling repo; a tool may be off PATH).
- **Capture:** at setup, harvest it once into this project's `.arlo/` snapshot — self-contained
  even if the dependency is later absent, but a dated projection that can rot (stamp source +
  date, the `LIGHTS-OUT.md` discipline; re-harvest when reachable). A capture is sufficient
  only if a cold operator needs *nothing else*, so persist: (a) the `.<dir>/ → <binary>`
  mapping; (b) each command's **arg template + flags**; (c) for a multi-party/multi-host op,
  the per-step **actor/where + human handoffs** (the rung-4 attribution, persisted not just
  presented, or the cold runbook reads as a single-operator script); (d) the **raw grounding
  source** for offline `card_grounded` re-verification; and (e) an honest **coverage/confidence
  self-assessment** — which needs arlo covers vs abstains on, the rung each earned, the known
  gaps, and the staleness date. (e) is the honest form of an assessment — a per-project
  self-report regenerated each setup, never a shipped grader/loss/score.

Either way, don't stop at the directory boundary; setup is when this linkage is cheap to
capture and impossible to reconstruct cold.

## 2b. Calibrate depth to the project

Match setup to the project, don't impose a shape. Single-command projects bottom out shallow
(small corpus, rung 0–1); N-step projects (stand up a control plane, recover a component,
restore-then-deploy) need the full climb (prose runbooks, prelude steps, a stronger LOM,
rung-2/4). **Measure it in situ:** pose the project's own needs, answer them, check each
against ground truth; where you fall short (no card, wrong-real pick, missing atoms), climb
and re-pose. Done when the LOM reliably serves this project's needs — the LOM tuning itself
against real ground truth, **not** a shipped grader or scored loop. **Enumerate the operator's
real flows here** — the small, knowable set they'll actually need (deploy, restart-and-confirm,
recover, onboard, rotate) — and for any that are multi-step, infer + ground + capture each as a
distilled runbook now (rung 4), while the lights are on. The state space is small enough that
capturing it at setup covers the common case; the rare uncaptured goal is inferred live at use.

## 3. Translate intent → a grounded command

Retrieval is **yours as the LOM**, over the real cards, returning a card's command verbatim.
`python3 -m arlo.translate cards.json "…"` runs a hybrid ranker but is an *accelerant, not the
path*: it needs a provisioned embedder (else `ModuleNotFoundError`) and its model-free floor
mis-ranks (can't index short tokens like `up`, collides prefixes, lets generic words clear on
a wrong card). You always are the LOM at skill-run time — rank the cards directly on purpose
*and* whether the command signature performs the operation, emit verbatim with runners-up.
Rank over **both** kinds of corpus artifact: harvested single-command cards *and* the
**distilled runbooks** setup captured for the operator's real flows (§2b / rung 4). A
high-level goal that matches a distilled runbook returns that whole grounded process —
re-verified against live source — so the operator (or a weaker offline LOM) gets the flow back
without re-inferring; a goal no captured flow covers is inferred live and escalated (§1);
a distilled runbook whose atoms no longer ground has rotted — re-infer and re-distill.

**Abstain on judgment, not a cosine number.** If the top card doesn't actually do what's
asked, or you know the surface wasn't fully harvested, say "no confident match" and climb to
rung 5 rather than hand back a *wrong real* command with unearned confidence. Label it — the
wrong-real is safe only because it's labeled.

**Show the trap you avoided — don't just quietly route around it.** When an *obvious* command
the operator (or a naive NL→shell model) would reach for is **not ground truth** — a plausible
`kubectl set env …` that isn't in the real surface, a flag that doesn't exist, a hot-swap the
system doesn't support — surface it explicitly as a **refused alternative** in the answer, not
just in your own head: show the tempting command, marked `✕ not in your ground truth
(card_grounded=False)`, with the one-line operational reason if you know it (it drifts from the
provisioner, it bounces the pod), *then* give the grounded answer. This is the invariant made
visible: arlo doesn't silently hand you the right command, it shows you the tempting wrong one
it refused, so you learn the trap instead of hitting it. The refused command is only ever shown
**labeled not-ground-truth**, never emitted as the answer — that is exactly why showing it is
safe. Surface at most the one or two an operator would actually try; don't invent traps to
look clever.

**A fault intent seeks restoration — don't lead with a destructive rebuild.** When the
operator reports a *symptom* ("X is hung / down / wedged / not responding") they want X
**restored**, not rebuilt. But the nearest command by name is often a *destructive* one — a
rebuild / reprovision / recreate whose own text carries X's name, so a literal-weighted rank
floats it to the top. Handing that back is the worst wrong-real: it doesn't miss, it destroys.
Match on the end-state wanted (X running again), not the token that names X — prefer the repair
(restart / recover), compose it from real primitives if no single card is it (rung 4), and if a
rebuild really is the nearest real command, surface it **labeled from its own harvested purpose
as "rebuild / DESTRUCTIVE — not a repair,"** demoted, never at a restore's confidence — or
abstain if neither repair nor its primitives exist. (Not a danger oracle — Q2 stands; the
"destructive" signal is read from the command's own ground-truth text, not you judging safety.)

## 4. Slot-fill a real template (rung 1)

    python3 -m arlo.binder card.json "bounce the deriver"

Binds a template's hole from your words, returning slot *values* only; `fill()` assembles from
the real template so the skeleton can't drift; unbound slots show as blanks. A deterministic
binder ships so the mechanism runs model-free (it mis-binds values, labeled — the LOM binds
better).

## Rungs 2–6: you reason, `ground.py` keeps you honest

You are the model running this skill; `ground.py` is the seam that keeps what you hand back
ground truth. Climb only as far as needed; label every answer with its rung.

- **Rung 2 — reason-rank** *(full grounding)*: pick which real card fits and why; return the
  id and call `ground.select(candidates, id)` (a non-candidate id is refused).
- **Rung 3 — explain** *(full grounding)*: narrate from the command's own `--help`, never
  memory; `ground.cited_flags_grounded(narration, help)` requires every cited flag to be a
  whole token in the help (`--parent` is not satisfied by `--parent-id`).
- **Rung 4 — compose / infer a grounded multi-step process** *(less-trusted)*: a high-level
  goal ("start the app", "recover the worker", "get a cold box able to operate the cluster")
  rarely maps to one card — infer the ordered process. Two sources, same grounding: chain
  pre-harvested cards (`ground.compose(cards, ids)`, which drops non-cards), and/or **infer the
  steps from the project's reference data** — the sequence a runbook or README documents —
  grounding EACH emitted step with `ground.card_grounded(command, source)` and dropping any that
  will not ground. Rules that keep this honest (each proven in real use):
  - **Ground against the source that *governs the outcome*, not merely one where the command
    appears — this is the dominant inference failure, read it twice.** `card_grounded=True`
    proves a string is real ground truth; it does NOT prove that string is what *decides* the
    goal at runtime. When a goal names an outcome (the model gets served, login is refused, spend
    is attributed), follow to the source that actually *reads or enforces* it — the code path,
    the running service's config, the live mount — and ground there. A docstring claiming an
    effect and the code producing it can disagree: trust the code that decides (`MODIFY /FLAGS=
    DISUSER` grounds True in help text, but if the authenticator never reads flags it is a silent
    no-op). "Live" is not the test — **effective** is: a live script not wired into the running
    service is as stale as a moved-path doc. And when the effective source is populated from
    another file (a repo config copied to a served location), the **propagation is a required
    step** — trace where the served source is written from; don't edit the copy that never
    reaches it. When the deciding source **forks** on an env var or parameter
    (`KEY=${SUPPLIED:-<mint>}`), trace *both* branches — a supplied-value override is often the
    working path, not the default. When the goal names a **live** target, test your path against
    its *current* state: if the effective source shows the happy path fails now, find the path
    that works today — never emit "re-provision the platform" to make your own path valid. And
    the code-is-authority rule cuts both ways: if the help is **silent** on a form but you traced
    it through the code and confirmed it effective, **emit it** — over-abstaining on a real
    code-grounded command fails the operator as surely as inventing one.
  - **Give exactly what the goal needs — one command if one suffices** (a target whose recipe
    already does start-and-health is the whole answer); never pad to look multi-step.
  - **Completeness scan before emitting:** (1) *what makes this fail in practice?* — capacity/
    resource ceilings, quotas, mutual-exclusion (a VRAM ceiling, one-at-a-time) are preconditions
    as real as auth and are usually stated away from the runbook; (2) *does the last step reach
    the goal's end-state, or just the happy-path spine?* — a printed "Next steps" echo is a
    pointer, not the process; scan for the tail.
  - Mark a precondition that may already hold **[conditional]** (auth/env — `op signin`, `direnv
    allow`); the operator skips it if done.
  - Include prose **prelude/verify** steps as grounded atoms; for a **multi-party/multi-host**
    op, present per-step **actor/where + handoffs** (`[owner, here] <mint-invite>` / `[joiner,
    their box] <redeem+report>` / `[owner, here] <grant>`) — bare verbs read as a single-operator
    script.
  - **Flag an honest gap, never fill it** — a step the goal needs but the reference never
    documents (a `kubeconfig`/`get-credentials` the docs assume) is surfaced as a gap in an
    otherwise-grounded runbook, not invented. **But synthesize before you flag:** a gap is honest
    only after you read the sources that would close it. Before calling a value "undocumented" or
    a goal "blocked", check (a) the sources you already cited or *discarded* — dropping one as
    superseded/heritage needs evidence it isn't the effective source, not a portfolio-wide prior
    (the IDs were in the doc that was dismissed); and (b) whether two options you read as mutually
    exclusive actually combine. Over-flagging a phantom gap fails the goal as surely as inventing.
    **Never claim a check you did not run** — a gap justified by a fabricated absence-check (a grep
    you didn't run, a source you didn't open) is the invariant broken on the honesty side; actually
    read the named sources and report the real result.
  - **Abstain on the whole goal** if no grounded process exists (a rollback with no documented
    procedure) rather than fabricate a plausible one.
  Show steps discretely, label less-trusted — verify the order.
  - **Capture the flows at setup, don't distill open-endedly through use.** The flows an operator
    actually needs on a project are a *small, enumerable set* — deploy, restart-and-confirm,
    recover, onboard, rotate a key. So the place to spend a rung-4 inference is **setup**, over
    that known flow list, not every use: at setup, enumerate the operator's real flows (§2b) and
    infer + ground each once, persisting it into `.arlo/` as a **distilled runbook** — the goal in
    the operator's words, the ordered steps each with source `file:line` + grounding, the
    `[conditional]` preconditions, the flagged gaps, and the **effective-source reasoning** that
    decided it — stamped with the date and the source SHAs/mtimes it grounded against, labeled
    rung-4-inferred (composition less-trusted, atoms grounded). At use, the operator *retrieves*
    the captured flow (§3 ranks over distilled runbooks as well as cards); a **rare goal the
    captured flows don't cover is inferred live**, and escalated up the LOM ladder (§1) if the
    default model can't. This bounds the work (a finite flow list at setup + a small live tail)
    instead of growing a corpus through open-ended use. A distilled runbook is **not frozen
    truth**: it is a dated snapshot re-verified against live source on use — each atom
    re-groundable, the effective-source claim re-checkable — same anti-rot discipline as any card;
    if the source moved, re-infer and re-capture.
- **Rung 5 — propose** *(review-required)*: draft a card and call `ground.card_grounded(command,
  source)` — the skeleton must appear verbatim (it joins backslash-continued lines and collapses
  whitespace first). Label grounded-to-source, not-yet-ground-truth. Prefer the **effective**
  source — the one whose output actually reaches the goal state — over any source that merely
  names the command, prose or live; a stale-or-non-effective source grounds True but is the
  `--parent` lie re-entering.
- **Rung 6 — generate** *(UNVERIFIED)*: only when 0–5 are empty; `ground.unverified(command)`
  stamps `grounded=False`, no path to a grounded confidence. No denylist (safety is the
  operator's). No model → unavailable; abstain.

## The lifecycle (how this skill is operated)

This document is the reference. arlo is *operated* through lifecycle skills, each a focused
procedure standing on it:

- **`/arlo:start`** (aliased **`/arlo:setup`**) — first-time setup: resolve the LOM ladder
  (§1), harvest this project's ground truth into cards (§2), write the lights-out fallback,
  put `arlo` on the PATH. Once, while the frontier is up.
- **`/arlo:update`** — re-read *this project* against the arlo you have: re-harvest from live
  ground truth (cards are a regenerated projection, never stored truth) and report what
  drifted. Periodically, and whenever the project's commands change — a stale card set is the
  `--parent`→`--parent-id` rot arlo exists to prevent, turned on arlo.
- **`/arlo:upgrade`** — move *arlo itself* forward: pull the latest arlo from upstream (new
  rungs, sharper harvest rules, fixes), then reconcile each project via `update`. Distinct
  axes, like `apt update` (re-index the project) vs `apt upgrade` (newer arlo).
- **`/arlo:remove`** — clean teardown: unwire `arlo` and delete the project's `.arlo/`
  projection, leaving the project's own ground truth untouched.

## Adding arlo to any project

arlo needs only the standard library. Point its spec at your project's real ground truth; the
*model* is whatever runs the skill (resolve it per §1). arlo names nothing about your
environment — if the system runs elsewhere, inject a reach (`build_corpus.environment_runner`)
and it harvests from there. An arlo that lies is worse than none: it *selects and fills*,
never *writes* the command shape. That is the line that keeps every rung honest.
