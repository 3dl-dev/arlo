# cases/ — the behavioral case library (what the skill must generalize to)

A real in-situ session is the only honest signal for whether arlo works. This directory
is where each session's lesson is **kept** — so coverage grows past "6/6", and a later
session does not re-learn the same failure from scratch.

It is **not** a grader, a harness, or an eval loop. That apparatus was deliberately deleted
(`grade/`, commit `888842b`) and the principle enshrined: *we distribute a skill, not code;
we never build an apparatus to grade, harness, or orchestrate it.* A case here is not run by
a `.py`. It is replayed the way arlo is always graded — an agent follows `SKILL.md` in a
project and you read what it does.

## What a case is (and is not)

A case is **one generalized behavioral expectation**, distilled from a single real session
into a project-agnostic rule the skill must satisfy in *any* project.

Two hard rules keep this library honest — both learned the hard way in this repo:

1. **No real-project ground truth. No target-specific commands.** A case never contains a
   command — no real host, VM control, or project script name. Such a command belongs to the
   *instance* arlo builds for that project (a step-3 output), never to arlo itself. A case names the *class* of intent and the *general* rule; if it needs an
   example, it uses a placeholder (`svc-X`, `the cache`), never a real system.

2. **Generalize; do not accumulate datapoints.** One session reveals a *class* of failure.
   Capture the class as one rule. You are a large model — the abstraction is what you are
   good at; the library holds abstractions, not a corpus of reproductions. If two sessions
   teach the same class, they sharpen one case; they do not add a second.

The test of a good case: it reads as true for a project neither you nor the session ever saw.

## Anatomy of a case file

Each `*.md` is one case:

- **Intent class** — the shape of what the operator typed (not the literal words).
- **The naive failure** — what a floor / name-match answer does wrong, and why.
- **The general rule** — the abstraction the skill must embody. Project-agnostic.
- **Where it lives in the skill** — the `SKILL.md` section this rule drove.
- **Replay** — how an agent checks the skill honors the rule against *its own* project's
  real ground truth (a procedure, not a checked-in fixture).

## Adding a case

A real session missed (or nearly missed). Ask: *what class of failure was that, stated so
it is true everywhere?* Write that as one case, sharpen the `SKILL.md` section it points to,
and confirm the rule is now what the skill says. If you cannot state it without naming a
real system, you have not finished generalizing.

## Replaying the library

There is nothing to run. Pick a project, have an agent follow `SKILL.md` against its real
ground truth, and for each case check the agent's answer honors the rule. A miss is a signal
to sharpen the skill — never to weaken the case.
