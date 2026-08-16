#!/usr/bin/env bash
# Regenerate the self-contained Claude Code plugin from the repo-root sources of truth.
#
# arlo ships a LIFECYCLE of skills, invoked as /arlo:<name>:
#   start   — first-time setup (harvest ground truth, resolve model tier, wire `arlo`)
#   setup   — alias of start
#   update  — re-harvest THIS project's live ground truth + report drift (uses installed arlo)
#   upgrade — pull the latest arlo from upstream, then reconcile via update
#   remove  — clean teardown
#
# Each skill body is authored under skills/<name>/SKILL.md (the source of truth). Skills that
# RUN the core (start, update) bundle a copy of it, plus REFERENCE.md — the full arlo document
# (repo-root SKILL.md) they cite for the trust gradient and the complete harvest rules. start
# also bundles the provisioner and the `arlo` launcher it wires onto the PATH. Claude Code may
# install just plugins/arlo/, so everything a skill needs is bundled beside it, never symlinked.
#
# Run after editing any skills/<name>/SKILL.md, the repo-root SKILL.md, or the arlo/ core.
set -euo pipefail
cd "$(dirname "$0")/.."                       # repo root

plug=plugins/arlo
skills_dst="$plug/skills"
reference=SKILL.md                            # the canonical arlo document

# Skills that bundle the core + REFERENCE.md (they harvest / run the core).
needs_core="start update"

rm -rf "$skills_dst"

for name in start setup update upgrade remove; do
  src="skills/$name/SKILL.md"
  [ -f "$src" ] || { echo "missing source: $src" >&2; exit 1; }
  dst="$skills_dst/$name"
  mkdir -p "$dst"
  cp "$src" "$dst/SKILL.md"
  # Sanity: the frontmatter name must equal the skill dir (invocation is /arlo:<dir>).
  grep -q "^name: $name\$" "$dst/SKILL.md" || {
    echo "frontmatter name in $src is not 'name: $name'" >&2; exit 1; }
  if [[ " $needs_core " == *" $name "* ]]; then
    mkdir -p "$dst/arlo"
    cp arlo/*.py "$dst/arlo/"
    cp "$reference" "$dst/REFERENCE.md"       # the canonical arlo document, bundled for citation
  fi
done

# start is the one that provisions the model and wires the launcher onto the PATH.
cp provision.sh "$skills_dst/start/provision.sh"
mkdir -p "$skills_dst/start/bin"
cp bin/arlo "$skills_dst/start/bin/arlo"

echo "regenerated $skills_dst:"
for name in start setup update upgrade remove; do
  extra=""
  [[ " $needs_core " == *" $name "* ]] && extra=" + core($(ls arlo/*.py | wc -l | tr -d ' ')) + REFERENCE.md"
  [ "$name" = start ] && extra="$extra + provision.sh + bin/arlo"
  echo "  /arlo:$name$extra"
done
