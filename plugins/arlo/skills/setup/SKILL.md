---
name: setup
description: "Alias for /arlo:start — set arlo up for this project (harvest ground truth, resolve the model tier, wire the `arlo` command). Follow the start skill."
---

# arlo:setup — alias of /arlo:start

`setup` and `start` are the same lifecycle action: first-time setup of arlo for this
project, run while the frontier is up. Follow **/arlo:start** — its bundled `SKILL.md` is
the procedure (resolve the model tier, harvest this project's ground truth into
`.arlo/cards.json`, write the lights-out fallback, and put `arlo` on the PATH).

After setup, keep arlo current with **/arlo:update**, and uninstall with **/arlo:remove**.
