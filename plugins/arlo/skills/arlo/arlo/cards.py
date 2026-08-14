#!/usr/bin/env python3
"""arlo capability cards: structured ground truth for the grounded answerer.

A raw corpus of harvested lines is a list of commands. A card is the unit that
makes arlo answer intent instead: it pairs the operator-facing purpose (plain
words, harvested from the tool's own header or doc) with the exact command to run
and where it came from. The answerer matches intent against purpose, then hands
back the command verbatim. arlo never writes a command; it only points at one.

Cards are generated from ground truth, never authored (the arlo invariant):
  - shell scripts: the leading comment block is the purpose, a `Usage:` line is
    the command.
  - verb-dispatched scripts (`mainframe rail`, `mf status`): one card PER verb, the
    verbs read from the script's real bash `case` dispatch, the invocation name from
    its header. A verb the script does not dispatch is never carded.
  - Makefile targets: a `##` comment block above a target is the purpose,
    `make <target>` is the command.

Standard library only. Extraction is deterministic parsing of the real files.
"""

import argparse
import json
import os
import re
import sys


def _rel(path):
    return path


# A dispatch verb branch in a bash `case`: `rail)` or `opencode|oc)`, indented, the
# pattern before `)`. Excludes the default `*)` and help branches.
_CASE_RE = re.compile(r"^\s*([a-z][\w-]*(?:\|[a-z][\w-]*)*)\)")
_SKIP_VERBS = {"-h", "--help", "help", "*"}


def _dispatch_verbs(lines):
    """The verb tokens of a bash `case` dispatch, in source order, deduped. For an
    alternated branch (`opencode|oc)`) the first alternative is the canonical verb."""
    verbs, seen = [], set()
    in_case = False
    for l in lines:
        s = l.strip()
        if s.startswith("case ") and " in" in s:
            in_case = True
            continue
        if s == "esac":
            in_case = False
            continue
        m = _CASE_RE.match(l)
        if m:
            verb = m.group(1).split("|")[0]
            if verb not in _SKIP_VERBS and verb not in seen:
                seen.add(verb)
                verbs.append(verb)
    return verbs


def _dispatch_prog(header, verbs):
    """The real invocation name of a dispatcher, from its own header: a `<prog> <verb>`
    line (e.g. `mainframe status`) where <verb> is a real case verb names <prog>. Falls
    back to None so the caller can use the file's basename."""
    vset = set(verbs)
    counts = {}
    for h in header:
        toks = h.replace("usage:", "").replace("Usage:", "").split()
        if len(toks) >= 2 and toks[1] in vset and re.fullmatch(r"[\w.-]+", toks[0]):
            counts[toks[0]] = counts.get(toks[0], 0) + 1
    return max(counts, key=counts.get) if counts else None


def _verb_purpose(header, verb):
    """A verb's purpose from the header's mode list: a line like
    `rail       — both GPUs → k3s-worker` or `rail: do the thing`. Ground truth from
    the tool's own doc; empty if the header does not describe the verb."""
    pat = re.compile(r"^" + re.escape(verb) + r"\b\s*[—:–-]*\s*(.+)$")
    for h in header:
        m = pat.match(h.strip())
        if m and m.group(1).strip():
            return m.group(1).strip()
    return ""


def extract_script_card(path):
    """One card from a shell script's header block. Handles a `Usage:` whose synopsis is
    on the following line(s) (`# Usage:` then `#   ./boot.sh ...`) as well as inline
    (`# Usage: foo <bar>`). Never returns a card with an empty command — a script whose
    header yields no usable invocation is not carded rather than carded as a blank."""
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    i = 1 if lines and lines[0].startswith("#!") else 0
    header = []
    while i < len(lines):
        l = lines[i]
        if l.startswith("#"):
            header.append(l.lstrip("#").strip())
            i += 1
        elif l.strip() == "":
            break  # a blank line ends the header block (headers are contiguous comments)
        else:
            break
    if not any(header):
        return None
    u_idx = next((i for i, h in enumerate(header) if h.lower().startswith("usage:")), None)
    command = None
    if u_idx is not None:
        after = header[u_idx].split(":", 1)[1].strip()
        if after:
            command = after
        else:  # synopsis is on the following indented line(s); take the first, sans comment
            for h in header[u_idx + 1:]:
                if h.strip():
                    command = h.split("#", 1)[0].strip() or None
                    break
        purpose = " ".join(header[:u_idx]).strip()
    else:
        command = _rel(path)   # no Usage line: the script itself is the command
        purpose = " ".join(header).strip()
    name = os.path.basename(path)
    if not command or not command.strip():
        return None
    return {
        "id": os.path.splitext(name)[0],
        "purpose": purpose or name,
        "command": command,
        "source": _rel(path),
    }


