# Answering-agent prompt (STEP-3, one per target project)

Fill in `<PROJECT_PATH>` and `<INTENTS_JSON>` (the held-out intents with `expected_command`
stripped — only `id` + `intent`). Dispatch a **fresh** agent with this as its task; its
model is the LOM. Collect its `{id: command}` answers and pass them to `grade/grade.py`.

---

You are executing the **arlo** skill in a target project's context — this is a graded run of
the skill, so follow it faithfully and do not shortcut it.

**arlo** is a grounded NL→command operator. Its one sacred invariant: it never emits a
command that is not real ground truth harvested from the target system. It may surface the
wrong *real* command, but never an invented one. If no real command fits an intent, it
abstains (`"NO_MATCH"`).

- The arlo skill + code live at `/home/baron/projects/arlo` (read `SKILL.md`; the core is the
  `arlo/` package — run it with `PYTHONPATH=/home/baron/projects/arlo python3 -m arlo.<module>`).
- The target project is `<PROJECT_PATH>`. It is **READ-ONLY**: read its files and harvest
  ground truth, but NEVER run a command that mutates it or its infrastructure.

**Task — follow the arlo skill's procedure:**
1. Read `/home/baron/projects/arlo/SKILL.md` for arlo's method (harvest cards from ground
   truth; the trust-gradient rungs; the neutral core).
2. Harvest the project's real ground truth into cards using arlo's harvester
   (`python3 -m arlo.cards`) against a spec you build by discovering the project's real
   operational surface (dispatcher scripts, `mk-*`/helper scripts, `make` targets, a tool's
   own `--help` subcommands). The harvested cards are the ONLY commands you may return.
3. For EACH intent below, hand back what arlo should — grounded in the harvested cards.
   Some intents are a **single command**; some are **multi-step procedures** (e.g. "stand up
   a fresh soak from scratch" = build the fixture, then build the binary, then run it).
   - Single command: get real candidates (`arlo.translate.rank`), reason-rank to the best
     *real* card (your judgment as the LOM), fill any template slots from the intent's own
     words. Return the command string. If nothing fits, `"NO_MATCH"`.
   - Multi-step: resolve the procedure into an **ordered runbook** — a *list* of real cards
     in run order (rung 4, compose). This is your job as the LOM to sequence; arlo's only
     rule is that **every step is a real command** (a verbatim card skeleton, slots filled),
     never invented. Return the ordered list of command strings. If you cannot ground a
     required step, say so rather than invent it.
   Do NOT force a multi-step intent into one command, and do NOT pad a single-command intent
   into a runbook — answer at the shape the intent actually needs.

Return `{id: answer}` for every intent, where `answer` is a command string (single, or
`"NO_MATCH"`) OR an ordered list of command strings (multi-step). For each also give
`card_source`(s) proving ground truth and the `rung` used.

Intents:
<INTENTS_JSON>
