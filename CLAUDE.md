# CLAUDE.md, arlo (project standing orders)

arlo is **A Real, Local Operator**: the no-frontier operational fallback. When the
frontier model is down and credits are out, the operator types their own words and
arlo hands back the exact command to run, grounded in the system's own ground truth.
Lights-out ops. The product is a **skill an agent invokes** (`SKILL.md`), agent-first;
the Python is the neutral core the skill calls, never a user-facing command line.

Read [`docs/decisions.md`](docs/decisions.md) before touching anything: it holds what
was decided and what is still open. The design is [`docs/design.md`](docs/design.md).

## The one invariant, sacred and narrow

**arlo never invents a command that is not real ground truth.** The worst it may do is
surface the wrong *real* command, and it always shows its confidence and the
alternatives so the operator can tell. It may never hand back a command that does not
exist. The concrete failure this prevents: a hand-maintained flag table said `--parent`
for months after the real flag became `--parent-id`, and everyone who trusted it
created orphans. arlo answers from the live command surface instead.

This is the line that separates arlo from a fine-tuned NL→shell generator (which
invents commands, some destructive). arlo is not that. If a change would let arlo emit
a command shape that is not ground truth, it violates the invariant, stop.

## How to think while building here

1. **The trust gradient, not "lookup only".** The local model (the LOM) does the
   hardest thing it can *while still pointing at ground truth*, and every answer is
   **labeled with the trust it earned**. rung 0 return-a-card-verbatim and rung 1
   slot-fill keep the invariant fully; higher rungs (compose, propose, generate) are
   labeled progressively less trusted. Never present a less-grounded answer with a
   more-grounded answer's confidence. Do not collapse the gradient back to lookup, and
   do not skip a rung's label to make an answer look stronger.

2. **Keep the invariant structural, not trust-based.** Where a mechanism can enforce
   the invariant by construction, make it. Rung 1's binder returns slot *values* only;
   `fill()` assembles the command from the real template, so no binder, deterministic
   or a large model, can alter the skeleton. Prefer that shape over "the model is asked
   nicely not to".

3. **Ground-source testing.** A capability is not done until a test grades it against
   real ground truth (a real script, a real `--help`, a real command surface), not a
   mock of the thing under test. The deterministic embedder and binder are genuine,
   model-free implementations used to prove mechanics hermetically, they are not mocks;
   the *quality* of a live LOM is a separate grade that needs a provisioned model, and
   is labeled as the boundary until then. A skipped or absent test is a failing test.

4. **Resolve, don't hardcode.** arlo names nothing about the target's environment. It
   reads the target's real ground truth (scripts, Makefiles, the `--help` of the infra
   commands actually in use) and, when the system runs somewhere other than the host,
   takes an injected runner to reach it. No fixed backend, no closed menu of supported
   tools. A checked-in card spec is a cache of already-harvested ground truth, never a
   menu of what is possible.

5. **Honest, always.** State what is built-and-tested versus designed, out loud. A
   weaker-but-honest result beats a stronger-sounding claim. Surface cost (a model
   pull, a runtime) rather than hiding it. Label a rung with the guarantee it earned.

6. **Independence.** arlo depends on nothing but the standard library and a small local
   model (behind a lazy import), and nothing of any particular harness, model vendor,
   or build tool. It must run when the frontier and the network to it are down; that is
   the whole point.

## Working here

- Run the tests: `python3 tests/test_grounding.py && python3 tests/test_host_translate.py`
  (both are hermetic, no model download).
- The product surface is `SKILL.md`. Nobody runs the Python at a shell as the product;
  an agent invokes the skill. Running the `.py` is how you *grade the core*, legitimate,
  but it is not the product.
