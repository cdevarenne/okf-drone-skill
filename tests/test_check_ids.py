"""Check that each v1 check id has its one governing concept (plan Decision 1)."""

from pathlib import Path

import pytest
from okf_lib import load_bundle

BUNDLE = load_bundle(Path(__file__).resolve().parents[1] / "knowledge")
V1_CHECKS = {
    "alt.max_agl": "regulations/easa-open",
    "category.operation": "regulations/easa-open",
    "plan.first_item_takeoff": "mavlink/nav-takeoff",
    "plan.last_item_return": "mavlink/nav-rtl",
    "plan.inside_geofence": "failsafes/geofence-breach",
    "failsafe.lost_link": "failsafes/lost-link",
    "failsafe.low_battery": "failsafes/low-battery",
    "failsafe.critical_battery": "failsafes/low-battery",
    "failsafe.geofence_breach": "failsafes/geofence-breach",
    "sora.applicable": "regulations/easa-specific-sora",
    "sora.igrc": "risk/igrc",
    "sora.final_grc": "risk/igrc",
    "sora.initial_arc": "risk/arc",
    "sora.residual_arc": "risk/arc",
    "sora.sail": "risk/sail",
    "sora.containment": "risk/containment",
}
KNOWN_GAPS = {"sora.oso"}


@pytest.mark.parametrize(("check_id", "concept_id"), V1_CHECKS.items())
def test_check_has_its_concept(check_id: str, concept_id: str) -> None:
    concept = BUNDLE.governing(check_id)
    assert concept is not None and concept.id == concept_id


def test_no_undeclared_check_ids() -> None:
    declared = {c for concept in BUNDLE.concepts.values() for c in concept.checks}
    assert declared == set(V1_CHECKS)


@pytest.mark.parametrize("check_id", sorted(KNOWN_GAPS))
def test_known_gap_has_no_concept(check_id: str) -> None:
    assert BUNDLE.governing(check_id) is None
