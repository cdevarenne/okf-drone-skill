# okf-drone-skill v1 — Design Spec

- **Date:** 2026-09-28
- **Status:** draft; owner decisions recorded (§10)
- **Tracking:** `DevMoi/backlog.csv` DRN-01..DRN-08
- **Template:** `cdevarenne/okf-grc-skill` (layout, bundle conventions, `okf_lib`, grounding rule, method)
- **Sources:** `drone_flightplan_usecase.md`, `drone_sora_hazards_bundle.md`, `Comprehensive Drone Flight Plan Template.md`. Optional: `DroneControlSW.02.md`.

---

## 1. Goal and definition of done

An OKF knowledge bundle grounds a skill. The skill takes one mission request and generates a
QGroundControl `.plan`. It validates the plan against the bundle, scores the risk, and writes a
go / no-go report for a human to sign.

**Done when:**

1. `make plan MISSION=missions/<id>.yaml` writes `out/<id>/mission.plan`, `validation.json`,
   `risk.json`, `report.md` and `signoff.yaml`.
2. Each seeded mission in `missions/SEEDED.yaml` gets its expected decision (§7).
3. Each check in `validation.json` and each score in `risk.json` cites a concept id.
   A check or score that has no concept is a **coverage gap**. It is never a default value.
4. `mission.plan` validates against the vendored `.plan` subset schema.
5. The bundle conformance test passes, and each concept carries `verified`.
6. `make render` writes the OKF visualizer HTML for `knowledge/`.

**Out of scope for v1:** simulation (PX4 SITL is DRN-10), live NOTAM / TFR / weather feeds,
LLM steps (DRN-09), fleet operations, FAA Part 107, national (DGAC) additions, a flight
controller, computer vision, ROS.

## 2. Guardrails

- **Scope:** mission planning, safety and regulatory compliance for civil operations.
- **Original work only.** Bundle text is written for this repo from public sources. Each
  regulatory concept names its source document and section.
- **Grounding is enforced in code.** A check reaches a rule only through a declaration in the
  bundle. No fallback value, no built-in threshold.
- **Deterministic core.** `make plan` calls no LLM.
- **Human decides.** The tool writes `signoff.yaml` with empty approval fields. It never fills them.
- **Knowledge gap is explicit.** SORA content goes into the bundle only after the owner reads the
  source (§3). A table that is not in the bundle gives HOLD, not a guess.

## 3. Pinned external versions

