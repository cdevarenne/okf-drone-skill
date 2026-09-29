# okf-drone-skill

An Open Knowledge Format (OKF) bundle grounds an agent skill. The skill plans one civil drone
mission, validates the plan against the bundle, scores the risk with EASA SORA 2.5, and writes a
go / no-go report for a human to sign.

The same pattern as [okf-grc-skill](https://github.com/cdevarenne/okf-grc-skill), in a new domain:
a knowledge-grounded agent finds the rules, makes an artifact, validates it against the rules,
scores the risk, and writes a document that a person signs.

**Scope:** mission planning, safety and regulatory compliance for civil operations in the EU.
No flight controller, no live NOTAM or weather feeds, no simulation in v1.

## Status

| Phase | Content | State |
|---|---|---|
| 0 | Scaffold, pinned versions, `.plan` subset schema, source register | Done |
| 1 | OKF bundle: regulations, SORA 2.5 tables, hazards, failsafes, MAVLink, mission types | Done, verified by the owner |
| 2 | `gen_plan`: mission request to QGroundControl `.plan` | Done |
| 3 | `validate_plan`, `score_risk` | Done |
| 4 | `render_report`, `signoff.yaml`, the seeded missions m01 to m05 | Done, owner review pending |
| 5 | Screenshots, "How this was built" | Planned |

The spec is [`docs/specs/2026-09-28-okf-drone-skill-v1-design.md`](docs/specs/2026-09-28-okf-drone-skill-v1-design.md).

## How it works

```
missions/<id>.yaml -> gen_plan -> validate_plan -> score_risk -> render_report
                        |             |               |              |
                   mission.plan  validation.json   risk.json   report.md, signoff.yaml
```

`make plan MISSION=missions/<id>.yaml` runs the pipeline. It calls no LLM.

- **GO:** all checks pass and there is no gap.
- **NO-GO:** at least one check fails.
- **HOLD:** no check fails, but at least one check or score has no concept (a coverage gap).
  A person must add knowledge or decide.

The tool writes `signoff.yaml` with empty approval fields. It never fills them.

## How grounding works

- Every check and every score cites a concept id in `knowledge/`. A check id is on exactly one
  concept (`checks:` in the frontmatter); the loader rejects a duplicate.
- Code reads regulatory values only from a concept's `table:`. There is no threshold in code.
- A check with no concept is a gap. It is never a default value. For example, the SORA
  operational safety objectives (OSOs) are not in v1, so a 'specific' category mission is HOLD.
- Every concept has a `# Source` section. It cites only documents with status `read` in
  [`docs/sources.md`](docs/sources.md). The conformance test enforces this.
- Every concept has a `verified` entry from a person. The conformance test enforces this too.
- A concept counts only if a person verified it; an unverified concept is a gap.

## Seeded missions

Five missions in [`missions/`](missions/) test the decision rule (spec §7):

- m01: an open-category VLOS survey within all limits.
- m02: an inspection above the open-category height limit.
- m03: a search with a waypoint outside the declared geofence.
- m04: a survey with no lost-link failsafe action.
- m05: a specific-category BVLOS survey; the SORA OSO table is not in the bundle.

`make seeded` runs them and writes the decisions, the failed checks, the gaps and the cited
concepts to [`docs/data/seeded.json`](docs/data/seeded.json). The golden test fails if that file
is not current.

## Knowledge bundle

| Folder | Content | Sources |
|---|---|---|
| [`regulations/`](knowledge/regulations/) | The 'open' category limits; the 'specific' category and SORA 2.5 | Reg. (EU) 2019/947; EASA AMC1 Art. 11 |
| [`risk/`](knowledge/risk/) | iGRC, ARC and TMPR, SAIL, containment; mitigations M1(A), M1(B), M1(C), M2 | EASA AMC1 Art. 11 (SORA 2.5); JARUS SORA 2.5 |
| [`hazards/`](knowledge/hazards/) | The flight-plan risk matrix: likelihood, severity, mitigation | Flight-plan template |
| [`failsafes/`](knowledge/failsafes/) | Lost link, battery, geofence, GPS loss: actions and PX4 parameters | Flight-plan template; PX4 v1.17 |
| [`mavlink/`](knowledge/mavlink/) | Takeoff, waypoint, return to launch, land | MAVLink common message set |
| [`mission-types/`](knowledge/mission-types/) | Grid, corridor, expanding square | Flight-plan template |
| [`platform/`](knowledge/platform/) | The QGroundControl `.plan` format | QGroundControl docs |

Where the EASA text (S2) and the JARUS text (S4) differ, the bundle uses the EASA text. The
differences are listed in [`docs/sources.md`](docs/sources.md).

## Quick start

Needs Python 3.14 and [uv](https://docs.astral.sh/uv/).

```sh
make bootstrap   # uv sync
make verify      # ruff and pytest
make render      # OKF visualizer HTML of knowledge/ in out/knowledge-viz.html
make plan MISSION=missions/m01-survey-open.yaml  # writes the five files in out/m01-survey-open/
make seeded      # runs m01 to m05; writes docs/data/seeded.json
```

## How this was built

Built with an AI coding agent (Claude Code) under a written process. The record is in the repo.

- **Spec, then plan, then tasks.** The spec is in [`docs/specs/`](docs/specs/). Each phase has
  a plan in [`docs/plans/`](docs/plans/) with the complete code and the expected test output.
  Each task has a tracking issue and one commit. The test fails first.
- **Plans are prototyped first.** The Phase 1 loader, tests and SORA tables were run in a
  scratch copy before they went into the plan. Executing the plan still found one plan error (a
  folder index cut one line short); it was fixed in the plan and in the bundle.
- **Sources before values.** No regulatory value was written from memory. Each one was read in
  a source document that the owner had read and marked `read`. The local copies are checked by
  SHA-256. Reading the source corrected one assumption (the 120 m limit is Article 4(1)(e) of
  Reg. (EU) 2019/947, not 4(1)(d)).
- **Human gates.** The owner read the sources (Phase 0) and verified every concept (Phase 1)
  before the next phase.

## Pins

External versions are in [`tools.lock`](tools.lock): the OKF commit, the QGroundControl plan
format versions, and the SORA edition.

## Layout

```
knowledge/                    OKF bundle
missions/                     mission requests m01 to m05 and SEEDED.yaml
.claude/skills/drone-mission-compliance/scripts/   okf_lib.py and the pipeline scripts
.claude/skills/drone-mission-compliance/schemas/   mission request schema
tests/                        unit and conformance tests
tests/fixtures/missions/      fixture mission requests (one per mission type)
docs/specs/, docs/plans/      spec and phase plans
docs/sources.md               source register
docs/data/                    generated results (make seeded)
```

## License

MIT. See [`LICENSE`](LICENSE).
