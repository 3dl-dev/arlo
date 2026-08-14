# Installing arlo

arlo is **a skill your agent uses**. You install it and use it from inside your agent —
you never drop to a shell, and you never run anything by hand. Add it *before* the
disaster, while the frontier is up, so it is ready when the lights go out.

## Claude Code

In your agent, add the marketplace and install the plugin:

```
/plugin marketplace add 3dl-dev/arlo
/plugin install arlo@arlo
```

That's it. From then on you just talk to your agent: ask it how to restart a service,
where the logs are, how to run a restore — and arlo answers with a **real** command from
your project's own ground truth (its scripts, Makefiles, and the `--help` of the tools
you actually run), labeled with how much it trusts the answer. If nothing matches, it
says so instead of inventing a command. The agent does all the work; you stay in the chat.

## Other agents (opencode, pi, hermes, …)

arlo is harness-agnostic by design — it is a plain-language skill plus a small standard
library core the agent runs for itself. Each agent has its own in-app way to add a skill
or plugin; use that. You never leave the agent to install or run anything. First-class
entries for these harnesses are tracked in the repo.

## Via hoist

If you drive deployments with hoist, hoist pulls arlo's distributable from the release
and installs it the same agent-first way. Release: https://github.com/3dl-dev/arlo/releases

## The model

arlo names no model. The one that runs the skill is your choice along a resource
gradient — your agent's own model, or a small local one, anything from a spare GPU down
to a bare CPU. The grounded core keeps whatever model you bring honest. Set it up while
the frontier is up, so arlo answers when it is down.