| Dependency | Pin | Notes |
|---|---|---|
| Python | `>=3.14`, uv | Same as the template |
| OKF spec | v0.2, `GoogleCloudPlatform/open-knowledge-format` @ `ad30107c31c0` | Template pin. DRN-02 checks for a newer commit. |
| QGC plan format | `fileType: Plan`, `version: 1`; `mission.version: 2`; `geoFence.version: 2`; `rallyPoints.version: 2` | [QGC plan file format](https://docs.qgroundcontrol.com/master/en/qgc-dev-guide/file_formats/plan.html). Vendor a subset schema in `tests/fixtures/`. |
| SORA | JARUS SORA 2.5, as adopted in EASA AMC & GM to Reg. (EU) 2019/947 by [ED Decision 2025/018/R](https://easa.europa.eu/en/document-library/agency-decisions/ed-decision-2025018r) | Source text: [JARUS SORA 2.5 main body](http://jarus-rpas.org/wp-content/uploads/2024/06/SORA-v2.5-Main-Body-Release-JAR_doc_25.pdf). Primary text: the Decision annex, AMC & GM Issue 1, Amendment 4 (renamed from Amendment 3 by the corrigendum of 12 December 2025; no content change). The annex states no applicability date. |

**SORA 2.5 changes that affect the existing slice** (`drone_sora_hazards_bundle.md` uses 2.0):

- Ground-risk mitigation M1 is split into M1(A) sheltering, M1(B) operational restrictions and
  M1(C) ground observation.
- Intrinsic GRC uses population density and a critical-area calculation (Annex F).
- Containment has low, medium and high levels and is assessed earlier.

Source for these three points: [EU Drone Port, SORA 2.5 summary](https://eudroneport.com/blog/sora-2-5-european-uas-operations/)
(secondary). DRN-02 confirms them in the JARUS main body. Not yet confirmed: the status of M3 (ERP),
the OSO count, and the SAIL table values.

## 4. Repository layout

```
okf-drone-skill/
├── CLAUDE.md
├── README.md                 # incl. "How this was built"
├── Makefile                  # bootstrap, plan, render, test, clean
├── pyproject.toml, uv.lock, tools.lock
├── knowledge/                # OKF bundle (§5.1)
├── missions/                 # mission requests + SEEDED.yaml
├── .claude/skills/drone-mission-compliance/
│   ├── SKILL.md
│   └── scripts/              # okf_lib.py, gen_plan.py, validate_plan.py, score_risk.py, render_report.py
├── tests/                    # fixtures/, conformance, unit, golden
├── docs/specs/, docs/plans/, docs/data/, docs/screenshots/
└── out/                      # git-ignored
```

## 5. Data contracts

### 5.1 Bundle conventions (OKF v0.2, same rules as the template §5.1)

| `type` | Files (v1) |
|---|---|
| `Regulation` | `regulations/easa-open.md`, `easa-specific-sora.md` |
| `Risk Table` | `risk/igrc.md`, `risk/arc.md`, `risk/sail.md`, `risk/containment.md` |
| `Mitigation` | `risk/m1a.md`, `m1b.md`, `m1c.md`, `m2.md` |
| `Hazard` | `hazards/*.md` (the 10 rows from the flight-plan template) |
| `Failsafe` | `failsafes/lost-link.md`, `low-battery.md`, `geofence-breach.md`, `gps-loss.md` |
| `MAVLink Command` | `mavlink/nav-takeoff.md` (22), `nav-waypoint.md` (16), `nav-rtl.md` (20), `nav-land.md` (21) |
| `Mission Type` | `mission-types/mapping-survey.md`, `infrastructure-inspection.md`, `search-pattern.md` |
| `Reference` | `platform/qgc-plan-format.md` |

- Every concept carries `type`, `title`, `description`, `tags`, `generated`, and, after review,
  `verified: [{by: "human:cdevarenne", at}]`.
- **Extension key `checks`:** a list of check ids this concept governs (for example
  `alt.max_agl`). A check id appears on exactly one concept. The loader raises `BundleError`
  otherwise.
- **Extension key `table`:** structured values for `Risk Table` concepts. Code reads values only
  from here.
- **Extension keys `likelihood`, `severity`:** integers 1–5 on `Hazard` concepts.
- Every `Regulation` and `Risk Table` concept has a `# Source` section with document, edition,
  section and URL.

### 5.2 Mission request (`missions/<id>.yaml`)

```yaml
id: m01-survey-open       # the file name without .yaml
mission_type: mapping-survey  # a concept in mission-types/
category: open            # open | specific
operation: VLOS           # VLOS | BVLOS
home: {lat: 44.7990, lon: -0.6000, amsl_m: 50}  # takeoff point; plannedHomePosition
terrain: flat             # flat | varied
area: {polygon: [[lat, lon], ...]}      # convex; the pattern stays inside it
geofence: {polygon: [[lat, lon], ...]}  # the inclusion polygon in the .plan
max_altitude_agl_m: 100   # the altitude of every item, relative to home
speed_ms: 8               # cruise and hover speed in the .plan
pattern: {spacing_m: 40}  # grid; expanding square adds datum: [lat, lon];
                          # corridor is {route: [[lat, lon], ...]}
ua: {mtom_kg: 0.9, char_dimension_m: 0.35, max_speed_ms: 15}
ground: {population_density: sparsely-populated}  # value set comes from risk/igrc.md
airspace: {class: G, declared_by: operator}
failsafes: {lost_link: RTL, low_battery: RTL, critical_battery: LAND, geofence_breach: RTL}
```

The schema is `.claude/skills/drone-mission-compliance/schemas/mission.schema.json` (Phase 2).
Value sets that come from the bundle (mission types, population density bands, failsafe
actions) are not in the schema; the pipeline checks them against the bundle.

Airspace, NOTAM and weather are **declared inputs** in v1. The report says so.
Terrain is a declared input too: v1 has no terrain data (see §6, `alt.max_agl`).
Failsafes are vehicle parameters, not part of the `.plan` file. v1 checks the declared values.
DRN-02 records the matching PX4 parameter names in `failsafes/*.md`.

### 5.3 Check result (`validation.json`)

`{check_id, status: pass|fail|gap, concept_id|null, evidence, message}`.
`gap` has `concept_id: null` and names the missing concept.

### 5.4 Risk result (`risk.json`)

Hazard matrix rows `{hazard_id, likelihood, severity, score, mitigations[], residual}`.
SORA summary `{igrc, mitigations_applied[], final_grc, initial_arc, residual_arc, sail}`.
Each value cites its concept. A missing or unverified table gives `"not_assessed"` plus a gap.

### 5.5 Decision

- **GO:** all checks pass, no gaps.
- **NO-GO:** at least one check fails.
- **HOLD:** no fail, but at least one gap. A human must add knowledge or decide.

## 6. Pipeline

`gen_plan | validate_plan | score_risk | render_report`, file-based, one purpose each.

1. `okf_lib.load_bundle` (copied from the template, then extended for `checks` and `table`).
2. `gen_plan`: pattern by mission type (grid, corridor, expanding square; the pattern name
   comes from the mission-type concept). Writes takeoff at `home`, the pattern waypoints, RTL,
   and the declared geofence polygon. It writes what the request asks for and never corrects
   it; `validate_plan` judges the result. A mission type or command with no concept is a gap.
3. `validate_plan`: v1 checks: altitude ceiling, all waypoints inside geofence, first item is
   takeoff, last item is RTL or land, declared failsafes present, category matches operation.
   Height rule (`alt.max_agl`): the plan altitudes are relative to home, and the
   `regulations/easa-open` limit is from the closest point of the surface. With
   `terrain: flat`, the check compares the plan altitudes with the limit. With
   `terrain: varied`, v1 has no terrain data, so the check is a gap (HOLD).
4. `score_risk`: hazard matrix from `hazards/`; SORA summary from `risk/` tables.
5. `render_report`: fills the flight-plan template sections, the decision and the audit trail.

## 7. Seeded missions (`missions/SEEDED.yaml`)

| Mission | Seeded condition | Expected |
|---|---|---|
| m01 | open category, VLOS, within all limits | GO |
| m02 | altitude above the open-category ceiling | NO-GO, cites `regulations/easa-open` |
| m03 | one waypoint outside the geofence (the declared geofence does not contain the area) | NO-GO, cites `failsafes/geofence-breach` |
| m04 | no lost-link failsafe declared | NO-GO, cites `failsafes/lost-link` |
| m05 | specific category, BVLOS; the OSO table (`sora.oso`) is not in the bundle | HOLD (gap), not GO |

## 8. Testing and verification

- Conformance test: every concept parses, has `verified`, and each check id is unique.
- Unit tests per script; the first test fails before the code exists.
- Golden test: m01–m05 decisions and cited concept ids.
- `make verify`: ruff, pytest, schema validation of every `mission.plan`.

## 9. Phases

| Phase | Items | Human gate |
|---|---|---|
| 0 | scaffold, pins, SORA 2.5 read (DRN-02) | owner reads the JARUS main body |
| 1 | bundle (DRN-03) | owner reviews each concept, adds `verified` |
| 2 | `gen_plan` (DRN-04) | — |
| 3 | `validate_plan` (DRN-05), `score_risk` (DRN-06) | — |
| 4 | report + loop (DRN-07) | owner reviews m01–m05 output |
| 5 | screenshots, README "How this was built" | — |

## 10. Decisions (owner, 2026-09-28)

1. Repo name: `okf-drone-skill`.
2. First commit: made by Claude Code under its own identity, so it shows as a contributor.
   All later commits: `cdevarenne`.
3. Specs in `docs/specs/`, plans in `docs/plans/`. No `superpowers/` directory.
4. Population density and all other SORA values: SORA 2.5 as adopted by EASA in 2025
   (ED Decision 2025/018/R). Not SORA 2.0. The owner reads the iGRC table in DRN-02 before
   the bundle uses it.