def extract_dispatch_cards(path):
    """One card PER VERB of a verb-dispatched script (`mainframe rail`, `mf status`).
    The verbs come from the script's real bash `case` dispatch — the source of truth for
    what verbs exist — so a verb that is not a real branch is never carded. The
    invocation name comes from the script's own header (`mainframe status` -> prog
    `mainframe`), falling back to the basename; each verb's purpose comes from the
    header's mode list when it documents the verb. The command is `prog verb`, both
    halves ground truth. Returns [] if the file has no dispatch."""
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    # leading comment region (the header): all comment lines before the first line of
    # code; blank lines inside it are skipped, not treated as the end.
    header, i = [], (1 if lines and lines[0].startswith("#!") else 0)
    while i < len(lines):
        l = lines[i]
        if l.startswith("#"):
            header.append(l.lstrip("#").strip())
        elif l.strip() == "":
            pass
        else:
            break
        i += 1
    verbs = _dispatch_verbs(lines)
    if not verbs:
        return []
    base = os.path.splitext(os.path.basename(path))[0]
    prog = _dispatch_prog(header, verbs) or os.path.basename(path)
    cards = []
    for v in verbs:
        cards.append({
            "id": f"{base}-{v}",
            "purpose": _verb_purpose(header, v) or f"{prog} {v}",
            "command": f"{prog} {v}",
            "source": f"{_rel(path)}:{v})",
        })
    return cards


def _host_run(cmd, timeout):
    import subprocess
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except Exception as e:  # noqa: BLE001
        return 127, f"(could not run: {e})"


# a command synopsis that is only a placeholder for "some subcommand" — carding it as a
# template would let arlo emit an ungrounded subcommand (rd frobnicate), so it is refused.
_CATCHALL_RE = re.compile(
    r"^\S+\s+[\[<]?(commands?|cmd|subcommands?|args?|options?|flags?)[\]>]?[.\s]*$",
    re.IGNORECASE)
# a "subcommands" section header in --help output (cobra/click/git/kubectl style)
_CMDSEC_RE = re.compile(r"^(available commands|commands|subcommands):\s*$", re.IGNORECASE)
_SUBCMD_RE = re.compile(r"^\s+([a-z][\w-]+)\s{2,}(\S.*)$")


