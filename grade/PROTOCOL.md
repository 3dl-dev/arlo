# STEP 3 — grading arlo (the agent-driven loss)

**This is the loss that judges arlo.** Not `tests/` (those are hermetic core-mechanics
checks), and there is no `eval/loss.py` — that graded arlo's shipped functions and was
deleted for being the wrong altitude. arlo's product is what an **agent** produces when it
runs `SKILL.md` in a project it has never seen, with the agent's own model as the LOM. So
the loss is measured by *running the skill*, not by calling arlo's code.

## The loop

For each target project:

1. **Author a held-out set** (once per project), if none exists in `grade/held_out/<project>.jsonl`.
   Read the project's real ground truth (its scripts, `case` dispatchers, `--help`, `make`
   targets) and write ~10–15 rows of operator-phrased intents paired with the **real** command
   they map to — plus a few intents the project has *no* command for (abstention). Row shape:
   `{"id": "...", "intent": "operator words", "expected_command": "the real command",
   "expected_key": "the grounded substring that must appear", "card_expected": true|false}`.
   Every `expected_command` must trace to real ground truth — you are writing the answer key,
   so verify it against the source. Abstention rows use `"expected_command": null,
   "card_expected": false`. Keep this file local (it is gitignored: project-specific, never
   ships with arlo).

2. **Dispatch an agent to run the skill in the project's context.** Spawn a *fresh* agent
   (its model is the LOM) and have it FOLLOW `SKILL.md` in the target project — READ-ONLY:
   discover the ground-truth surface, harvest cards, and for each intent return the single
   real command arlo should hand back (slots filled from the intent's own words), or
   `"NO_MATCH"` if it cannot ground one. It must never invent a command, and never run a
   mutating command against the project. It returns `{id: command}` for every intent. (Give
   it the intents WITHOUT the expected commands.) See `grade/agent-prompt.md` for the exact
   prompt.

3. **Grade its answers** against the held-out set:

       python3 grade/grade.py grade/held_out/<project>.jsonl <answers.json>

   Retrieval = right real command; abstention = correctly declined. Every miss is a gradient:
   it names where the skill, *run in context*, fell short — and the fix is upstream in
   `SKILL.md` (how the agent should reason/harvest) or, only when a guarantee must hold by
   construction, in the neutral core. It is almost never "grade the code here."

## What a good result looks like

The grounding core keeps every emitted command a real one (invariant holds); a capable LOM
closes the retrieval gap. On mainframe this scored retrieval 28/28, abstention 6/6. A low
score is a real gradient into the skill; a hermetic core test going green is not the same
thing and never will be.
