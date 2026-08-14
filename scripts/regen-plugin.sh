#!/usr/bin/env bash
# Regenerate the self-contained Claude Code plugin from the repo-root source of truth.
# Claude Code may install just plugins/arlo/, so SKILL.md + the stdlib core are bundled
# (not symlinked out of the plugin). Run after editing SKILL.md or the arlo/ core.
set -euo pipefail
cd "$(dirname "$0")/.."          # repo root
dst=plugins/arlo/skills/arlo
rm -rf "$dst"; mkdir -p "$dst/arlo"
cp SKILL.md "$dst/SKILL.md"
cp arlo/*.py "$dst/arlo/"
echo "regenerated $dst from root (SKILL.md + $(ls arlo/*.py | wc -l) core modules)"
