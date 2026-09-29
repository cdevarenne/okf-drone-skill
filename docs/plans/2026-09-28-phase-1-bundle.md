# okf-drone-skill Phase 1 Plan: the OKF bundle

Execute with Claude Code, task by task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** a `knowledge/` bundle of 32 concepts (spec §5.1) that `okf_lib` loads, that passes the
conformance tests, and that the owner verifies. Every regulatory value comes from a source with
status `read` in `docs/sources.md`.

**Spec:** `docs/specs/2026-09-28-okf-drone-skill-v1-design.md` §5.1, §9 Phase 1. **Backlog:** DRN-03.

**Template:** `cdevarenne/okf-grc-skill` @ `b9c9311`: `okf_lib.py`, `tests/test_okf_lib.py`,
`tests/test_bundle_conformance.py`, the bundle layout (`index.md`, `log.md`, folder indexes).

**Provenance:** Tasks 1 to 6 were run in a prototype on 2026-09-28 (Python 3.14.0rc2, uv 0.8.17,
ruff 0.16.9, pytest 9.1.1). The file contents below are copied from that run. The expected
outputs come from it. The SORA values were read from the local copies of S2 and S4; both SHA-256
values match `docs/sources.md`.

## Global constraints

- Commits on `main` as `cdevarenne`. Short subject in ASD-STE100. Body line `Closes #N`.
- Every commit ships tests, or says that it is docs only. The test fails first.
- Before every commit: `make verify` (ruff and pytest).
- `generated.by` is `claude-code`. Do not write a model name in the repo.
- `generated.at` is the time of the commit, in the owner's time zone (PST, `-07:00`). The
  files below show the prototype value `2026-09-28T20:00:00-07:00`.
- A concept cites only sources with status `read`. The conformance test enforces this.
- The bundle uses S2 values where S2 and S4 differ, and cites S4 as origin (decision of
  2026-09-28, `docs/sources.md`).
- Task 12 is a human gate. The executing agent stops there.

## Decisions for the owner (before Task 0)

Read these and change the plan if you disagree.

1. **Check ids.** Each check id is on exactly one concept (spec §5.1). Proposed set:

   | Check id | Concept | Seeded mission |
   |---|---|---|
   | `alt.max_agl` | `regulations/easa-open` | m02 |
   | `category.operation` | `regulations/easa-open` | |
   | `plan.first_item_takeoff` | `mavlink/nav-takeoff` | |
   | `plan.last_item_return` | `mavlink/nav-rtl` (RTL or LAND) | |
   | `plan.inside_geofence` | `failsafes/geofence-breach` | m03 |
   | `failsafe.lost_link` | `failsafes/lost-link` | m04 |
   | `failsafe.low_battery` | `failsafes/low-battery` | |
   | `failsafe.critical_battery` | `failsafes/low-battery` | |
   | `failsafe.geofence_breach` | `failsafes/geofence-breach` | |
   | `sora.applicable` | `regulations/easa-specific-sora` | m05 |
   | `sora.igrc`, `sora.final_grc` | `risk/igrc` | m05 |
   | `sora.initial_arc`, `sora.residual_arc` | `risk/arc` | m05 |
   | `sora.sail` | `risk/sail` | m05 |
   | `sora.containment` | `risk/containment` | m05 |
   | `sora.oso` | none (the OSO table is not in v1) | m05 |

2. **m05 stays HOLD.** Phase 1 puts the SORA tables in the bundle, so the spec §7 reason for m05
   ("SORA table not in bundle") no longer holds. The OSO table (S2 Table 14) is out of v1
   (spec §5.1 has no OSO concept). So `sora.oso` has no concept, is a gap, and m05 stays HOLD.
   Phase 3 updates spec §7 to say this.
3. **`failsafes/gps-loss` has no check.** The mission request (spec §5.2) declares no GPS-loss
   action. The concept exists for the hazard links and the PX4 parameter name.
4. **Hazard values come from S10.** Likelihood, severity and residual (all `Low`) are the
   values in the flight-plan template §6. The score is likelihood x severity, as the template's
   "Risk Score" column shows. The input note `drone_sora_hazards_bundle.md` is a draft only;
   the bundle does not copy its SORA 2.0 text (M3, 400 ft).
5. **New sources S9 and S10** (Task 1). S10 is your flight-plan template. Set it to `read`
   before Task 4. S9 (MAVLink) must be `read` before Task 7.
6. **ARC inputs.** `risk/arc` needs declared airspace facts (atypical, airport environment,
   controlled, TMZ, urban, above 500 ft). The mission request (spec §5.2) does not have them yet.
   Phase 3 extends it. Phase 1 only records the decision tree.

## Blocked inputs

The container's network policy denies `eur-lex.europa.eu`, `docs.px4.io` and `mavlink.io`
(also for the server-side fetch, checked 2026-09-28).
Tasks 7, 8 and 10 need these sources. Two ways to unblock:

- Add the three hosts to the environment's allowed domains, or
- Save the pages as PDF to Google Drive (the Drive connector works) and send the links.

| Source | Needed by | What |
|---|---|---|
| S1 Reg. (EU) 2019/947, consolidated 2025-05-01: https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02019R0947-20250501 | Task 10 | Art. 4 (open category), Art. 5 and 11 (specific category) |
| S7 PX4 v1.17: https://docs.px4.io/v1.17/en/advanced_config/parameter_reference and https://docs.px4.io/v1.17/en/config/safety_intro | Task 8 | Failsafe parameter names and allowed values |
| S9 MAVLink common message set | Task 7 | `MAV_CMD_NAV_*` ids 16, 20, 21, 22 and their params |

Tasks 1 to 6 and 11 do not need them.

## Task order

1 → 2 → 3 → 4, 5, 6 (any order) → 7 → 8 → 9 → 10 → 11 → 12.
Task 9 (hazards) links to failsafes, so Task 8 comes first.

## Task 0: Tracking issues (no commit)

- [ ] **Step 1:** Create one issue per task. The last issue is #4, so Task N becomes issue #N+4.

```
T1 (DRN-03): Register S9, S10 and the S2/S4 differences
T2 (DRN-03): okf_lib: load the bundle
T3 (DRN-03): Bundle root and conformance tests
T4 (DRN-03): Reference and mission-type concepts
T5 (DRN-03): SORA risk tables
T6 (DRN-03): SORA ground-risk mitigations
T7 (DRN-03): MAVLink command concepts (needs S9)
T8 (DRN-03): Failsafe concepts (needs S7)
T9 (DRN-03): Hazard concepts
T10 (DRN-03): Regulation concepts and the v1 check ids (needs S1)
T11 (DRN-03): Bundle map, log and render
T12 (DRN-03): Owner verifies the bundle (human gate)
```

Body: `Phase 1. See docs/plans/2026-09-28-phase-1-bundle.md, Task N.`

- [ ] **Step 2:** List the issues. Expected: #5 to #16 open.

---

## Task 1: Register S9, S10 and the S2/S4 differences (#5)

**Files:** modify `docs/sources.md`. Docs only.

- [ ] **Step 1:** Add two rows after S8 in the first table:

