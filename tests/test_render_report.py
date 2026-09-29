"""Check render_report: the report sections, the sign-off file, and its protection."""

import hashlib
from pathlib import Path

import pytest
import yaml
from pipeline import run_mission
from render_report import APPROVER_ROLES, main

ROOT = Path(__file__).resolve().parents[1]
MISSIONS = ROOT / "tests" / "fixtures" / "missions"
KNOWLEDGE, LOCK = ROOT / "knowledge", ROOT / "tools.lock"
SECTIONS = [
    "## 1. Mission overview",
    "## 2. Operational details",
    "## 3. Airspace and regulatory compliance",
    "## 4. Risk assessment",
    "## 5. Flight profile and waypoint plan",
    "## 6. Decision",
    "## 7. Audit trail",
    "## 8. Approvals",
]


def pipeline(tmp_path: Path, name: str) -> Path:
    assert run_mission(MISSIONS / f"{name}.yaml", KNOWLEDGE, LOCK, tmp_path) == 0
    return tmp_path / name


def args(tmp_path: Path, name: str) -> list[str]:
    return [
        "--mission", str(MISSIONS / f"{name}.yaml"), "--knowledge", str(KNOWLEDGE),
        "--lock", str(LOCK), "--out", str(tmp_path),
    ]  # fmt: skip


def test_report_has_the_template_sections_in_order(tmp_path: Path) -> None:
    report = (pipeline(tmp_path, "specific") / "report.md").read_text()
    positions = [report.index(s) for s in SECTIONS]
    assert positions == sorted(positions)
    assert report.startswith("# Mission report: specific\n\n**Proposed decision: HOLD**")


def test_report_names_every_cited_concept_in_the_audit_trail(tmp_path: Path) -> None:
    report = (pipeline(tmp_path, "specific") / "report.md").read_text()
    audit = report[report.index("## 7. Audit trail") :]
    for cid in ("risk/igrc", "risk/m1a", "hazards/loss-of-c2", "regulations/easa-open"):
        assert f"| {cid} |" in audit
    assert "human:cdevarenne" in audit


def test_report_shows_both_units_for_the_arc_limits(tmp_path: Path) -> None:
    report = (pipeline(tmp_path, "specific") / "report.md").read_text()
    assert "500 ft AGL (152.4 m)" in report


def test_open_mission_is_not_sora_scored(tmp_path: Path) -> None:
    report = (pipeline(tmp_path, "survey") / "report.md").read_text()
    assert "SORA 2.5: not applicable (category open)." in report
    assert "**Proposed decision: GO**" in report


def test_signoff_has_empty_approvals_and_the_file_hashes(tmp_path: Path) -> None:
    folder = pipeline(tmp_path, "specific")
    doc = yaml.safe_load((folder / "signoff.yaml").read_text())
    assert doc["proposed_decision"] == "HOLD"
    assert [a["role"] for a in doc["approvals"]] == list(APPROVER_ROLES)
    assert all(a[f] == "" for a in doc["approvals"] for f in ("name", "decision", "date"))
    for key, name in (("plan_sha256", "mission.plan"), ("report_sha256", "report.md")):
        assert doc[key] == hashlib.sha256((folder / name).read_bytes()).hexdigest()


def test_output_is_deterministic(tmp_path: Path) -> None:
    first = pipeline(tmp_path / "a", "search")
    second = pipeline(tmp_path / "b", "search")
    for name in ("report.md", "signoff.yaml"):
        assert (first / name).read_text() == (second / name).read_text()


def test_started_signoff_is_never_overwritten(tmp_path: Path) -> None:
    folder = pipeline(tmp_path, "survey")
    signoff = folder / "signoff.yaml"
    signed = signoff.read_text().replace('name: ""', 'name: "A. Pilot"', 1)
    signoff.write_text(signed)
    report = (folder / "report.md").read_text()
    assert main(args(tmp_path, "survey")) == 2
    assert signoff.read_text() == signed
    assert (folder / "report.md").read_text() == report


def test_unsigned_signoff_is_rewritten(tmp_path: Path) -> None:
    pipeline(tmp_path, "survey")
    assert main(args(tmp_path, "survey")) == 0


def test_missing_results_return_2(tmp_path: Path) -> None:
    folder = pipeline(tmp_path, "survey")
    (folder / "risk.json").unlink()
    (folder / "signoff.yaml").unlink()
    assert main(args(tmp_path, "survey")) == 2


@pytest.mark.parametrize("name", ["survey", "specific"])
def test_report_does_not_approve(tmp_path: Path, name: str) -> None:
    report = (pipeline(tmp_path, name) / "report.md").read_text()
    assert "a person decides and signs" in report
