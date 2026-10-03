"""Check the verified rule: a person verified the concept at or after its last change."""

from dataclasses import replace

from bundle_helpers import BUNDLE
from results import is_verified


def _with(generated_at: str, verified_at: str):
    c = BUNDLE.concepts["mavlink/nav-rtl"]
    fm = dict(c.frontmatter)
    fm["generated"] = {"by": "claude-code", "at": generated_at}
    fm["verified"] = [{"by": "human:owner", "at": verified_at}]
    return replace(c, frontmatter=fm)


def test_verified_after_the_change_counts() -> None:
    assert is_verified(_with("2026-10-02T10:00:00-07:00", "2026-10-02T11:00:00-07:00"))


def test_verified_before_the_change_does_not_count() -> None:
    assert not is_verified(_with("2026-10-02T10:00:00-07:00", "2026-09-28T21:00:00-07:00"))


def test_offsets_are_compared_as_times() -> None:
    assert is_verified(_with("2026-10-02T17:00:00+00:00", "2026-10-02T10:00:00-07:00"))
