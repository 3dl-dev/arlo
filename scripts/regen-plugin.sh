#!/usr/bin/env bash
# Regenerate the self-contained Claude Code plugin from the repo-root source of truth.
# The plugin skill is named `start` so the getting-started command is `/arlo:start`.
# Claude Code may install just plugins/arlo/, so SKILL.md + the stdlib core are bundled
# (not symlinked out). Run after editing SKILL.md or the arlo/ core.
set -euo pipefail
cd "$(dirname "$0")/.."          # repo root
dst=plugins/arlo/skills/start
rm -rf "$dst"; mkdir -p "$dst/arlo"
# carry the operator skill, renamed to the getting-started verb
sed 's/^name: arlo$/name: start/' SKILL.md > "$dst/SKILL.md"
cp arlo/*.py "$dst/arlo/"
echo "regenerated $dst (name: start) from root (SKILL.md + $(ls arlo/*.py | wc -l) core modules)"
