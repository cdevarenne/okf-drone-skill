"""Helpers for tests that need a changed copy of the real bundle."""

from dataclasses import replace
from pathlib import Path

from okf_lib import Bundle, load_bundle

BUNDLE = load_bundle(Path(__file__).resolve().parents[1] / "knowledge")


def without(*concept_ids: str) -> Bundle:
    """Return the bundle without the given concepts."""
    return Bundle({k: v for k, v in BUNDLE.concepts.items() if k not in concept_ids})


def unverified(*concept_ids: str) -> Bundle:
    """Return the bundle with the `verified` entries removed from the given concepts."""
    concepts = dict(BUNDLE.concepts)
    for cid in concept_ids:
        fm = {k: v for k, v in concepts[cid].frontmatter.items() if k != "verified"}
        concepts[cid] = replace(concepts[cid], frontmatter=fm)
    return Bundle(concepts)
