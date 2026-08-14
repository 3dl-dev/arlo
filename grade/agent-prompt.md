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
3. For EACH intent below, return the single command arlo should hand back — grounded in the
   harvested cards. Use the rungs: get real candidates (`arlo.translate.rank`), reason-rank to
   the best *real* card (your judgment as the LOM), and fill any template slots from the
   intent's own words. The command MUST be a real card's command (verbatim skeleton), slots
   filled — never invented. If no card genuinely fits, return `"NO_MATCH"`.

Return `{id: command}` for every intent (command = the real command with slots filled, or
`"NO_MATCH"`). For each also give `card_source` (the file/verb proving ground truth) and
`rung` used.

Intents:
<INTENTS_JSON>
