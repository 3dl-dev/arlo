#!/usr/bin/env python3
"""arlo: the structural grounding primitives for rungs 2-6.

arlo is a skill. The *reasoning* of each rung — reason-rank, disambiguate, explain,
compose, propose, generate — is prose in SKILL.md, carried out by whatever model runs
the skill (the harness oracle, or a standalone local model the operator wires up in
their own context). This module is the small, model-agnostic seam those procedures call
to stay honest: each function takes the model's OUTPUT (a chosen id, an ordered list of
ids, a drafted command, a narration) and enforces that what arlo emits is ground truth.

Because these enforce the invariant by construction, no model — however capable or
however broken — can route around them: the command bytes arlo hands back come from
ground truth here, not from the model's tokens. That is the whole reason this is code
and not more prose. Everything the model actually *decides* stays in the skill, so the
skill improves with the model and this core does not need to change.

Standard library only. rung 1's structural core (fill / skeleton_intact) lives in
binder.py, the design center and the reference for how a driver plugs a model in.
"""

import re

from .binder import literals  # rung-1 helper: the literal (non-slot) segments of a command


# ---- rung 2: reason-rank / disambiguate -------------------------------------------
# The model chooses among the REAL candidates translate.rank surfaced and returns an
# id. select() turns that id into the card's command, verbatim; an id that is not a
# candidate is refused, so the model can only ever re-order real cards.

class NotACandidate(ValueError):
    """A chosen id is not among the real candidates — refused, never coerced."""


def select(candidates, card_id):
    """Resolve a chosen id to its candidate's VERBATIM command. `candidates` is a list
    of dicts with at least {id, command}. Raises NotACandidate if card_id is not one of
    them — the one place a rung-2 command is produced, and it only ever comes from a
    real card."""
    for c in candidates:
        if c["id"] == card_id:
            return c
    raise NotACandidate(card_id)


# ---- rung 4: compose --------------------------------------------------------------
# The model plans a short sequence and returns an ordered list of card ids. compose()
# emits each card's command verbatim, in order; an id that is not a real card is dropped
# and reported, never turned into a command. Steps are discrete (not joined into one
# `a && b` line) so each stays independently verifiable — composition is inferred, so
# the caller labels the runbook less-trusted.

def compose(cards, step_ids):
    """Resolve an ordered list of ids to an ordered runbook of VERBATIM commands.
    Returns (steps, dropped): steps is the real cards in order; dropped is the ids that
    are not real cards (reported, never emitted). A non-list `step_ids` composes to
    nothing rather than to garbage."""
    if not isinstance(step_ids, list):
        return [], []
    by_id = {c["id"]: c for c in cards}
    steps, dropped = [], []
    for cid in step_ids:
        c = by_id.get(cid)
        (steps.append(c) if c is not None else dropped.append(cid))
    return steps, dropped


# ---- rung 3: explain --------------------------------------------------------------
# The model narrates what a real command does — but from the command's OWN harvested
# --help, never memory. Any option token it cites must be a WHOLE token in that help,
# so a renamed flag (--parent after it became --parent-id) is caught, not waved through.
# rung 3 emits prose, not a command, so this is a floor on the explanation's honesty.

_OPT_RE = re.compile(r"(?<![\w-])(--?[A-Za-z][\w-]*)")


def option_tokens(text):
    """The set of whole option tokens in text: {'--parent-id', '-h', ...}. Whole-token,
    so '--parent-id' never collapses to '--parent'."""
    return set(_OPT_RE.findall(text or ""))


def cited_flags_grounded(narration, help_text):
    """Every option token the narration cites must appear in the command's harvested
    help. Returns (grounded, offenders) — offenders are cited flags absent from ground
    truth. Catches a hallucinated or stale flag independently of who wrote the prose."""
    offenders = sorted(option_tokens(narration) - option_tokens(help_text))
    return (not offenders, offenders)


# ---- rung 5: propose --------------------------------------------------------------
# The model reads real source and drafts a card. This is the first command the model
# ASSEMBLES rather than copies, so it must be grounded to the source it read — every
# literal (non-slot) segment of the proposed command must appear in that source — and it
# is always a review-required draft, never auto-adopted into the corpus.

def card_grounded(command, source_text):
    """Every literal (non-slot) segment of a proposed command must appear in the source
    the model read; slot placeholders may be inferred. Reuses binder.literals so
    'grounded' at rung 5 means exactly what 'skeleton' means at rung 1. Returns
    (grounded, missing_segments)."""
    src = source_text or ""
    missing = [seg.strip() for seg in literals(command)
               if seg.strip() and seg.strip() not in src]
    return (not missing, missing)


# ---- rung 6: generate -------------------------------------------------------------
# The no-card tail. This breaks grounding, so its one guarantee is label integrity: a
# generated command is NEVER presented as grounded. Per decision Q2 there is no
# danger/denylist — safety is the operator's; arlo's job is the honest label.

UNVERIFIED = ("UNVERIFIED — this command was GENERATED, not found in your ground truth. "
              "arlo cannot vouch for it. Read it, and run it only if you are sure; you "
              "are responsible for it.")


def unverified(command):
    """Stamp a generated command with the permanent rung-6 label. grounded and verified
    are False by construction and there is no source — the result cannot be mistaken for,
    or promoted to, a grounded rung."""
    return {"command": command, "grounded": False, "verified": False,
            "trust": UNVERIFIED, "source": None}
