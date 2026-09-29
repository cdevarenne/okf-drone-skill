# CLAUDE.md — okf-drone-skill

## What this is
An OKF knowledge bundle grounds a skill that plans one drone mission, validates the plan against
the bundle, scores the risk (EASA SORA 2.5) and writes a go / no-go report for a human to sign.
Spec: `docs/specs/2026-09-28-okf-drone-skill-v1-design.md`. Read the spec before you change a data shape.
Template: `../okf-grc-skill`. Its specs, plans and README "How this was built" show the method.

## Scope
Civil mission planning, safety and regulatory compliance.

## Design properties
useful, secure, repeatable, composable, deterministic where it matters.
- `make plan` calls no LLM. LLM steps are extras and run only when the owner runs them.
- Every check and score cites a concept id. No concept -> coverage gap -> HOLD. Never a default value.
- Code reads regulatory values only from the bundle. No threshold in code.
- The tool never fills approval fields in `signoff.yaml`.
- Published numbers are generated, never typed: `docs/data/*.json` holds results; prose cites them.

## Working rules
- The first commit is by Claude Code under its own identity. Every later commit is by `cdevarenne`. No Co-Authored-By trailer.
- Work directly on `main`. No pull requests.
- CI is manual-only. Do not run it.
- The owner runs paid API steps locally, with a budget guard.
- The owner reviews and verifies anything a person must approve: `verified` entries, eval labels, SORA content.
- Spec first, then plan, then tasks, with tracking issues. One commit per task; the test fails first.
- Specs go in `docs/specs/`, plans in `docs/plans/`.
- Write docs, docstrings, comments and commit messages in ASD-STE100 Simplified Technical English.
- Before every commit: ruff and pytest.

## Toolchain
Python 3.14 + uv. `uv sync`; `uv run pytest`; `make plan MISSION=missions/<id>.yaml`.
All external versions are pinned in `tools.lock`.
