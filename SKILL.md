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
(`arlo/provision.sh` stands up that last option — not a default). Pick the best fit and
provision it while the frontier is up. Pinning one model is the thumb-on-the-scale arlo exists
to avoid (invariant #4, resolve don't hardcode). The grounding core keeps whatever you bring honest.

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
against real ground truth, **not** a shipped grader or scored loop.

## 3. Translate intent → a grounded command

Retrieval is **yours as the LOM**, over the real cards, returning a card's command verbatim.
`python3 -m arlo.translate cards.json "…"` runs a hybrid ranker but is an *accelerant, not the
path*: it needs a provisioned embedder (else `ModuleNotFoundError`) and its model-free floor
mis-ranks (can't index short tokens like `up`, collides prefixes, lets generic words clear on
a wrong card). You always are the LOM at skill-run time — rank the cards directly on purpose
*and* whether the command signature performs the operation, emit verbatim with runners-up.

**Abstain on judgment, not a cosine number.** If the top card doesn't actually do what's
asked, or you know the surface wasn't fully harvested, say "no confident match" and climb to
rung 5 rather than hand back a *wrong real* command with unearned confidence. Label it — the
wrong-real is safe only because it's labeled.

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
  - **Give exactly what the goal needs — one command if one suffices** (a target whose recipe
    already does start-and-health is the whole answer); never pad to look multi-step.
  - Mark a precondition that may already hold **[conditional]** (auth/env — `op signin`, `direnv
    allow`); the operator skips it if done.
  - Include prose **prelude/verify** steps as grounded atoms; for a **multi-party/multi-host**
    op, present per-step **actor/where + handoffs** (`[owner, here] <mint-invite>` / `[joiner,
    their box] <redeem+report>` / `[owner, here] <grant>`) — bare verbs read as a single-operator
    script.
  - **Flag an honest gap, never fill it** — a step the goal needs but the reference never
    documents (a `kubeconfig`/`get-credentials` the docs assume) is surfaced as a gap in an
    otherwise-grounded runbook, not invented.
  - **Abstain on the whole goal** if no grounded process exists (a rollback with no documented
    procedure) rather than fabricate a plausible one.
  Show steps discretely, label less-trusted — verify the order.
- **Rung 5 — propose** *(review-required)*: draft a card and call `ground.card_grounded(command,
  source)` — the skeleton must appear verbatim (it joins backslash-continued lines and collapses
  whitespace first). Label grounded-to-source, not-yet-ground-truth. Prefer a **live**
  script/`--help` over prose; a stale doc grounds True but is the `--parent` lie re-entering.
- **Rung 6 — generate** *(UNVERIFIED)*: only when 0–5 are empty; `ground.unverified(command)`
  stamps `grounded=False`, no path to a grounded confidence. No denylist (safety is the
  operator's). No model → unavailable; abstain.

## Adding arlo to any project

arlo needs only the standard library. Point its spec at your project's real ground truth; the
*model* is whatever runs the skill (resolve it per §1). arlo names nothing about your
environment — if the system runs elsewhere, inject a reach (`build_corpus.environment_runner`)
and it harvests from there. An arlo that lies is worse than none: it *selects and fills*,
never *writes* the command shape. That is the line that keeps every rung honest.
