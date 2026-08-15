---
name: start
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

## 1. Resolve the local operator model (LOM), in situ — do not assume a fixed one

arlo names **no** model, and pointing this step at one specific model in one specific
direction is an error out of the gate — the antithesis of arlo. The LOM is a resource
gradient you resolve *here, in place*, from what this operator actually has and what this
project actually needs. It may be:

- the very model now running this skill (you), ranking the real cards directly with no
  separate embedder at all — often the best fit, since you are already a capable model;
- a large local model or self-hosted endpoint the operator wired up;
- a small instruct/coder model, or a bare CPU sentence-embedder (`arlo/provision.sh
  [runtime_dir] [model_name]` is *one* way to stand up that last option — not the mandated
  one, not a default).

Assess and pick the best fit; provision it now, while the frontier is up, if it needs
provisioning. This is invariant #4 (resolve, don't hardcode) applied to the model tier
itself — putting a thumb on the scale toward any named model or fixed runtime is exactly the
mistake arlo exists to avoid. Whatever you resolve, the grounding core below keeps it honest.

## 2. Extract capability cards from ground truth

    python3 -m arlo.cards <spec.json> --root <checkout> --out cards.json

A card pairs a command with its ground-truth purpose and its source. `arlo.cards` is a
**deterministic first pass, not the finished corpus.** It parses the easy, regular cases: a
shell script's header comment (purpose) and `Usage:` line (command); a **verb-dispatched**
script (`mainframe rail`, `mf status`) into one card *per verb* from its real `case`
dispatch; a universal infra command (`docker compose restart`, `kubectl rollout restart`)
from its own `--help`. The spec keys are `scripts`, `dispatchers`, `makefiles`, `helpcards`.
But a deterministic parser is necessarily partial and can mis-parse, and **you are the LOM —
your job is to verify its draft against real source and complete the harvest by hand**,
staying grounded the whole way: only ever card a command that appears *verbatim as a real
invocation in real source*. `ground.card_grounded(command, source)` is your check for that.

**Verify every drafted card against its source — this is where the invariant is kept when
the parser slips.** A card whose command is not a real invocation in its cited source is a
fabrication and must be dropped, no matter how confident it looks. The concrete failure this
catches: a dispatcher whose program name the parser guessed from a *description word* (it
read `sync   sync ~/.claude to workshop` and emitted `sync inference`, `sync off`, `sync
logs` — but `sync` is coreutils, and `sync inference` is not a real operation; the real form
is `mainframe inference`). Synthesized `prog verb` cards where `prog` never appears as the
script's own `#!`/basename/`Usage:` invocation, verbs pulled from *nested* `case` blocks
rather than the top-level dispatch, and colliding ids across two dispatchers are all parser
artifacts — read the script's real top-level dispatch and header, keep the real verbs, drop
the phantoms. Emitting a `prog verb` that does not exist is the gravest failure class (the
`--parent`-lie, reproduced by the harvester); the invariant is absolute, so this verify pass
is not optional.

**Then complete the surface — a real command the parser drops is a real command the operator
won't get.** The parser structurally misses these; card them yourself from ground truth:

- **Makefiles: card *every* recipe-bearing target, not only the `##`-documented ones.** The
  parser keys on `##`; an undocumented `all:`/`clean:`/`test:` target is ground truth too
  (purpose falls back to the target name or its first recipe line). Projects routinely leave
  the headline op (`make test`, `make up`) undocumented — harvest them straight from the
  `Makefile`. Skip only build-system noise (`cmake_*`, `edit_cache`, `rebuild_cache`, …).
  When a target *wraps* a lower-level command, the target is the operator's canonical
  surface: return `make <target>`, not the wrapped command.
- **Infra `--help` whose shape the parser can't read — recover the verbs by hand.** The
  deterministic extractor only reads a cobra-style `Available Commands:`/`Commands:` section
  with `≥2` spaces before the description. Real tools break every one of those assumptions,
  and each break silently drops real verbs: a **nonzero exit** that still prints usage (`go`,
  or a frozen-verb string like `gpu: want submit|status|logs|…`); a **different section
  header** (`Basic Commands (Beginner):`, `The commands are:`, `Unit Commands:`);
  **colon-aligned padding** that leaves the *longest* verb only one space (so `az group
  create`, `az containerapp revision deactivate`, a cobra group's longest subcommand vanish
  while their shorter siblings card fine); and a **catch-all placeholder** synopsis (`kubectl
  [flags] [options]`, `go <command> [arguments]`) that is not a runnable command. Read the
  real `--help`/usage yourself and card each actual verb (`prog verb`); never card the
  placeholder.