```markdown
| S9 | MAVLink common message set | master | https://mavlink.io/en/messages/common.html | `mavlink/*` command ids and parameters | unread |
| S10 | Comprehensive Drone Flight Plan Template (owner input; kept outside the repo) | 1.0 | none | `hazards/*`, `mission-types/*`, failsafe actions | unread |
```

S10 has no URL. It is an owner input, kept outside the repo like the PDFs.

- [ ] **Step 2:** Add this section before "## Known discrepancy in S8":

```markdown
## Differences between S2 and S4 (Phase 1)

Found 2026-09-28 by agent in the local copies (SHA-256 match). The bundle uses S2.

| Topic | S2 (AMC1 Art. 11) | S4 (JARUS main body) |
|---|---|---|
| 250 g rule for iGRC 1 | adds "unless operating over assemblies of people" (p. 24) | no exception (p. 34) |
| Containment Table 8 rows | I & II; III; IV, V & VI (p. 39) | I & II; III; "IV - VI"; "V-VI", which overlap (p. 49) |
| Containment Table 12 speed | < 120 m/s (p. 41) | < 125 m/s (p. 50) |
| VLOS ARC reduction | VLOS and BVLOS with airspace observers (p. 34) | VLOS and pilot with an observer alongside (p. 43) |
| SAIL table caption | "Table 3" (p. 38); the text calls it Table 7 | Table 7 (p. 47) |

The iGRC, Table 5 credits, TMPR and SAIL values are the same in S2 and S4.
```

- [ ] **Step 3:** In the first table, set the S1 edition to `consolidated 2025-05-01` with the
  URL above, and set the S7 edition to `v1.17` with the two URLs above (owner, 2026-09-28).
- [ ] **Step 4: Verify.** `make verify`. Expected: `14 passed`.
- [ ] **Step 5: Commit.** `Register S9, S10 and the S2/S4 differences (docs only)`, `Closes #5`.
- [ ] **Step 6: Owner.** Set S10 to `read YYYY-MM-DD`. Task 4 needs it.

---

## Task 2: okf_lib: load the bundle (#6)

**Files:** create `.claude/skills/drone-mission-compliance/scripts/okf_lib.py` (delete the
`.gitkeep` there), `tests/test_okf_lib.py`, `tests/fixtures/bundle/`.

The loader is the template's loader without the GRC parts (controls, frameworks, `rule_ids`,
suppressions). It adds `checks` (unique across the bundle, else `BundleError`) and `table`
(a mapping). `Bundle.governing(check_id)` returns the one concept for a check, or `None` for a
coverage gap.

- [ ] **Step 1: Write the fixture bundle.**

`tests/fixtures/bundle/index.md`:

```markdown
---
okf_version: "0.2"
---
# Fixture bundle

* [Risk](risk/) - one risk table
* [Failsafes](failsafes/) - one failsafe
```

`tests/fixtures/bundle/log.md`:

```markdown
# Directory Update Log

## 2026-09-28
* **Initialization**: Fixture bundle for tests/test_okf_lib.py.
```

`tests/fixtures/bundle/risk/sail.md`:

```markdown
---
type: Risk Table
title: SAIL determination (fixture)
description: Fixture risk table. The values are test data, not SORA values.
tags: [fixture]
checks: [sora.sail]
table:
  rows: {"2": {a: I}}
---
# Rule

Test data only. See [lost link](../failsafes/lost-link.md) and [missing](../risk/missing.md).

# Source

Fixture.
```

`tests/fixtures/bundle/failsafes/lost-link.md`:

```markdown
---
type: Failsafe
title: Lost link (fixture)
description: Fixture failsafe.
tags: [fixture]
checks: [failsafe.lost_link]
---
# Rule

Test data only. See [the SORA page](https://example.org/sora.md) and [index](../index.md).
```

- [ ] **Step 2: Write the failing test.**

`tests/test_okf_lib.py`:

```python
"""Check the bundle loader against a fixture bundle and against broken files."""

from pathlib import Path

import pytest
from okf_lib import BundleError, load_bundle

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "bundle"


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_loads_concepts_and_skips_reserved_files() -> None:
    assert set(load_bundle(FIXTURE).concepts) == {"risk/sail", "failsafes/lost-link"}


def test_concept_fields() -> None:
    sail = load_bundle(FIXTURE).concepts["risk/sail"]
    assert sail.type == "Risk Table"
    assert sail.path == "risk/sail.md"
    assert sail.tags == ("fixture",)
    assert sail.checks == ("sora.sail",)
    assert sail.table == {"rows": {"2": {"a": "I"}}}


def test_links_resolve_and_keep_broken_links() -> None:
    bundle = load_bundle(FIXTURE)
    assert bundle.concepts["risk/sail"].links == ("failsafes/lost-link", "risk/missing")
    assert bundle.concepts["failsafes/lost-link"].links == ()


def test_governing_concept_or_gap() -> None:
    bundle = load_bundle(FIXTURE)
    assert bundle.governing("failsafe.lost_link").id == "failsafes/lost-link"
    assert bundle.governing("alt.max_agl") is None


def test_of_type_and_section() -> None:
    bundle = load_bundle(FIXTURE)
    assert [c.id for c in bundle.of_type("Failsafe", "Risk Table")] == [
        "failsafes/lost-link",
        "risk/sail",
    ]
    sail = bundle.concepts["risk/sail"]
    assert bundle.section(sail, "Source") == "Fixture."
    assert bundle.section(sail, "Nope") is None


def test_table_defaults_to_empty() -> None:
    assert load_bundle(FIXTURE).concepts["failsafes/lost-link"].table == {}


@pytest.mark.parametrize(
    ("rel", "text", "match"),
    [
        ("a.md", "just markdown\n", "missing YAML frontmatter"),
        ("a.md", "---\ntitle: no type\n---\n", "no non-empty 'type'"),
        ("a.md", "---\ntype: X\ntags: one\n---\n", "'tags' must be a YAML list"),
        ("a.md", "---\ntype: X\nchecks: [Alt]\n---\n", "is not '<group>.<name>'"),
        ("a.md", "---\ntype: X\ntable: [1, 2]\n---\n", "'table' must be a YAML mapping"),
        ("a.md", "---\ntype: X\ntitle: [unclosed\n---\n", "unparseable frontmatter"),
    ],
)
def test_broken_file_is_rejected(tmp_path: Path, rel: str, text: str, match: str) -> None:
    _write(tmp_path, rel, text)
    with pytest.raises(BundleError, match=match):
        load_bundle(tmp_path)


def test_duplicate_check_id_is_rejected(tmp_path: Path) -> None:
    _write(tmp_path, "a.md", "---\ntype: X\nchecks: [alt.max_agl]\n---\n")
    _write(tmp_path, "b.md", "---\ntype: Y\nchecks: [alt.max_agl]\n---\n")
    with pytest.raises(BundleError, match="already declared by a"):
        load_bundle(tmp_path)
```

Run `uv run pytest -q`. Expected: `ERROR collecting tests/test_okf_lib.py`,
`ModuleNotFoundError: No module named 'okf_lib'`.

- [ ] **Step 3: Write the loader.**

`.claude/skills/drone-mission-compliance/scripts/okf_lib.py`:

```python
"""Load an OKF v0.2 bundle into an in-memory concept graph.

Adapted from okf-grc-skill. This version adds two extension keys: `checks` (the check ids a
concept governs) and `table` (the structured values of a concept). Code reads regulatory values
only from `table`.
"""

from __future__ import annotations

import posixpath
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

RESERVED = frozenset({"index.md", "log.md"})
_FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n?(.*)\Z", re.DOTALL)
_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
_H1 = re.compile(r"^# (.+?)\s*$", re.MULTILINE)
_CHECK_ID = re.compile(r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+")


class BundleError(ValueError):
    """A bundle file violates OKF v0.2 conformance or a convention of this repo."""


@dataclass(frozen=True)
class Concept:
    """One OKF concept document."""

    id: str
    path: str
    type: str
    title: str
    description: str
    tags: tuple[str, ...]
    checks: tuple[str, ...]
    table: Mapping[str, Any]
    frontmatter: Mapping[str, Any]
    body: str
    links: tuple[str, ...]


@dataclass(frozen=True)
class Bundle:
    """All concepts in a bundle, keyed by concept id."""

    concepts: Mapping[str, Concept]

    def of_type(self, *types: str) -> list[Concept]:
        """Return the concepts of the given types, sorted by id."""
        return sorted((c for c in self.concepts.values() if c.type in types), key=lambda c: c.id)

    def governing(self, check_id: str) -> Concept | None:
        """Return the one concept that declares `check_id` in `checks`, or None (a coverage gap)."""
        return next((c for c in self.concepts.values() if check_id in c.checks), None)

    def section(self, concept: Concept, heading: str) -> str | None:
        """Return the body text under `# heading`, up to the next level-1 heading."""
        matches = list(_H1.finditer(concept.body))
        for i, m in enumerate(matches):
            if m.group(1) == heading:
                end = matches[i + 1].start() if i + 1 < len(matches) else len(concept.body)
                return concept.body[m.end() : end].strip()
        return None


def _resolve_link(target: str, concept_path: str) -> str | None:
    """Return the concept id that a markdown link points to, or None for a non-concept link."""
    target = target.split("#", 1)[0]
    if "://" in target or target.startswith("mailto:") or not target.endswith(".md"):
        return None
    if target.startswith("/"):
        resolved = posixpath.normpath(target.lstrip("/"))
    else:
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(concept_path), target))
    if resolved.startswith("..") or posixpath.basename(resolved) in RESERVED:
        return None
    return resolved.removesuffix(".md")


def _string_list(rel_path: str, fm: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = fm.get(key, [])
    if not isinstance(value, list):
        raise BundleError(f"{rel_path}: '{key}' must be a YAML list")
    return tuple(str(v) for v in value)


def _parse(rel_path: str, text: str) -> Concept:
    m = _FRONTMATTER.match(text)
    if not m:
        raise BundleError(f"{rel_path}: missing YAML frontmatter")
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        raise BundleError(f"{rel_path}: unparseable frontmatter: {e}") from e
    if not isinstance(fm, dict) or not str(fm.get("type") or "").strip():
        raise BundleError(f"{rel_path}: frontmatter has no non-empty 'type'")
    checks = _string_list(rel_path, fm, "checks")
    for check in checks:
        if not _CHECK_ID.fullmatch(check):
            raise BundleError(f"{rel_path}: check id {check!r} is not '<group>.<name>'")
    table = fm.get("table", {})
    if not isinstance(table, dict):
        raise BundleError(f"{rel_path}: 'table' must be a YAML mapping")
    body = m.group(2)
    stem = rel_path.removesuffix(".md")
    return Concept(
        id=stem,
        path=rel_path,
        type=str(fm["type"]).strip(),
        title=str(fm.get("title") or posixpath.basename(stem)),
        description=str(fm.get("description") or ""),
        tags=_string_list(rel_path, fm, "tags"),
        checks=checks,
        table=table,
        frontmatter=fm,
        body=body,
        links=tuple(
            dict.fromkeys(
                link
                for t in _LINK.findall(body)
                if (link := _resolve_link(t, rel_path)) is not None
            )
        ),
    )


def load_bundle(root: Path) -> Bundle:
    """Parse every non-reserved .md under `root` into a Bundle.

    Raise BundleError if a file does not conform, or if two concepts declare the same check id.
    """
    concepts: dict[str, Concept] = {}
    owner: dict[str, str] = {}
    for path in sorted(root.rglob("*.md")):
        if path.name in RESERVED:
            continue
        rel = path.relative_to(root).as_posix()
        concept = _parse(rel, path.read_text(encoding="utf-8"))
        for check in concept.checks:
            if check in owner:
                raise BundleError(
                    f"{rel}: check id {check!r} is already declared by {owner[check]}"
                )
            owner[check] = concept.id
        concepts[concept.id] = concept
    return Bundle(concepts=concepts)
```

- [ ] **Step 4: Verify.** `make verify`. Expected: `All checks passed!` and `27 passed`.
- [ ] **Step 5: Commit.** `Add okf_lib to load the bundle`, `Closes #6`.

---

## Task 3: Bundle root and conformance tests (#7)

**Files:** create `knowledge/index.md`, `knowledge/log.md`, `tests/test_bundle_conformance.py`;
delete `knowledge/.gitkeep`.

The conformance test checks OKF v0.2 structure and the rules of this repo: known types,
required metadata, relative and unbroken links, and a `# Source` section that cites only
sources with status `read`. `EXPECTED` starts empty. Each later task adds its row first, so its
test fails first. The `verified` test comes at Task 12.

- [ ] **Step 1: Write the failing test.**

`tests/test_bundle_conformance.py`:

```python
"""Check the knowledge/ bundle: OKF v0.2 conformance and the conventions of this repo."""

import re
from pathlib import Path

import pytest
import yaml
from okf_lib import load_bundle

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "knowledge"
SOURCES = ROOT / "docs" / "sources.md"
TYPES = {
    "Regulation",
    "Risk Table",
    "Mitigation",
    "Hazard",
    "Failsafe",
    "MAVLink Command",
    "Mission Type",
    "Reference",
}
# Concept ids per type. Each Phase 1 task adds its row before it adds the files.
EXPECTED: dict[str, set[str]] = {}
BUNDLE = load_bundle(KNOWLEDGE)
CONCEPTS = sorted(BUNDLE.concepts.values(), key=lambda c: c.id)


def source_status() -> dict[str, str]:
    """Return {source id: status} from the first table in docs/sources.md."""
    rows = re.findall(r"^\| (S\d+) \|.*\| ([^|]+) \|$", SOURCES.read_text(), re.MULTILINE)
    return {sid: status.strip() for sid, status in rows}


def test_root_index_declares_okf_version() -> None:
    text = (KNOWLEDGE / "index.md").read_text()
    assert yaml.safe_load(text.split("---\n")[1]) == {"okf_version": "0.2"}


def test_folder_indexes_have_no_frontmatter() -> None:
    for index in KNOWLEDGE.rglob("index.md"):
        if index.parent != KNOWLEDGE:
            assert not index.read_text().startswith("---"), index


def test_log_dates_are_iso() -> None:
    for log in KNOWLEDGE.rglob("log.md"):
        for heading in re.findall(r"^## (.+)$", log.read_text(), re.MULTILINE):
            assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", heading), f"{log}: {heading}"


def test_types_are_the_documented_set() -> None:
    assert {c.type for c in CONCEPTS} <= TYPES


def test_bundle_has_the_expected_concepts() -> None:
    for type_, ids in EXPECTED.items():
        assert {c.id for c in BUNDLE.of_type(type_)} == ids, type_


def test_no_broken_links() -> None:
    for concept in CONCEPTS:
        for link in concept.links:
            assert link in BUNDLE.concepts, f"{concept.path}: broken link to {link}"


def test_links_are_relative() -> None:
    """The pinned OKF visualizer ignores bundle-absolute links."""
    for concept in CONCEPTS:
        assert "](/" not in concept.body, concept.path


@pytest.mark.parametrize("concept", CONCEPTS, ids=lambda c: c.id)
def test_required_metadata(concept) -> None:
    fm = concept.frontmatter
    assert fm.get("title") and fm.get("description") and fm.get("tags"), concept.path
    assert fm.get("generated", {}).get("by") and fm["generated"].get("at"), concept.path


@pytest.mark.parametrize("concept", CONCEPTS, ids=lambda c: c.id)
def test_source_cites_only_read_documents(concept) -> None:
    source = BUNDLE.section(concept, "Source")
    assert source, f"{concept.path}: no '# Source' section"
    cited = set(re.findall(r"\bS\d+\b", source))
    assert cited, f"{concept.path}: '# Source' names no source id"
    status = source_status()
    for sid in sorted(cited):
        assert status.get(sid, "").startswith("read"), f"{concept.path}: {sid} is not read"
```

Run `uv run pytest -q`. Expected: `1 failed, 33 passed, 2 skipped`. The failure is
`test_root_index_declares_okf_version` (`FileNotFoundError` for `knowledge/index.md`).

- [ ] **Step 2: Write the bundle root.**

`knowledge/index.md`:

```markdown
---
okf_version: "0.2"
---
# OKF Drone Mission Knowledge Bundle

Knowledge graph that grounds the `drone-mission-compliance` skill. Every check and every score
that the skill writes cites a concept here. A check or a score with no concept is a coverage
gap. It is never a default value.

# Map
```

`knowledge/log.md`:

```markdown
# Directory Update Log

## 2026-09-28
* **Initialization**: Created the bundle root: index and log. No concepts yet.
```

- [ ] **Step 3: Verify.** `make verify`. Expected: `34 passed, 2 skipped` (the two parametrized
  tests have no concepts yet).
- [ ] **Step 4: Commit.** `Add the bundle root and the conformance tests`, `Closes #7`.

---

## Task 4: Reference and mission-type concepts (#8)

**Needs:** S10 status `read` (Task 1, Step 6).

**Files:** create `knowledge/platform/{index,qgc-plan-format}.md`,
`knowledge/mission-types/{index,mapping-survey,infrastructure-inspection,search-pattern}.md`;
modify `tests/test_bundle_conformance.py`. Task 11 writes the bundle map and log.

- [ ] **Step 1: Write the failing test.** Add to `EXPECTED`:

```python
    "Reference": {"platform/qgc-plan-format"},
    "Mission Type": {
        f"mission-types/{m}"
        for m in ("mapping-survey", "infrastructure-inspection", "search-pattern")
    },
```

Run `uv run pytest -q`. Expected: `1 failed, 33 passed, 2 skipped`
(`test_bundle_has_the_expected_concepts`).

- [ ] **Step 2: Write the concepts.**

`knowledge/platform/index.md`:

```markdown
# Platform

* [QGC plan format](qgc-plan-format.md) - the file format that `gen_plan` writes
```

`knowledge/platform/qgc-plan-format.md`:

```markdown
---
type: Reference
title: QGroundControl plan file format
description: The JSON .plan file that QGroundControl loads. v1 writes a subset of it.
tags: [qgc, plan-format, mission, geofence]
generated:
  by: claude-code
  at: "2026-09-28T20:00:00-07:00"
---
# Rule

A `.plan` file is JSON with `fileType: Plan`, a `mission` (items), a `geoFence` (circles and
polygons) and `rallyPoints`. The versions are pinned in `tools.lock`.

v1 writes only `SimpleItem` mission items and inclusion polygons. The vendored subset schema
`tests/fixtures/qgc/plan.schema.json` is the contract. Circle fences and `ComplexItem` are not
in v1.

# Source

- S8: QGroundControl plan file format (master). The polygon `version` is 2 in the table and 1
  in the example; the subset schema accepts both.
```

`knowledge/mission-types/index.md`:

```markdown
# Mission types

* [Mapping survey](mapping-survey.md) - grid pattern
* [Infrastructure inspection](infrastructure-inspection.md) - corridor pattern
* [Search pattern](search-pattern.md) - expanding square
```

`knowledge/mission-types/mapping-survey.md`:

```markdown
---
type: Mission Type
title: Mapping survey
description: Cover an area in parallel lines to map it.
tags: [mission-type, mapping, survey, grid]
table:
  pattern: grid
generated:
  by: claude-code
  at: "2026-09-28T20:00:00-07:00"
---
# Rule

`gen_plan` uses the `grid` pattern for this mission type. The plan starts with a takeoff,
flies the pattern inside the mission area, and ends with a return to launch. See
[QGC plan format](../platform/qgc-plan-format.md).

# Source

- S10: §1 Mission Type; §7 Mapping/Survey Specific Parameters: Pattern Type (Grid).
```

`knowledge/mission-types/infrastructure-inspection.md`:

```markdown
---
type: Mission Type
title: Infrastructure inspection
description: Fly along a linear asset (line, pipe, road) to inspect it.
tags: [mission-type, inspection, corridor]
table:
  pattern: corridor
generated:
  by: claude-code
  at: "2026-09-28T20:00:00-07:00"
---
# Rule

`gen_plan` uses the `corridor` pattern for this mission type. The plan starts with a takeoff,
flies the pattern inside the mission area, and ends with a return to launch. See
[QGC plan format](../platform/qgc-plan-format.md).

# Source

- S10: §1 Mission Type; §7 Mission Type (Infrastructure Inspection); Mapping/Survey Specific Parameters: Pattern Type (Corridor).
```

`knowledge/mission-types/search-pattern.md`:

```markdown
---
type: Mission Type
title: Search pattern
description: Search an area from a datum outward.
tags: [mission-type, search, expanding-square]
table:
  pattern: expanding-square
generated:
  by: claude-code
  at: "2026-09-28T20:00:00-07:00"
---
# Rule

`gen_plan` uses the `expanding-square` pattern for this mission type. The plan starts with a takeoff,
flies the pattern inside the mission area, and ends with a return to launch. See
[QGC plan format](../platform/qgc-plan-format.md).

# Source

- S10: §1 Mission Type; §7 Reconnaissance Specific Parameters: Search Pattern (Expanding Square).
```

- [ ] **Step 3: Verify.** `make verify`. Expected: `42 passed`.
- [ ] **Step 4: Commit.** `Add the reference and mission-type concepts`, `Closes #8`.

---

## Task 5: SORA risk tables (#9)

**Files:** create `knowledge/risk/{index,igrc,arc,sail,containment}.md`,
`tests/test_sora_tables.py`; modify `tests/test_bundle_conformance.py`.

The values are copied from S2 (pp. 24-41) and checked against S4 (pp. 34-51). The tests check
shape and internal consistency (rows and columns do not decrease, every SAIL is in each
containment table once). They do not repeat the values; the owner checks the values at Task 12.

- [ ] **Step 1: Write the failing tests.** Add to `EXPECTED`:

```python
    "Risk Table": {f"risk/{t}" for t in ("igrc", "arc", "sail", "containment")},
```

`tests/test_sora_tables.py` (without the mitigation test, which Task 6 adds):

```python
"""Check the shape and internal consistency of the SORA risk tables in knowledge/risk/.

These tests do not repeat the values. The owner checks the values against S2 and S4.
"""

from pathlib import Path

from okf_lib import load_bundle

BUNDLE = load_bundle(Path(__file__).resolve().parents[1] / "knowledge")
SAILS = ["I", "II", "III", "IV", "V", "VI"]
ARCS = ["a", "b", "c", "d"]
ROBUSTNESS = {"low", "medium", "high", "out-of-scope"}


def table(concept_id: str) -> dict:
    return BUNDLE.concepts[concept_id].table


def test_igrc_columns_grow() -> None:
    cols = table("risk/igrc")["columns"]
    assert len(cols) == 5
    for key in ("max_dimension_m", "max_speed_ms"):
        values = [c[key] for c in cols]
        assert values == sorted(set(values)), key


def test_igrc_rows_are_monotonic() -> None:
    rows = table("risk/igrc")["rows"]
    assert len({r["band"] for r in rows}) == len(rows) == 7
    for row in rows:
        assert len(row["igrc"]) == 5, row["band"]
        cells = [v for v in row["igrc"] if v is not None]
        assert cells == sorted(cells), row["band"]
    for col in range(5):
        cells = [r["igrc"][col] for r in rows if r["igrc"][col] is not None]
        assert cells == sorted(cells), col


def test_igrc_floor_names_a_band() -> None:
    igrc = table("risk/igrc")
    assert igrc["final_grc_floor"] in {r["band"] for r in igrc["rows"]}


def test_sail_rows_are_monotonic() -> None:
    sail = table("risk/sail")
    assert sail["arc_columns"] == ARCS
    grcs = [r["final_grc_max"] for r in sail["rows"]]
    assert grcs == sorted(set(grcs))
    rank = [[SAILS.index(s) for s in r["sail"]] for r in sail["rows"]]
    for row in rank:
        assert row == sorted(row)
    for col in range(len(ARCS)):
        assert [r[col] for r in rank] == sorted(r[col] for r in rank)


def test_arc_rules_end_with_a_default() -> None:
    arc = table("risk/arc")
    rules = arc["initial_arc"]
    assert all(r["arc"] in ARCS for r in rules)
    assert rules[-1]["when"] == {}
    assert all(r["when"] for r in rules[:-1])
    assert set(arc["tmpr"]) == set(ARCS)
    assert arc["residual_arc"]["lowest_by_vlos"] in ARCS


def test_containment_tables_cover_every_sail_once() -> None:
    tables = table("risk/containment")["tables"]
    assert [t["id"] for t in tables] == ["8", "9", "10", "11", "12", "13"]
    for t in tables:
        sails = [s for row in t["rows"] for s in row["sail"]]
        assert sails == SAILS, t["id"]
        for row in t["rows"]:
            assert len(row["robustness"]) == len(t["columns"]), t["id"]
            assert set(row["robustness"]) <= ROBUSTNESS, t["id"]
```

Run `uv run pytest -q`. Expected: `7 failed, 41 passed` (the six tests in
`test_sora_tables.py` with `KeyError`, and `test_bundle_has_the_expected_concepts`).

- [ ] **Step 2: Write the concepts.**

`knowledge/risk/index.md`:

```markdown
# Risk

SORA 2.5 risk tables and ground-risk mitigations, as adopted by EASA.

* [iGRC](igrc.md) - intrinsic ground risk class
* [ARC](arc.md) - initial and residual air risk class, TMPR
* [SAIL](sail.md) - final GRC x residual ARC
* [Containment](containment.md) - containment robustness
```

`knowledge/risk/igrc.md`:

```markdown
---
type: Risk Table
title: Intrinsic ground risk class (iGRC)
description: SORA 2.5 Step 2. The iGRC from the UA size and speed and the highest population density in the iGRC footprint.
tags: [sora, grc, igrc, ground-risk, population-density]
checks: [sora.igrc, sora.final_grc]
table:
  columns:
    - {max_dimension_m: 1, max_speed_ms: 25}
    - {max_dimension_m: 3, max_speed_ms: 35}
    - {max_dimension_m: 8, max_speed_ms: 75}
    - {max_dimension_m: 20, max_speed_ms: 120}
    - {max_dimension_m: 40, max_speed_ms: 200}
  rows:
    - {band: controlled-ground-area, below_people_km2: null, igrc: [1, 1, 2, 3, 3]}
    - {band: remote, below_people_km2: 5, igrc: [2, 3, 4, 5, 6]}
    - {band: lightly-populated, below_people_km2: 50, igrc: [3, 4, 5, 6, 7]}
    - {band: sparsely-populated, below_people_km2: 500, igrc: [4, 5, 6, 7, 8]}
    - {band: suburban, below_people_km2: 5000, igrc: [5, 6, 7, 8, 9]}
    - {band: high-density-metropolitan, below_people_km2: 50000, igrc: [6, 7, 8, 9, 10]}
    - {band: assemblies-of-people, below_people_km2: null, igrc: [7, 8, null, null, null]}
  small_ua: {max_takeoff_mass_kg: 0.25, max_speed_ms: 25, igrc: 1, not_over_assemblies: true}
  final_grc_floor: controlled-ground-area
generated:
  by: claude-code
  at: "2026-09-28T20:00:00-07:00"
---
# Rule

Find the iGRC at the intersection of the highest population density band in the iGRC
footprint and the left-most column where the UA maximum characteristic dimension and the UA
maximum speed are both within the column values. A `null` cell is not part of SORA: the
operation is outside the scope of SORA (certified category).

A single UA with a take-off mass of 250 g or less and a maximum speed of 25 m/s or less has an
iGRC of 1, unless it operates over assemblies of people (`small_ua`).

The final GRC is the iGRC plus the credits of the applied mitigations, in numerical sequence.
The M1 mitigations cannot reduce the final GRC below the value in the `controlled-ground-area`
row of the same column (`final_grc_floor`).

A final GRC above 7 is outside SORA. See [SAIL](sail.md).

# Bands

The band names come from the qualitative descriptors: controlled ground area or extremely
remote; remote; lightly populated; sparsely populated or residential lightly populated;
suburban or low-density metropolitan; high-density metropolitan; assemblies of people.

# Source

- S2: AMC1 Article 11, S.4.2.3 Table 1 (iGRC) and Table 2 (qualitative descriptors),
  pp. 24-26; S.4.3.4 (M1 floor).
- S4: §4.2, Table 2 (p. 34) and Table 3 (p. 36); §4.3.4(f) (p. 39). Origin text.
- S2 adds "unless operating over assemblies of people" to the 250 g rule. The bundle uses S2.
```

`knowledge/risk/arc.md`:

```markdown
---
type: Risk Table
title: Air risk class (ARC) and TMPR
description: SORA 2.5 Steps 4 to 6. The initial ARC from the airspace, the VLOS reduction to the residual ARC, and the TMPR.
tags: [sora, arc, air-risk, tmpr, vlos]
checks: [sora.initial_arc, sora.residual_arc]
table:
  initial_arc:
    - {when: {atypical_airspace: true}, arc: a}
    - {when: {above_fl600: true}, arc: b}
    - {when: {airport_environment: true, airspace_class_in: [B, C, D]}, arc: d}
    - {when: {airport_environment: true}, arc: c}
    - {when: {above_500ft_agl: true, mode_c_veil_or_tmz: true}, arc: d}
    - {when: {above_500ft_agl: true, controlled_airspace: true}, arc: d}
    - {when: {above_500ft_agl: true}, arc: c}
    - {when: {mode_c_veil_or_tmz: true}, arc: c}
    - {when: {controlled_airspace: true}, arc: c}
    - {when: {over_urban_area: true}, arc: c}
    - {when: {}, arc: b}
  residual_arc:
    vlos_reduction_classes: 1
    vlos_applies_to: [VLOS, BVLOS-with-airspace-observers]
    lowest_by_vlos: b
  tmpr: {a: none, b: low, c: medium, d: high}
generated:
  by: claude-code
  at: "2026-09-28T20:00:00-07:00"
---
# Rule

The initial ARC comes from the decision tree: use the first entry of `initial_arc` whose
`when` conditions are all true for the operational volume. The last entry has no condition.

Above 500 ft AGL and below FL600, uncontrolled airspace gives ARC-c over urban and over rural
areas. Below 500 ft AGL, uncontrolled airspace over rural areas gives ARC-b.

For VLOS operations, and for BVLOS operations with airspace observers, the initial ARC can be
reduced by one class. This reduction cannot give ARC-a. Other strategic mitigations (Annex C)
are not in v1.

For BVLOS operations, the TMPR comes from the residual ARC. VLOS is an acceptable tactical
mitigation for all ARC levels.

# Source

- S2: AMC1 Article 11, S.4.4.3, Figure 6 (p. 32); S.4.5.4 (p. 34); S.4.6.3, Table 6 (p. 35).
- S4: §4.4.3, Figure 6 (p. 41); §4.5.4 (pp. 43-44); §4.6.3, Table 6 (p. 45). Origin text.
- S2 extends the VLOS reduction to BVLOS with airspace observers. The bundle uses S2.
```

`knowledge/risk/sail.md`:

```markdown
---
type: Risk Table
title: SAIL determination
description: SORA 2.5 Step 7. The SAIL (I to VI) from the final GRC and the residual ARC.
tags: [sora, sail]
checks: [sora.sail]
table:
  arc_columns: [a, b, c, d]
  rows:
    - {final_grc_max: 2, sail: [I, II, IV, VI]}
    - {final_grc_max: 3, sail: [II, II, IV, VI]}
    - {final_grc_max: 4, sail: [III, III, IV, VI]}
    - {final_grc_max: 5, sail: [IV, IV, IV, VI]}
    - {final_grc_max: 6, sail: [V, V, V, VI]}
    - {final_grc_max: 7, sail: [VI, VI, VI, VI]}
  above_table: certified-category
generated:
  by: claude-code
  at: "2026-09-28T20:00:00-07:00"
---
# Rule

Use the first row whose `final_grc_max` is equal to or more than the final GRC, and the column
of the residual ARC. A final GRC above the last row puts the operation in the certified
category.

# Source

- S2: AMC1 Article 11, S.4.7.3, SAIL determination table, p. 38 (the table caption reads
  "Table 3"; the text calls it Table 7).
- S4: §4.7.3, Table 7 (p. 47). Origin text. The values are the same.
```

`knowledge/risk/containment.md`:

```markdown
---
type: Risk Table
title: Containment requirements
description: SORA 2.5 Step 8. The containment robustness from the UA size and speed, the SAIL, and the adjacent-area population limits.
tags: [sora, containment, adjacent-area]
checks: [sora.containment]
table:
  low_below_takeoff_mass_kg: 0.25
  tables:
    - id: "8"
      max_dimension_m: 1
      below_speed_ms: 25
      shelter: true
      columns:
        - {below_people_km2: null, assemblies: over-400k}
        - {below_people_km2: null, assemblies: 40k-to-400k}
        - {below_people_km2: 50000, assemblies: under-40k}
      rows:
        - {sail: [I, II], robustness: [high, medium, low]}
        - {sail: [III], robustness: [medium, low, low]}
        - {sail: [IV, V, VI], robustness: [low, low, low]}
    - id: "9"
      max_dimension_m: 3
      below_speed_ms: 35
      shelter: true
      columns:
        - {below_people_km2: null, assemblies: over-400k}
        - {below_people_km2: null, assemblies: 40k-to-400k}
        - {below_people_km2: 50000, assemblies: under-40k}
        - {below_people_km2: 5000, assemblies: under-40k}
      rows:
        - {sail: [I, II], robustness: [out-of-scope, high, medium, low]}
        - {sail: [III], robustness: [out-of-scope, medium, low, low]}
        - {sail: [IV], robustness: [medium, low, low, low]}
        - {sail: [V, VI], robustness: [low, low, low, low]}
    - id: "10"
      max_dimension_m: 3
      below_speed_ms: 35
      shelter: false
      columns:
        - {below_people_km2: null, assemblies: over-400k}
        - {below_people_km2: 50000, assemblies: 40k-to-400k}
        - {below_people_km2: 5000, assemblies: under-40k}
        - {below_people_km2: 500, assemblies: under-40k}
      rows:
        - {sail: [I, II], robustness: [out-of-scope, high, medium, low]}
        - {sail: [III], robustness: [out-of-scope, medium, low, low]}
        - {sail: [IV], robustness: [medium, low, low, low]}
        - {sail: [V, VI], robustness: [low, low, low, low]}
    - id: "11"
      max_dimension_m: 8
      below_speed_ms: 75
      shelter: false
      columns:
        - {below_people_km2: null, assemblies: over-400k}
        - {below_people_km2: 50000, assemblies: 40k-to-400k}
        - {below_people_km2: 5000, assemblies: under-40k}
        - {below_people_km2: 500, assemblies: under-40k}
        - {below_people_km2: 50, assemblies: under-40k}
      rows:
        - {sail: [I, II], robustness: [out-of-scope, out-of-scope, high, medium, low]}
        - {sail: [III], robustness: [out-of-scope, out-of-scope, medium, low, low]}
        - {sail: [IV], robustness: [out-of-scope, medium, low, low, low]}
        - {sail: [V], robustness: [medium, low, low, low, low]}
        - {sail: [VI], robustness: [low, low, low, low, low]}
    - id: "12"
      max_dimension_m: 20
      below_speed_ms: 120
      shelter: false
      columns:
        - {below_people_km2: null, assemblies: over-400k}
        - {below_people_km2: 50000, assemblies: 40k-to-400k}
        - {below_people_km2: 5000, assemblies: under-40k}
        - {below_people_km2: 500, assemblies: under-40k}
        - {below_people_km2: 50, assemblies: under-40k}
      rows:
        - {sail: [I, II], robustness: [out-of-scope, out-of-scope, out-of-scope, high, medium]}
        - {sail: [III], robustness: [out-of-scope, out-of-scope, out-of-scope, medium, low]}
        - {sail: [IV], robustness: [out-of-scope, out-of-scope, medium, low, low]}
        - {sail: [V], robustness: [out-of-scope, medium, low, low, low]}
        - {sail: [VI], robustness: [medium, low, low, low, low]}
    - id: "13"
      max_dimension_m: 40
      below_speed_ms: 200
      shelter: false
      columns:
        - {below_people_km2: null, assemblies: over-400k}
        - {below_people_km2: 50000, assemblies: 40k-to-400k}
        - {below_people_km2: 5000, assemblies: under-40k}
        - {below_people_km2: 500, assemblies: under-40k}
        - {below_people_km2: 50, assemblies: under-40k}
      rows:
        - {sail: [I, II], robustness: [out-of-scope, out-of-scope, out-of-scope, out-of-scope, high]}
        - {sail: [III], robustness: [out-of-scope, out-of-scope, out-of-scope, out-of-scope, medium]}
        - {sail: [IV], robustness: [out-of-scope, out-of-scope, out-of-scope, medium, low]}
        - {sail: [V], robustness: [out-of-scope, out-of-scope, medium, low, low]}
        - {sail: [VI], robustness: [out-of-scope, medium, low, low, low]}
generated:
  by: claude-code
  at: "2026-09-28T20:00:00-07:00"
---
# Rule

A UA with a take-off mass below 250 g gets low containment, with no operational limit for the
adjacent area.

Otherwise, use the first table whose `max_dimension_m` and `below_speed_ms` fit the UA. In
that table, find the row that lists the SAIL. Choose the column from the operational limits:
the average population density allowed in the adjacent area, and the outdoor assemblies
allowed within 1 km of the operational volume. Use the most stringent of the two. The cell
gives the containment robustness. `out-of-scope` means SORA does not support the operation.

The adjacent area extends from the operational volume by the distance flown in 3 minutes at
maximum speed, not less than 5 km and not more than 35 km.

# Source

- S2: AMC1 Article 11, S.4.8.3, Tables 8 to 13 (pp. 38-41).
- S4: §4.8.3, Tables 8 to 13 (pp. 48-51). Origin text.
- S2 Table 8 has three rows (I and II; III; IV, V and VI). S4 Table 8 has four rows with
  "IV - VI" and "V-VI", which overlap. The bundle uses S2.
- S2 Table 12 gives "< 120 m/s"; S4 gives "< 125 m/s". The bundle uses S2.
```

- [ ] **Step 3: Verify.** `make verify`. Expected: `56 passed`.
- [ ] **Step 4: Commit.** `Add the SORA risk tables`, `Closes #9`.

---

## Task 6: SORA ground-risk mitigations (#10)

**Files:** create `knowledge/risk/{m1a,m1b,m1c,m2}.md`; modify `knowledge/risk/index.md`,
`tests/test_sora_tables.py`, `tests/test_bundle_conformance.py`.

- [ ] **Step 1: Write the failing tests.** Add to `EXPECTED`:

```python
    "Mitigation": {f"risk/{m}" for m in ("m1a", "m1b", "m1c", "m2")},
```

Append to `tests/test_sora_tables.py`:

```python
def test_mitigations_have_a_sequence_and_credits() -> None:
    mitigations = BUNDLE.of_type("Mitigation")
    assert sorted(m.table["sequence"] for m in mitigations) == [1, 2, 3, 4]
    for m in mitigations:
        credit = m.table["credit"]
        assert set(credit) == {"low", "medium", "high"}, m.id
        assert all(v is None or (isinstance(v, int) and v < 0) for v in credit.values()), m.id
```

Run `uv run pytest -q`. Expected: `2 failed, 55 passed` (the new test and
`test_bundle_has_the_expected_concepts`).

- [ ] **Step 2: Write the concepts.** Credits from S2 Table 5 (p. 29), same as S4 Table 5.

`knowledge/risk/m1a.md`:

```markdown
---
type: Mitigation
title: "M1(A) Strategic mitigation: sheltering"
description: SORA 2.5 ground-risk mitigation. Its credit to the final GRC depends on its level of robustness.
tags: [sora, grc, mitigation, sheltering]
table:
  sequence: 1
  credit: {low: -1, medium: -2, high: null}
generated:
  by: claude-code
  at: "2026-09-28T20:00:00-07:00"
---
# Rule

Apply the mitigations in the order of `sequence`. The credit is added to the iGRC at the
level of robustness that the operator shows (Annex B). A `null` credit means that level is not
available for this mitigation. See [iGRC](igrc.md) for the M1 floor.

# Source

- S2: AMC1 Article 11, S.4.3.3, Table 5 (p. 29).
- S4: §4.3.3, Table 5 (p. 38). Origin text. The values are the same.
```

`knowledge/risk/m1b.md`, `m1c.md` and `m2.md` have the same body. Only these fields change:

| File | `title` | `tags` last item | `sequence` | `credit` |
|---|---|---|---|---|
| `m1b.md` | `"M1(B) Strategic mitigation: operational restrictions"` | `operational-restrictions` | 2 | `{low: null, medium: -1, high: -2}` |
| `m1c.md` | `"M1(C) Tactical mitigation: ground observation"` | `ground-observation` | 3 | `{low: -1, medium: null, high: null}` |
| `m2.md` | `"M2 Effects of UA impact dynamics are reduced"` | `impact-dynamics` | 4 | `{low: null, medium: -1, high: -2}` |

Append to `knowledge/risk/index.md`:

```markdown
* [M1(A)](m1a.md) - sheltering
* [M1(B)](m1b.md) - operational restrictions
* [M1(C)](m1c.md) - ground observation
* [M2](m2.md) - impact dynamics
```

- [ ] **Step 3: Verify.** `make verify`. Expected: `65 passed`.
- [ ] **Step 4: Commit.** `Add the SORA ground-risk mitigations`, `Closes #10`.

---

## Task 7: MAVLink command concepts (#11)

**Needs:** S9 readable in the session, and S9 status `read`. Not prototyped.

**Files:** create `knowledge/mavlink/{index,nav-takeoff,nav-waypoint,nav-rtl,nav-land}.md`;
modify `tests/test_bundle_conformance.py`.

- [ ] **Step 1: Write the failing tests.** Add to `EXPECTED`:

```python
    "MAVLink Command": {f"mavlink/{c}" for c in ("nav-takeoff", "nav-waypoint", "nav-rtl", "nav-land")},
```

Append to `tests/test_bundle_conformance.py`:

```python
def test_mavlink_commands_have_an_id_and_seven_params() -> None:
    ids = {"mavlink/nav-waypoint": 16, "mavlink/nav-rtl": 20, "mavlink/nav-land": 21, "mavlink/nav-takeoff": 22}
    for cid, number in ids.items():
        table = BUNDLE.concepts[cid].table
        assert table["mavlink_id"] == number, cid
        assert len(table["params"]) == 7, cid
```

- [ ] **Step 2: Write the concepts.** Frontmatter: `type: MAVLink Command`, `table.mavlink_id`,
  `table.name` (for example `MAV_CMD_NAV_TAKEOFF`), `table.params` (seven entries, each the S9
  label or `null` when S9 marks it empty). `nav-takeoff` carries `checks: [plan.first_item_takeoff]`.
  `nav-rtl` carries `checks: [plan.last_item_return]` and links to `nav-land` ("RTL or LAND").
  `# Source` cites S9 and, for the QGC `frame` values, S8.
- [ ] **Step 3: Verify.** `make verify`.
- [ ] **Step 4: Commit.** `Add the MAVLink command concepts`, `Closes #11`.

---

## Task 8: Failsafe concepts (#12)

**Needs:** S7 readable in the session. Not prototyped.

**Files:** create `knowledge/failsafes/{index,lost-link,low-battery,geofence-breach,gps-loss}.md`;
modify `tests/test_bundle_conformance.py`.

- [ ] **Step 1: Write the failing tests.** Add to `EXPECTED`:

```python
    "Failsafe": {f"failsafes/{f}" for f in ("lost-link", "low-battery", "geofence-breach", "gps-loss")},
```

Append to `tests/test_bundle_conformance.py`:

```python
def test_failsafes_name_actions_and_px4_parameters() -> None:
    for concept in BUNDLE.of_type("Failsafe"):
        table = concept.table
        assert table["actions"] and all(isinstance(a, str) for a in table["actions"]), concept.id
        assert table["px4_params"] and all(p.isupper() for p in table["px4_params"]), concept.id
```

- [ ] **Step 2: Write the concepts.**

  | Concept | `checks` | `table.actions` (from S10 §7) | Mission request key |
  |---|---|---|---|
  | `lost-link` | `failsafe.lost_link` | RTL, LAND, LOITER | `lost_link` |
  | `low-battery` | `failsafe.low_battery`, `failsafe.critical_battery` | low: RTL, LAND; critical: LAND | `low_battery`, `critical_battery` |
  | `geofence-breach` | `failsafe.geofence_breach`, `plan.inside_geofence` | RTL, LOITER, LAND, WARN | `geofence_breach` |
  | `gps-loss` | none | LAND, ALT_HOLD, STABILIZE | none |

  `table.px4_params` lists the PX4 parameter names from S7 (for example the data-link-loss
  action and timeout). Write only names found in S7. `# Source` cites S10 and S7.
  The failsafes do not hold threshold values (for example 25 % or 15 %): those are mission
  settings, not rules.
- [ ] **Step 3: Verify.** `make verify`.
- [ ] **Step 4: Commit.** `Add the failsafe concepts`, `Closes #12`.

---

## Task 9: Hazard concepts (#13)

**Files:** create `knowledge/hazards/` (index and 10 concepts); modify
`tests/test_bundle_conformance.py`. Not prototyped.

- [ ] **Step 1: Write the failing tests.** Add to `EXPECTED`:

```python
    "Hazard": {
        f"hazards/{h}"
        for h in (
            "loss-of-c2", "gps-jamming", "low-battery", "midair-manned", "midair-suas",
            "obstacle-ground", "loss-of-vlos", "public-interference", "payload-malfunction",
            "weather-change",
        )
    },
```

Append to `tests/test_bundle_conformance.py`:

```python
@pytest.mark.parametrize("concept", [c for c in CONCEPTS if c.type == "Hazard"], ids=lambda c: c.id)
def test_hazard_scores(concept) -> None:
    fm = concept.frontmatter
    for key in ("likelihood", "severity"):
        assert isinstance(fm.get(key), int) and 1 <= fm[key] <= 5, f"{concept.path}: {key}"
    assert fm.get("residual") in {"Low", "Medium", "High"}, concept.path
```

- [ ] **Step 2: Write the concepts.** Values from S10 §6:

  | Concept | Title | L | S | Residual | Links |
  |---|---|---|---|---|---|
  | `loss-of-c2` | Loss of C2 link | 2 | 4 | Low | `failsafes/lost-link` |
  | `gps-jamming` | GPS signal loss or jamming | 1 | 4 | Low | `failsafes/gps-loss` |
  | `low-battery` | Battery failure or low battery | 2 | 3 | Low | `failsafes/low-battery` |
  | `midair-manned` | Mid-air collision with manned aircraft | 1 | 5 | Low | `risk/arc` |
  | `midair-suas` | Mid-air collision with other small UAS | 2 | 3 | Low | `failsafes/geofence-breach`, `risk/arc` |
  | `obstacle-ground` | Collision with a ground obstacle | 2 | 3 | Low | none |
  | `loss-of-vlos` | Loss of visual line of sight | 2 | 3 | Low | `risk/arc` |
  | `public-interference` | Public interference or disturbance | 2 | 2 | Low | `risk/igrc` |
  | `payload-malfunction` | Payload malfunction | 2 | 2 | Low | none |
  | `weather-change` | Extreme weather change | 2 | 4 | Low | none |

  Body: `# Mitigation` (the S10 mitigation text, rewritten in STE; for `midair-manned` write
  "operate below the open-category height limit" with no number, because 400 ft is the FAA
  value), `# Residual risk`, `# Source` (S10 §6). `hazards/index.md` says: score = likelihood x
  severity; scale 1 = very low, 5 = very high (S10 §6).
- [ ] **Step 3: Verify.** `make verify`.
- [ ] **Step 4: Commit.** `Add the hazard concepts`, `Closes #13`.

---

## Task 10: Regulation concepts and the v1 check ids (#14)

**Needs:** S1 readable in the session. Not prototyped.

**Files:** create `knowledge/regulations/{index,easa-open,easa-specific-sora}.md`,
`tests/test_check_ids.py`; modify `tests/test_bundle_conformance.py`.

- [ ] **Step 1: Write the failing tests.** Add to `EXPECTED`:

```python
    "Regulation": {"regulations/easa-open", "regulations/easa-specific-sora"},
```

`tests/test_check_ids.py`:

```python
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
```

- [ ] **Step 2: Write the concepts.**
  - `easa-open`: `checks: [alt.max_agl, category.operation]`. `table`: the maximum height above
    the closest point of the surface (m), the maximum MTOM (kg), and the allowed operations
    (VLOS). Values only from S1 Art. 4. `# Source` cites S1 (article and point).
  - `easa-specific-sora`: `checks: [sora.applicable]`. `table.edition: "2.5"` (matches
    `tools.lock`) and `table.steps` (the SORA 2.5 step names from S2 S.4). Links to every
    `risk/` concept. `# Source` cites S1 Art. 5 and 11, S2 AMC1 Art. 11, S4.
- [ ] **Step 3: Verify.** `make verify`.
- [ ] **Step 4: Commit.** `Add the regulation concepts and the v1 check ids`, `Closes #14`.

---

## Task 11: Bundle map, log and render (#15)

**Files:** modify `knowledge/index.md`, `knowledge/log.md`. Docs only.

- [ ] **Step 1:** Write the `# Map` in `knowledge/index.md`: one line per folder
  (regulations, risk, hazards, failsafes, mavlink, mission-types, platform).
- [ ] **Step 2:** Add a log entry per concept task, dated with the commit date.
- [ ] **Step 3:** `make render`. Expected: `Wrote 32 concept(s), ...` and
  `out/knowledge-viz.html`. In the prototype container, render failed on Python 3.14.0rc2
  (pydantic `AssertionError`) and passed on 3.13 (`Wrote 13 concept(s), 8 edge(s)`). If 3.14
  fails, report it. Do not change the Makefile pin without the owner.
- [ ] **Step 4: Commit.** `Add the bundle map and log (docs only)`, `Closes #15`.

---

## Task 12: Human gate: owner verifies the bundle (#16)

**The executing agent stops here and hands off to the owner.**

- [ ] **Step 1:** The owner reads each concept against its `# Source`, and fixes values.
- [ ] **Step 2:** The owner adds to each concept:

```yaml
verified:
  - by: "human:cdevarenne"
    at: "YYYY-MM-DDTHH:MM:00-07:00"
```

- [ ] **Step 3:** Add to `tests/test_bundle_conformance.py`:

```python
@pytest.mark.parametrize("concept", CONCEPTS, ids=lambda c: c.id)
def test_every_concept_is_human_verified(concept) -> None:
    verified = concept.frontmatter.get("verified") or []
    assert any(str(e.get("by", "")).startswith("human:") for e in verified), concept.path
```

- [ ] **Step 4:** `make verify`, then commit with `Closes #16`.

After Task 12: write the Phase 2 plan (`gen_plan`, DRN-04).
