"""Run the four pipeline steps for one mission, as `make plan` does (spec §6)."""

from __future__ import annotations

from pathlib import Path

import gen_plan
import render_report
import score_risk
import validate_plan


def run_mission(mission: Path, knowledge: Path, lock: Path, out: Path) -> int:
    """Run gen_plan, validate_plan, score_risk and render_report. Return the first non-zero code."""
    common = ["--mission", str(mission), "--knowledge", str(knowledge), "--out", str(out)]
    for step, args in (
        (gen_plan.main, [*common, "--lock", str(lock)]),
        (validate_plan.main, common),
        (score_risk.main, common),
        (render_report.main, [*common, "--lock", str(lock)]),
    ):
        code = step(args)
        if code:
            return code
    return 0
