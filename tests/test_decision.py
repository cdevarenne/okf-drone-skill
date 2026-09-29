"""Check the decision rule (spec §5.5)."""

import pytest
from decision import GO, HOLD, NO_GO, decide


def check(check_id: str, status: str) -> dict:
    return {
        "check_id": check_id,
        "status": status,
        "concept_id": None,
        "evidence": "",
        "message": "",
    }


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        (["pass", "pass"], GO),
        (["pass", "not_applicable"], GO),
        ([], HOLD),
        (["pass", "gap"], HOLD),
        (["gap", "not_applicable"], HOLD),
        (["pass", "fail"], NO_GO),
        (["gap", "fail"], NO_GO),
    ],
)
def test_decision_rule(statuses: list[str], expected: str) -> None:
    assert decide(check(f"c.{i}", s) for i, s in enumerate(statuses)).value == expected


def test_decision_keeps_the_causes() -> None:
    d = decide([check("a.x", "fail"), check("b.y", "gap"), check("c.z", "pass")])
    assert [c["check_id"] for c in d.fails] == ["a.x"]
    assert [c["check_id"] for c in d.gaps] == ["b.y"]
