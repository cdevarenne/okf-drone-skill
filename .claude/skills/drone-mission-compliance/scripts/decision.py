"""The go / no-go decision that the tool proposes (spec §5.5). A person makes the decision."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from results import FAIL, GAP

GO, NO_GO, HOLD = "GO", "NO-GO", "HOLD"


@dataclass(frozen=True)
class Decision:
    """The proposed decision and the results that caused it."""

    value: str
    fails: tuple[dict[str, Any], ...]
    gaps: tuple[dict[str, Any], ...]


def decide(checks: Iterable[dict[str, Any]]) -> Decision:
    """Return NO-GO if a check fails, else HOLD if a check is a gap, else GO.

    `pass` and `not_applicable` do not change the decision. No checks at all is HOLD: nothing
    was checked, so the tool cannot propose GO.
    """
    checks = list(checks)
    fails = tuple(c for c in checks if c["status"] == FAIL)
    gaps = tuple(c for c in checks if c["status"] == GAP)
    value = NO_GO if fails else HOLD if gaps or not checks else GO
    return Decision(value, fails, gaps)
