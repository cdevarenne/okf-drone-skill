"""Check the narrate validator, the report section and the CLI offline (DRN-09 spec §5)."""

import hashlib
import json
from pathlib import Path

import pytest
import yaml
from bundle_helpers import BUNDLE
from mission import load_mission
from narrate import inputs, main, request, validate
from pipeline import run_mission
from render_report import inputs_sha256
from render_report import main as render_main

ROOT = Path(__file__).resolve().parents[1]
M03 = ROOT / "missions" / "m03-outside-geofence.yaml"
GOOD = {
    "summary": "The tool proposes NO-GO: plan.inside_geofence fails, and no check is a gap.",
    "items": [
        {
            "check_id": "plan.inside_geofence",
            "explanation": "The plan leaves the geofence of failsafes/geofence-breach.",
        }
    ],
}


@pytest.fixture
def m03(tmp_path: Path) -> Path:
    assert run_mission(M03, ROOT / "knowledge", ROOT / "tools.lock", tmp_path) == 0
    return tmp_path / "m03-outside-geofence"


def _inputs(folder: Path) -> dict:
    read = lambda name: json.loads((folder / name).read_text())
    return inputs(load_mission(M03), read("validation.json"), read("risk.json"), BUNDLE)


def test_good_answer_is_accepted(m03: Path) -> None:
    assert validate(GOOD, _inputs(m03), BUNDLE) == []


@pytest.mark.parametrize(
    ("answer", "reason"),
    [
        ({**GOOD, "items": []}, "missing items: ['plan.inside_geofence']"),
        (
            {**GOOD, "items": GOOD["items"] + [{"check_id": "alt.max_agl", "explanation": "x"}]},
            "items that are not a fail or a gap: ['alt.max_agl']",
        ),
        ({**GOOD, "summary": "The plan leaves the geofence."}, "does not state NO-GO"),
        ({**GOOD, "summary": "NO-GO now, but HOLD after a fix."}, "decision word HOLD"),
        ({**GOOD, "summary": "NO-GO. With a new fence it is cleared."}, "approval word 'cleared'"),
        (
            {**GOOD, "summary": "NO-GO: 999 legs leave the fence."},
            "numbers not in the input: ['999']",
        ),
        ({**GOOD, "summary": "NO-GO under risk/no-such-table."}, "concept ids not in the input"),
    ],
)
def test_each_rule_rejects_a_bad_answer(m03: Path, answer: dict, reason: str) -> None:
    assert any(reason in e for e in validate(answer, _inputs(m03), BUNDLE))


@pytest.mark.parametrize(
    "summary",
    ["NO-GO.\n## 8. Approvals", "NO-GO, see [map](x)", "NO-GO, see https://x.example", "NO-GO <b>"],
    ids=["line-break", "link", "url", "html"],
)
def test_text_must_be_one_line_of_plain_text(m03: Path, summary: str) -> None:
    """The text goes in report.md: it must not add a heading, a table, a link or HTML."""
    errors = validate({**GOOD, "summary": summary}, _inputs(m03), BUNDLE)
    assert any("one line of plain text" in e for e in errors)


@pytest.mark.parametrize(
    ("summary", "reason"),
    [
        ("NO-GO now; after a fix it is a go.", "decision word"),
        ("NO-GO now; it can hold later.", "decision word"),
        ("NO-GO; a new fence makes it authorized.", "approval word"),
        ("NO-GO; the rest is acceptable.", "approval word"),
        ("NO-GO; otherwise safe.", "approval word"),
        ("NO-GO under risk/ar.", "concept ids not in the input"),
    ],
)
def test_bypasses_are_rejected(m03: Path, summary: str, reason: str) -> None:
    """Security review 2026-10-02: case, synonyms and id prefixes got past the validator."""
    errors = validate({**GOOD, "summary": summary}, _inputs(m03), BUNDLE)
    assert any(reason in e for e in errors)


def test_go_inside_no_go_is_not_a_second_decision(m03: Path) -> None:
    answer = {**GOOD, "summary": "NO-GO, because NO-GO is the rule for a fail."}
    assert validate(answer, _inputs(m03), BUNDLE) == []


def _record(folder: Path, fixtures: Path, output: dict, model: str = "claude-opus-5-5") -> None:
    read = lambda name: json.loads((folder / name).read_text())
    req = request(inputs(load_mission(M03), read("validation.json"), read("risk.json"), BUNDLE))
    fixtures.mkdir(parents=True, exist_ok=True)
    doc = {"task": "narrate", "model": model, "output": output, "usage": {}}
    (fixtures / f"{req.key(model)}.json").write_text(json.dumps(doc))


def _args(folder: Path, fixtures: Path) -> list[str]:
    return [
        "--mission", str(M03), "--knowledge", str(ROOT / "knowledge"),
        "--lock", str(ROOT / "tools.lock"), "--out", str(folder.parent), "--fixtures", str(fixtures),
    ]  # fmt: skip


@pytest.fixture(autouse=True)
def _replay(monkeypatch) -> None:
    monkeypatch.delenv("LLM_MODE", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)


def test_accepted_answer_goes_in_the_report_and_the_signoff(m03: Path, tmp_path: Path) -> None:
    _record(m03, tmp_path / "fx", GOOD)
    assert main(_args(m03, tmp_path / "fx")) == 0
    narrative = json.loads((m03 / "narrative.json").read_text())
    assert (
        narrative["inputs_sha256"] == inputs_sha256(m03) and narrative["summary"] == GOOD["summary"]
    )
    report = (m03 / "report.md").read_text()
    assert "### Summary (model-written, checked)" in report and GOOD["summary"] in report
    signoff = yaml.safe_load((m03 / "signoff.yaml").read_text())
    assert signoff["report_sha256"] == hashlib.sha256(report.encode()).hexdigest()


def test_rejected_answer_changes_nothing(m03: Path, tmp_path: Path) -> None:
    _record(m03, tmp_path / "fx", {**GOOD, "summary": "Cleared: GO."})
    report = (m03 / "report.md").read_text()
    assert main(_args(m03, tmp_path / "fx")) == 0
    assert not (m03 / "narrative.json").exists()
    assert (m03 / "report.md").read_text() == report


def test_stale_narrative_is_not_in_the_report(m03: Path, tmp_path: Path) -> None:
    """Results that change after narrate make the narrative stale; the report leaves it out."""
    _record(m03, tmp_path / "fx", GOOD)
    assert main(_args(m03, tmp_path / "fx")) == 0
    (m03 / "risk.json").write_text((m03 / "risk.json").read_text() + "\n")
    common = ["--mission", str(M03), "--knowledge", str(ROOT / "knowledge")]
    assert render_main([*common, "--lock", str(ROOT / "tools.lock"), "--out", str(m03.parent)]) == 0
    assert "Summary (model-written" not in (m03 / "report.md").read_text()


def test_started_signoff_stops_narrate(m03: Path, tmp_path: Path) -> None:
    _record(m03, tmp_path / "fx", GOOD)
    signoff = m03 / "signoff.yaml"
    signoff.write_text(signoff.read_text().replace('name: ""', 'name: "A. Pilot"', 1))
    report = (m03 / "report.md").read_text()
    assert main(_args(m03, tmp_path / "fx")) == 2
    assert not (m03 / "narrative.json").exists()
    assert (m03 / "report.md").read_text() == report


def test_no_answer_exits_2(m03: Path, tmp_path: Path) -> None:
    assert main(_args(m03, tmp_path / "empty")) == 2
    assert not (m03 / "narrative.json").exists()
