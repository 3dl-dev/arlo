#!/usr/bin/env python3
"""arlo STEP-3 grader — scores what an AGENT produced by running the skill.

Read this before you touch it: this file deliberately does **not** import arlo. It
grades the *product* — the answers an agent hands back after running `SKILL.md` in a
target project — not arlo's shipped functions. If you find yourself adding
`from arlo import ...` here to "grade retrieval," stop: that is the build-it-here mode
failure (see CLAUDE.md, the altitude invariant). The whole point of STEP 3 is that the
skill is executed by an agent in a project's context, with the agent's model as the LOM,
and this only compares its answers to a held-out set. No model, no arlo code, no floor.

Two kinds of held-out row:
  - single command:  {id, intent, expected_command, expected_key, card_expected}
                     — answer is a command string ("NO_MATCH" = abstained). Rungs 0-2.
  - multi-step:      {id, intent, expected_steps: [{command, key}, ...], multi: true}
                     — answer is an ORDERED LIST of real commands (a runbook the agent
                       composed, rung 4). Scored order-aware: each expected step's key
                       must appear, in order, somewhere in the agent's list.

Answers file: json {id: "command"}  OR  {id: ["step", "step", ...]} for multi-step.

Usage:
    python3 grade/grade.py <held_out.jsonl> <answers.json>
"""

import json
import sys


def load_held_out(path):
    return [json.loads(l) for l in open(path).read().splitlines() if l.strip()]


def _hit(cmd, key, expected_command=None):
    cmd = (cmd or "").strip()
    return bool(cmd) and cmd != "NO_MATCH" and (cmd == expected_command or (key and key in cmd))


def _as_list(a):
    if isinstance(a, list):
        return [str(x) for x in a]
    if a and a != "NO_MATCH":
        return [str(a)]
    return []


def grade(held_out, answers):
    s_t = s_ok = a_t = a_ok = m_t = m_full = 0
    fails, m_partial = [], []
    m_steps_ok = m_steps_tot = 0
    for r in held_out:
        a = answers.get(r["id"])
        if r.get("expected_steps"):            # --- multi-step (rung 4) ---
            m_t += 1
            steps = r["expected_steps"]
            got = _as_list(a)
            pos = matched = 0
            for st in steps:
                key = st.get("key") or st.get("command")
                for j in range(pos, len(got)):
                    if _hit(got[j], key, st.get("command")):
                        pos, matched = j + 1, matched + 1
                        break
            m_steps_ok += matched
            m_steps_tot += len(steps)
            if matched == len(steps):
                m_full += 1
            else:
                m_partial.append((r["id"], r["intent"], matched, len(steps), got))
        elif r.get("card_expected"):           # --- single command (rungs 0-2) ---
            s_t += 1
            key = r.get("expected_key") or r.get("expected_command") or ""
            got = _as_list(a)
            if any(_hit(c, key, r.get("expected_command")) for c in got):
                s_ok += 1
            else:
                fails.append((r["id"], r["intent"], (got or ["(none)"])[0], r.get("expected_command")))
        else:                                   # --- abstention ---
            a_t += 1
            if a == "NO_MATCH":
                a_ok += 1
            else:
                fails.append((r["id"], r["intent"], _as_list(a) or "(none)", "ABSTAIN"))
    return dict(s_t=s_t, s_ok=s_ok, a_t=a_t, a_ok=a_ok, m_t=m_t, m_full=m_full,
               m_steps_ok=m_steps_ok, m_steps_tot=m_steps_tot, fails=fails, m_partial=m_partial)


def main(argv=None):
    argv = argv or sys.argv[1:]
    if len(argv) != 2:
        print("usage: python3 grade/grade.py <held_out.jsonl> <answers.json>")
        return 2
    g = grade(load_held_out(argv[0]), json.load(open(argv[1])))

    print(f"=== STEP-3 grade: {argv[0]}  (agent output, real LOM) ===")
    if g["s_t"]:
        print(f"single-command (rungs 0-2):  {g['s_ok']}/{g['s_t']}")
    if g["m_t"]:
        print(f"multi-step runbooks (rung 4): {g['m_full']}/{g['m_t']} fully correct"
              f"   ({g['m_steps_ok']}/{g['m_steps_tot']} steps grounded & in order)")
    if g["a_t"]:
        print(f"abstention:                  {g['a_ok']}/{g['a_t']}")
    if g["fails"] or g["m_partial"]:
        print("\nmisses (gradients — where the skill, run in context, fell short):")
        for i, intent, got, want in g["fails"]:
            print(f"  {i}: '{intent}'  -> {got}   (want {want})")
        for i, intent, matched, total, got in g["m_partial"]:
            print(f"  {i}: '{intent}'  -> multi-step {matched}/{total} steps in order; got {got}")
    else:
        print("\nclean: single commands right, runbooks complete and ordered, abstentions correct.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
