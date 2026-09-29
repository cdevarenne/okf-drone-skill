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
EXPECTED: dict[str, set[str]] = {
    "Reference": {"platform/qgc-plan-format"},
    "Mission Type": {
        f"mission-types/{m}"
        for m in ("mapping-survey", "infrastructure-inspection", "search-pattern")
    },
    "Risk Table": {f"risk/{t}" for t in ("igrc", "arc", "sail", "containment")},
    "Mitigation": {f"risk/{m}" for m in ("m1a", "m1b", "m1c", "m2")},
}
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