def extract_help_cards(cmd, timeout=30, run=None):
    """Cards harvested from a tool's own --help (ground truth for an infra command no
    project script wraps). Returns a LIST:

      - if the help lists subcommands (an `Available Commands:` / `Commands:` section),
        ONE card PER subcommand (`prog verb`), so each is real ground truth — the same
        verb-awareness the bash-`case` harvester gives, for --help-listed CLIs;
      - otherwise a single card from the synopsis, UNLESS the synopsis is a catch-all
        placeholder (`prog [command]`), which is refused: carding it would let arlo emit
        an ungrounded subcommand. Better no card than a template that invents commands.

    run is the command runner, (cmd, timeout) -> (rc, text), default host."""
    run = run or _host_run
    rc, out = run(cmd, timeout)
    if rc != 0:            # the command is absent -> no fabricated card
        return []
    lines = [l.rstrip() for l in out.splitlines()]
    prog = cmd.split(" --help")[0].split(" -h")[0].strip()

    # 1) a real subcommand section -> one card per verb
    for i, l in enumerate(lines):
        if _CMDSEC_RE.match(l.strip()):
            subs = []
            for sl in lines[i + 1:]:
                if not sl.strip():
                    if subs:
                        break        # blank line ends the section
                    continue
                m = _SUBCMD_RE.match(sl)
                if m and m.group(1).lower() not in ("help", "completion"):
                    subs.append({
                        "id": f"{prog.replace(' ', '-')}-{m.group(1)}",
                        "purpose": m.group(2).strip(),
                        "command": f"{prog} {m.group(1)}",
                        "source": cmd,
                    })
                elif not sl.startswith((" ", "\t")):
                    break            # a dedented line ends the section
            if subs:
                return subs

    # 2) no section -> a single synopsis card, unless it is a catch-all placeholder
    desc = next((l.strip() for l in lines
                 if l.strip() and not l.strip().lower().startswith("usage:")), "")
    usage_idx = next((i for i, l in enumerate(lines)
                      if l.strip().lower().startswith("usage:")), None)
    command = ""
    if usage_idx is not None:
        after = lines[usage_idx].split(":", 1)[1].strip()
        if after:
            command = after
        else:
            for l in lines[usage_idx + 1:]:
                if l.strip():
                    command = l.strip()
                    break
    if not command:
        command = cmd.replace(" --help", "")
    if _CATCHALL_RE.match(command):   # 'rd [command]' -> refuse, don't invent
        return []
    return [{
        "id": cmd.replace(" --help", "").replace(" ", "-"),
        "purpose": desc or cmd,
        "command": command,
        "source": cmd,
    }]


def extract_makefile_cards(path):
    """One card per documented Makefile target (a `##` block above `target:`)."""
    cards = []
    doc = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f.read().splitlines():
            if line.startswith("##"):
                doc.append(line.lstrip("#").strip())
            elif line and line[0].isalnum() and ":" in line.split()[0]:
                target = line.split(":", 1)[0].strip()
                if doc and target and target != ".PHONY":
                    cards.append({
                        "id": f"make-{target}",
                        "purpose": " ".join(d for d in doc if d).strip(),
                        "command": f"make {target}",
                        "source": f"{_rel(path)}:{target}",
                    })
                doc = []
            elif not line.strip():
                continue
            else:
                doc = []
    return cards


def build_cards(spec, root=".", run=None):
    """spec: {scripts: [paths], makefiles: [paths], helpcards: [cmds]} relative to
    root. run is the command runner for helpcards, (cmd, timeout) -> (rc, text),
    default host. Pass an environment runner to harvest helpcards from inside
    wherever the system runs; script/makefile cards read files under root."""
    cards = []
    for rel in spec.get("scripts", []):
        p = os.path.join(root, rel)
        if os.path.isfile(p):
            c = extract_script_card(p)
            if c:
                if c["command"] == p:      # no Usage: line; show the relative path
                    c["command"] = rel
                c["source"] = rel
                cards.append(c)
    for rel in spec.get("makefiles", []):
        p = os.path.join(root, rel)
        if os.path.isfile(p):
            for c in extract_makefile_cards(p):
                c["source"] = c["source"].replace(p, rel)
                cards.append(c)
    for rel in spec.get("dispatchers", []):
        p = os.path.join(root, rel)
        if os.path.isfile(p):
            for c in extract_dispatch_cards(p):
                c["source"] = c["source"].replace(p, rel)
                cards.append(c)
    for cmd in spec.get("helpcards", []):
        cards.extend(extract_help_cards(cmd, run=run))
    # defense in depth: never surface a card with no command (a fabricated blank).
    return [c for c in cards if c.get("command") and c["command"].strip()]


def main(argv=None):
    ap = argparse.ArgumentParser(description="extract arlo capability cards from ground truth")
    ap.add_argument("spec", help="JSON: {scripts:[...], makefiles:[...]}")
    ap.add_argument("--root", default=".", help="base dir the spec paths are relative to")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    with open(args.spec) as f:
        spec = json.load(f)
    cards = build_cards(spec, args.root)
    with open(args.out, "w") as f:
        json.dump(cards, f, indent=2)
    print(f"extracted {len(cards)} cards -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
