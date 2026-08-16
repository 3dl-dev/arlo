# arlo

**A Real, Local Operator. Lights-out ops.**

When your coding agent is down or rate-limited and the app breaks at 3am, you type your
own words and arlo hands back the exact command to run — grounded in your system's own
ground truth. It runs on an independent local path and **never invents a command** that
isn't real.

## arlo is a skill

The product is a skill your agent invokes — [`SKILL.md`](SKILL.md) — not a command line.
You install it, set it up once while the frontier is up, then just talk to your agent:

```
/plugin marketplace add 3dl-dev/arlo
/plugin install arlo@arlo
/arlo:start          # arlo learns this project's real commands
```

Then ask ("how do I restart the deriver?") and arlo answers with a real command, or says
"no confident match" rather than invent one. Lights-out, at a shell: `arlo <your words>`.
Full install: [`docs/INSTALL.md`](docs/INSTALL.md).

## Under the skill

The `arlo/` package is a **small neutral core the skill calls** — a subordinate library,
not the product. It exists to hold arlo's one invariant *by construction* (a command it
returns is always real ground truth); see [`arlo/README.md`](arlo/README.md) for the rule
on what earns code here versus what stays skill prose. Standard library only.

- Design, trust gradient, lineage: [`docs/design.md`](docs/design.md)
- Decisions made and still open: [`docs/decisions.md`](docs/decisions.md)
- How to think while building arlo (read the **altitude invariant** first): [`CLAUDE.md`](CLAUDE.md)

## Grading arlo

arlo is graded by **running the skill**, not by running its code: an agent executes
`SKILL.md` in a project it hasn't seen and you read what it does. There is deliberately no
grader, harness, or eval loop (that apparatus was deleted — we ship a skill, not code). What
a real session reveals is distilled into a generalized, project-agnostic expectation in
[`cases/`](cases/), the growing record of what the skill must do. The hermetic checks in
`tests/` grade only the core's mechanics (the structural guarantees); a green test suite is
not a graded product.

## License

LGPL-2.1-or-later. Full text in [`COPYING`](COPYING). You may add arlo to any project,
proprietary included, and link it freely; changes to arlo itself stay open. Copyright
(C) 2026 the arlo authors.