- **Script synopses the parser truncates or collapses.** Join **backslash-continued** `Usage:`
  lines before reading them (else you card an env-var prefix with a dangling `\`, or refuse a
  genuinely-present multi-line command at rung 5). Card **each variant** a header lists
  (`./boot.sh`, `--clean`, `--rebuild`, `--slim` are four real commands, not one). Split a
  synopsis that shows **two example forms** (`api.sh GET … | api.sh POST …`) into separate
  cards. Recognize an **indented synopsis with no literal `Usage:` keyword** (`#   deploy.sh
  <user> <name>`) so the argument template survives for rung-1 slot-fill. Strip a trailing
  parenthetical **annotation** (`scripts/run-soak.sh [DURATION]   (default: 48h)`) off the
  command — real doc text, but not part of the invocation.
- **The parameterized recipes in the project's Markdown runbooks.** For many shops the real,
  runnable ground truth — the full `az containerapp update -g … -n … --image …`, `cmake -B
  build -D…`, a k3s recovery `kubectl delete secret … && systemctl restart k3s-agent` — lives
  only in `docs/`, not in any script header or `--help`. `arlo.cards` has no channel for
  Markdown, so read those code fences yourself and card the commands, each grounded to the
  doc line with `card_grounded`. Prefer a **live** script/`--help` over prose when both exist:
  a hand-written doc goes stale (a moved path, a renamed flag) — exactly the drift arlo
  exists to catch — so the harvested script wins the tie.
- **Scope `helpcards` to the tools this project actually drives ops through.** arlo cards
  whatever `--help` you name; naming a tool the project never invokes (a `docker compose
  --help` in a repo with no compose file) injects real-but-irrelevant cards that dominate
  ranking. Grep the runbooks first; card only the surfaces the project's ops actually use.
  For a **large multi-subgroup CLI** (`az`, `gcloud`, `kubectl`), do not helpcard its
  top-level `--help` at all: it lists subgroups you can't run bare (`az group` is a group,
  `az group create` is the command) and utility leaves you never touch (`az login`,
  `az feedback`), while hiding the ops verbs under a `Subgroups:` header the parser skips.
  Harvest the concrete `az <group> <verb>` invocations the runbooks actually use instead.
- **The preconditions that make any of this runnable — auth, config, env.** Do not assume the
  box you run on is the configured box where setup happened. A fresh clone or a cold machine
  has the *system* but not the operator's *access* to it: `az` unauthed, `kubectl` with no
  context, secrets unloaded, `.envrc` unallowed. The commands that restore that access —
  `az login`, `az acr login -n …`, `kubectl config use-context …`, `op signin`, `direnv
  allow`, `source .envrc`, `docker login …` — are operational ground truth too, and they live
  in the project's README/setup docs and CI env blocks. Those names are *illustrations, not a
  menu*: this project's restore surface may use none of them (a `source_env` in `.envrc`, an
  insecure registry with no login, a 1Password flow) — harvest the ones this project actually
  documents, and abstain on a precondition it does not, rather than parrot an example here.
  Access to a *running* system is often not in the project's own files at all: a project that
  runs on a platform it doesn't itself contain (a tenant of another system, deployed on a
  cluster a sibling repo stood up) keeps its reach-the-system path in *that platform's* docs —
  and the project's own docs point there (a `deploy/README` that says "runs on <host>'s k3s
  cluster — see <host>/docs/…"). Follow that pointer (next bullet) and harvest the real access
  path from it: reach the control-plane node over the host's own ssh surface, then `sudo k3s
  kubectl …`, or whatever the platform documents. Abstaining because the command is not in
  *this* repo, when the project itself points at the repo that has it, is a harvest that
  stopped one hop too early. Harvest them: in a lights-out moment,
  restoring a precondition is often the *first* real need and the prelude (rung 4) to every
  other op. The invariant still binds — arlo never invents a credential or a config value; it
  surfaces the real, grounded restore command and leaves the secret to the operator.
- **Reach past the repo tree — discover the project's operational dependencies and recurse
  into each one's ground truth.** A project is operated through more than its own files: the
  platform it lives on and the tools it habitually runs are part of its operational reality,
  and their command surface is ground truth even though it lives elsewhere. **Find these from
  the project's own evidence — do not wait to be handed them** (being told "this project uses
  `rd`" is a thumb on the scale; the skill's job is to make you *notice* it):
  - **Declared dependency.** The project's docs name where it runs or what it needs: "runs on
    <platform> — see <platform>/docs/…", a host/cluster/bastion, a sibling repo. Follow the
    reference; it is this project's ground truth by the project's own declaration.
  - **Ambient dependency, discovered from footprint.** A tool the project drives ops through
    but *never declares*, because it is shared infra. Read the footprint: the dotdirs it
    carries, the config and state files it accumulates, and the commands its scripts habitually
    invoke. **The ones that matter are the ones you do NOT already recognize — an unfamiliar
    `.<something>/` dir or config is a dependency signal, not noise; do not skip it because you
    can't place it, and do not lean on a name you happen to already know (that is the frontier
    model's crutch — at a real site the shared tool is one you have never seen).** Resolve an
    unknown artifact to its tool *from evidence, not recall*:
    - **Read the artifact itself.** Its contents usually say what it *is*, even when they never
      name the command: a schema, a service kind, endpoints, a `project`/`board`/`id` field
      (e.g. a `.<x>/config.json` carrying nostr event kinds and a "board" coordinate is a
      nostr-native board tool; a state file's keys name its model). That fixes *what* you're
      dealing with.
    - **Resolve the binary separately** — the dir name and the CLI often differ (a `.ready/`
      board is driven by `rd`, not `ready`), so do not assume `.<name>/` ⇒ `<name>`. Probe PATH
      (`which <name>`, `<name> --help`), and if that misses, find *what writes these files*:
      grep the project's scripts/CI for the artifact path (a fixture or soak script that names
      the real command), or the tool's own repo if it is present on the box. This last mile is
      the fragile hop: the state files reliably say *what* the tool is, but often nothing
      in-tree spells the CLI. When you can name what it is but not the runnable binary, you have
      found a real dependency you cannot yet ground — that `.<x>/ → <binary>` mapping is a prime
      thing to **capture** at setup while it is known (record it into the project's arlo config,
      per the recurse/capture choice below), so cold use never has to re-derive it. Until it is
      captured or a writer names it, abstain — do not guess the binary.
    - **Then harvest its surface** (`<tool> --help`, one card per verb per §2), which lives in
      the tool or the tool's own repo/skill, **not** in this project.
    If you cannot resolve a footprint artifact to a grounded command surface, say so and abstain
    on its ops — never guess a verb for a tool you only half-identified. A whole class of "only
    the frontier model knew how" ops (grant a teammate onto a shared board, reseal it) is
    exactly this: real verbs of a shared tool that no consuming repo documents.
  Whichever way a dependency surfaces, its referenced source is as real as a `Usage:` line and
  grounded the same way (`card_grounded` against the tool's help/doc). Resolve it by **either
  strategy, the operator's call, both supported**; name neither as the default:
  - **Recurse.** Re-harvest from the dependency (the platform, or the tool's own repo/`--help`)
    at the moment of use — always current, but the dependency must be reachable then (a cold
    clone of *this* repo alone may not carry the sibling repo; a tool may be absent from PATH).
    This is the "regenerate, don't store" side.
  - **Capture.** At setup, while the frontier is up and the dependency is reachable, harvest its
    ground truth once and record it into *this* project's own arlo corpus / restore snapshot —
    self-contained at lights-out even if the dependency is absent, but a dated projection that
    can rot, so stamp it with its source and date (the `LIGHTS-OUT.md` discipline) and
    re-harvest when the dependency is reachable again. A capture is only sufficient if a cold
    operator needs *nothing else* — so it must persist, not just the bare command+purpose:
    (a) the `.<dir>/ → <binary>` mapping (the fragile hop, so cold use never re-derives it);
    (b) each command's **arg template and flags** (or rung-1 slot-fill has no hole to bind);
    (c) for a multi-party/multi-host op, the per-step **actor/where and human handoffs** — the
    same attribution rung 4 presents at answer-time, *persisted* here, or the cold runbook reads
    as a single-operator script; (d) the **raw grounding source** (the `--help`/doc text) so
    the cold operator can re-verify `card_grounded` offline without the tool present; and
    (e) an honest **coverage/confidence self-assessment** — which of this project's real needs
    (§2b) arlo covers versus abstains on, the trust rung each covered answer earned, the known
    gaps (surfaces not harvested, a dependency identified but whose binary would not resolve, a
    hidden/undocumented op), and the staleness date. This is arlo telling the operator *how far
    to trust it on this project, before the lights are out* — and it is the honest form of an
    assessment: a per-project self-report the setup LOM writes and **regenerates** each setup
    (anti-rot: the skill ships the instruction to produce it, never a frozen score), NOT a
    shipped grader, loss, or benchmark number (that apparatus arlo does not build). Capturing
    only command+purpose+source is the under-capture that leaves cold onboarding incomplete —
    and capturing no self-assessment leaves the operator unable to tell a covered need from a
    gap until they hit it at 3am.
  Which to use is the operator's decision, resolved from their situation (is the dependency
  present at lights-out? is its surface stable enough to snapshot?) — the same
  regenerate-vs-dated-snapshot tradeoff arlo already makes for cards. Either way, do not stop
  at the directory boundary; setup is when this linkage is cheap to capture and impossible to
  reconstruct cold, so capture or wire it then.

## 2b. Calibrate the setup to the project — climb only as far as its ops need

Projects differ in operational complexity, and arlo's setup should match the project rather
than impose a fixed shape. A project whose ops are single commands (vms: `boot`, build,
`ctest`) bottoms out **shallow** — a small card corpus and rung 0–1 is the whole job. A
project where nearly everything is N-step (mainframe, EAF: stand up the control plane and
confirm health, recover a component, restore access then deploy) needs the **full climb**:
deeper harvest (prose runbooks, precondition/prelude steps), a more capable resolved LOM
(§1), and rung-2/4 reasoning and composition.

Do not guess the depth — **measure it in situ, and self-calibrate.** Pose the project's own
real needs to yourself, answer them from the harvested corpus + resolved LOM, and check each
answer against ground truth (a real script/`--help`/runbook — the same grounding you card
from). Where you fall short — a need with no card, a wrong-real pick, a multi-step op whose
atoms are missing — climb: harvest deeper, resolve a stronger LOM, add composition, then
re-pose the needs. Setup is done when the LOM reliably serves *this* project's real needs,
grounded, not when a fixed checklist is ticked. This is the LOM tuning its own setup in
situ, using the project's own ground truth as the check — **not** a shipped grader, a
held-out benchmark, or a scored loop. Those are apparatus arlo does not build; the
calibration is you, reasoning against real ground truth, climbing until the project is served.

## 3. Translate intent into a grounded command

Retrieval is **yours to do as the resolved LOM (§1), over the real cards, returning a card's
command verbatim.** `python3 -m arlo.translate cards.json "reset a password"` will run a
hybrid similarity+lexical ranker for you — but treat it as an *accelerant, not the answer
path*: it requires a provisioned embedder (it `ModuleNotFoundError`s if none is installed —
so it is not the command to reach for the moment you have no model), and its shipped
model-free `bag_of_words` floor mis-ranks badly (it cannot index short tokens like `up`,
collides 5-char prefixes like `production`/`products`, and lets generic ops words — `status`,
`logs`, `job` — clear the floor with a wrong card). When you are the LOM (you always are at
skill-run time), rank the real cards directly: weigh the intent against each card's purpose
*and* whether its command signature actually performs the operation named, and emit the
chosen command verbatim with the runners-up.

**Abstain on judgment, not on a cosine number.** A high blind score from shared words is not
a match. If the top card's command does not actually do what the intent asks — or if you know
the surface it asks about was not fully harvested (§2) — say "no confident match" and, when a
real source exists, climb to rung 5 (propose from that source) rather than hand back a *wrong
real* command wearing unearned confidence. Surfacing a plausible-but-wrong real command as
though it were the answer is the failure the harvest and abstention gaps combine to produce;
it is safe only because you label it — do not skip the label.

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
verify the order.** When the sequence spans multiple actors or machines (an owner mints an
invite, the joiner redeems it on *their own* box, the owner then grants), the who/where for
each step is ground truth in the verb's own `--help` prose — a card carries only the bare
verb, so harvest the actor/where and present it per step (`[owner] rd invite …` / `[joiner]
rd join …` / `[owner] rd grant …`). The bare ordered verbs alone do not say that a human
handoff and a second machine sit between them; emitting them without that attribution reads
as a single-operator script and misleads. A real runbook sequence usually includes prose prelude and verify steps —
auth/env setup (`op signin`, `direnv allow`), post-checks (`go vet`, a `verifylive` smoke) —
that live in the docs, not in any script header, and a `compose` will only emit the scripted
middle if those atoms were never harvested. When the composed sequence looks thin, the fix is
upstream: harvest the prelude/verify steps from the runbook (§2) so the composition is the
*real* sequence. If an atom the sequence needs cannot be grounded, drop it and say so rather
than paper the gap with an invented step.

### Rung 5 — propose  *(summarizes real source — review required)*
When no card fits, read real source (a `--help`, a runbook, a script) and draft a card.
Call `ground.card_grounded(command, source)`: the proposed command's skeleton must appear
verbatim in the source you read, or it is refused. A proposal is always a **review-required
draft**, never auto-adopted into the corpus. Label it two ways: grounded-to-the-source, and
not-yet-ground-truth-pending-review. Two source cautions ground-source testing surfaced:
before the substring check, **join backslash-continued lines *and* collapse internal
whitespace runs** — a fence commonly writes `nostr-relay-prod \` with a space *before* the
backslash, so a bare join leaves a double space (`prod  --image`) that the exact-substring
check still misses; without the whitespace-collapse a genuinely-present multi-line command (a
wrapped `az containerapp update …` or `cmake -B build -D…`) is falsely refused. And prefer a **live**
script/`--help` over a prose doc when both describe the command — a hand-written runbook can
be stale (a moved `Dockerfile` path, a renamed flag), and `card_grounded` will happily bless
the stale form because it only checks the source you handed it. Grounded-to-a-stale-doc is the
`--parent` failure re-entering at rung 5; the live source breaks the tie.

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
