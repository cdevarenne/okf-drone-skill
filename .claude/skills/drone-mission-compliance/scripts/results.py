"""Check results for validation.json and risk.json (spec §5.3, §5.4), and the grounding rule."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from okf_lib import Bundle, Concept

PASS, FAIL, GAP, NOT_APPLICABLE = "pass", "fail", "gap", "not_applicable"


@dataclass(frozen=True)
class CheckResult:
    """One check or score. `concept_id` is None only for a gap with no concept."""

    check_id: str
    status: str
    concept_id: str | None
    evidence: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def is_verified(concept: Concept) -> bool:
    """Return True if a person verified the concept at or after its last change (`generated.at`)."""
    changed = _time(concept.frontmatter["generated"]["at"])
    entries = concept.frontmatter.get("verified") or []
    return any(
        str(e.get("by", "")).startswith("human:") and _time(e["at"]) >= changed for e in entries
    )


def _time(value: object) -> datetime:
    return datetime.fromisoformat(str(value))


def governing(bundle: Bundle, check_id: str) -> Concept | None:
    """Return the verified concept that governs `check_id`, or None (a coverage gap)."""
    concept = bundle.governing(check_id)
    return concept if concept is not None and is_verified(concept) else None


def verified_concept(bundle: Bundle, concept_id: str) -> Concept | None:
    """Return the concept `concept_id` if it exists and is verified, else None."""
    concept = bundle.concepts.get(concept_id)
    return concept if concept is not None and is_verified(concept) else None


def no_concept(check_id: str) -> CheckResult:
    """Return the gap for a check that no verified concept governs."""
    return CheckResult(
        check_id, GAP, None, "", f"no verified concept in the bundle governs {check_id}"
    )


def result(
    concept: Concept, check_id: str, status: str, evidence: str, message: str
) -> CheckResult:
    """Return a result that cites `concept`."""
    return CheckResult(check_id, status, concept.id, evidence, message)
